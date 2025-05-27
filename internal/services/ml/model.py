import inspect
import math
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from torch import nn
from torchvision import transforms

from internal.config import get_config
from internal.utils import log

logger = log.get_logger()


class PyTorchModel:
    def __init__(
        self,
        model: nn.Module,
    ) -> None:
        self.model = model

        sig = inspect.signature(self.model.forward)
        self._accepts_abcd = len(sig.parameters) >= 2  # noqa: PLR2004

    @staticmethod
    def get_transformer() -> transforms.Compose:
        return transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.RandomHorizontalFlip(),
                transforms.RandomRotation(360),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.5], std=[0.5]),
            ],
        )

    def load_model(self, path_to_weights: str) -> None:
        state_dict = torch.load(path_to_weights, map_location=torch.device(get_config().ML_DEVICE))
        self.model.load_state_dict(state_dict)
        self.model.eval()

    def predict(
        self,
        image_input: str | Path | Image.Image,
        transform: transforms.Compose | None = None,
    ) -> tuple[int, float]:
        img = Image.open(image_input).convert("RGB") if isinstance(image_input, (str, Path)) else image_input

        if transform is None:
            transform = self.get_transformer()

        data = transform(img).unsqueeze(0)
        device = next(self.model.parameters()).device
        data = data.to(device)
        self.model.eval()
        abcd_tensor = None

        if self._accepts_abcd:
            # cv2 ожидает NumPy RGB
            np_img = np.array(img)
            feats = self.compute_abcd_features(np_img)
            vec = [
                feats["asymmetry"],
                feats["border_irregularity"],
                feats["color_variation"],
                feats["diameter"],
                feats["abcd_score"],
            ]
            abcd_tensor = torch.tensor(vec, dtype=torch.float32, device=device).unsqueeze(0)

        args = (data, abcd_tensor) if self._accepts_abcd else (data,)

        with torch.no_grad():
            logits = self.model(*args)
            probs = nn.functional.softmax(logits, dim=1)
            prob_value, pred_idx = probs.max(dim=1)

        return pred_idx.item(), prob_value.item()

    @staticmethod
    def compute_abcd_features(image: str | Path) -> dict[str, float]:
        """
        Вычисляет параметры ABCD-теста:
        - A: Асимметрия
        - B: Нерегулярность границ
        - C: Вариация цвета
        - D: Диаметр
        Также вычисляется суммарный abcd_score.
        """
        # Переводим изображение в оттенки
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        # Применяем пороговую обработку (Otsu) для выделения области родинки
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Находим контуры
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            # Если контуры не найдены, возвращаем нулевые значения
            return {
                "asymmetry": 0.0,
                "border_irregularity": 0.0,
                "color_variation": 0.0,
                "diameter": 0.0,
                "abcd_score": 0.0,
            }

        # Выбираем самый большой контур (предполагаем, что это родинка)
        contour = max(contours, key=cv2.contourArea)

        # 1. Асимметрия (A)
        max_pointer_ellipse = 5
        if len(contour) < max_pointer_ellipse:
            asymmetry = 0.0  # Недостаточно точек для аппроксимации эллипса
        else:
            ellipse = cv2.fitEllipse(contour)
            (_, axes, _) = ellipse
            major_axis = max(axes)
            minor_axis = min(axes)
            asymmetry = (major_axis - minor_axis) / major_axis if major_axis != 0 else 0.0

        # 2. Нерегулярность границ (B)
        area = cv2.contourArea(contour)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        border_irregularity = (hull_area - area) / hull_area if hull_area != 0 else 0.0

        # 3. Вариация цвета (C)
        # Создаем маску по контуру
        mask = np.zeros(gray.shape, np.uint8)
        cv2.drawContours(mask, [contour], -1, 255, -1)
        # Вычисляем стандартное отклонение цветов в области родинки
        _, std_dev = cv2.meanStdDev(image, mask=mask)
        color_variation = float(np.mean(std_dev))

        # 4. Диаметр (D)
        diameter = math.sqrt(4 * area / math.pi) if area > 0 else 0.0

        # Итоговый ABCD-счет (пример объединения, можно задавать веса)
        abcd_score = (asymmetry * 1.3) + (border_irregularity * 0.1) + (color_variation * 0.5) + (diameter * 0.5)

        return {
            "asymmetry": asymmetry,
            "border_irregularity": border_irregularity,
            "color_variation": color_variation,
            "diameter": diameter,
            "abcd_score": abcd_score,
        }
