from __future__ import annotations

from base import BaseModel
from .factual import FactualSetting
from .psychometric import PsychometricSetting
from .pedagogical import PedagogicalSetting


class QuizValidatorSetting(BaseModel):
    factual: FactualSetting
    psychometric: PsychometricSetting
    pedagogical: PedagogicalSetting
    