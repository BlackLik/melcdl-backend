from typing import Annotated

from pydantic import Field

LoginField = Annotated[str, Field(min_length=6, max_length=256)]
