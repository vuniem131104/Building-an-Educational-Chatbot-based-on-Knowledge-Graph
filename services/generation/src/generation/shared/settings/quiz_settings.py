from __future__ import annotations 

from base import BaseModel
from .concept_card import ConceptCardExtractorSetting
from .topic_generator import TopicGeneratorSetting
from .question_answer_generator import QuestionAnswerGeneratorSetting
from .explanation import ExplanationGeneratorSetting
from .distractors import DistractorsGeneratorSetting

class QuizGenerationSetting(BaseModel):
    concept_card_extractor: ConceptCardExtractorSetting
    topic_generator: TopicGeneratorSetting
    question_answer_generator: QuestionAnswerGeneratorSetting
    explanation_generator: ExplanationGeneratorSetting
    distractors_generator: DistractorsGeneratorSetting
    vector_db_path: str
    max_concurrent_tasks: int