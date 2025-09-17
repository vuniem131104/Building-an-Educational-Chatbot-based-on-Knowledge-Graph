from __future__ import annotations

from base import BaseModel


class QuizEvaluatorSetting(BaseModel):
    """Settings for LLM-as-Judge quiz evaluation"""
    model: str = "gpt-4o-mini"
    temperature: float = 0.1
    top_p: float = 1.0
    n: int = 1
    frequency_penalty: float = 0.0
    max_completion_tokens: int = 4000
    reasoning_effort: str | None = "medium"
    
    # Evaluation criteria weights (should sum to 100)
    content_alignment_weight: int = 25
    learning_objectives_weight: int = 20
    question_quality_weight: int = 20
    difficulty_appropriateness_weight: int = 15
    pedagogical_soundness_weight: int = 10
    language_clarity_weight: int = 10
    
    # Score thresholds
    acceptance_threshold: int = 80  # Accept quiz if score >= 80
    revision_threshold: int = 60    # Suggest revision if 60 <= score < 80
    # Reject if score < 60
    
    # Evaluation modes
    enable_detailed_analysis: bool = True
    enable_individual_question_evaluation: bool = True
    enable_content_coverage_analysis: bool = True
    enable_pedagogical_effectiveness_analysis: bool = False
    
    # Content processing
    max_lecture_content_length: int = 8000  # Characters
    max_questions_per_batch: int = 10
    
    # Retry settings
    max_retry_attempts: int = 3
    retry_delay_seconds: int = 2