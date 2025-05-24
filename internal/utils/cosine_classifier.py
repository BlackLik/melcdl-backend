import torch
from torch import nn


class CosineClassifier(nn.Module):
    def __init__(self, in_features: int, num_classes: int, scale: float = 10.0) -> None:
        super().__init__()
        self.scale = scale
        # Параметры - веса для каждого класса
        self.weight = nn.Parameter(torch.Tensor(num_classes, in_features))
        # Инициализация весов (например, Xavier)
        nn.init.xavier_uniform_(self.weight)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: [batch, in_features]
        """
        # Нормализуем входные признаки по L2 норме вдоль размерности признаков
        x_norm = nn.functional.normalize(x, p=2, dim=1)  # [batch, in_features]
        # Нормализуем веса
        w_norm = nn.functional.normalize(self.weight, p=2, dim=1)
        # Вычисляем косинусное сходство: матричное умножение x_norm и транспонированных w_norm
        cosine_sim = torch.mm(x_norm, w_norm.t())  # [batch, num_classes]
        # Масштабируем сходство для повышения экспрессивности логитов
        return self.scale * cosine_sim
