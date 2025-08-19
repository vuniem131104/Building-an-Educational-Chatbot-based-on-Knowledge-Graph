from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any

from .base_model import CustomBaseModel as BaseModel


class BaseApplication(ABC, BaseModel):
    @abstractmethod
    def run(self, inputs: Any) -> Any:
        raise NotImplementedError()


class AsyncBaseApplication(ABC, BaseModel):
    @abstractmethod
    async def run(self, inputs: Any) -> Any:
        raise NotImplementedError()
