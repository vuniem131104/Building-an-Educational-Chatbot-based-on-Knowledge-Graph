from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import Field, BaseModel

from generation.shared.models import QuizQuestion


class EvaluationCriteria(str, Enum):
    """Criteria for evaluating quiz quality"""
    CONTENT_ALIGNMENT = "content_alignment"  # 25 points
    LEARNING_OBJECTIVES = "learning_objectives"  # 20 points
    QUESTION_QUALITY = "question_quality"  # 20 points 
    DIFFICULTY_APPROPRIATENESS = "difficulty_appropriateness"  # 15 points
    PEDAGOGICAL_SOUNDNESS = "pedagogical_soundness"  # 10 points
    LANGUAGE_CLARITY = "language_clarity"  # 10 points


class CriteriaScore(BaseModel):
    """Score for a specific evaluation criteria"""
    criteria: EvaluationCriteria = Field(..., description="The evaluation criteria")
    score: int = Field(..., ge=0, le=100, description="Score for this criteria (0-100)")
    max_score: int = Field(..., description="Maximum possible score for this criteria")
    feedback: str = Field(..., description="Detailed feedback for this criteria")
    strengths: List[str] = Field(default_factory=list, description="Identified strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Identified weaknesses")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")


class QuizEvaluationInput(BaseModel):
    """Input for quiz evaluation"""
    quiz_questions: List[QuizQuestion] = Field(..., description="Quiz questions to evaluate")
    lecture_content: str = Field(..., description="Original lecture content for comparison")
    course_code: str = Field(..., description="Course code")
    week_number: int = Field(..., description="Week number")
    evaluation_criteria: List[EvaluationCriteria] = Field(
        default_factory=lambda: list(EvaluationCriteria), 
        description="Criteria to evaluate against"
    )


class QuizEvaluationOutput(BaseModel):
    """Output of quiz evaluation"""
    total_score: int = Field(..., ge=0, le=100, description="Total evaluation score (0-100)")
    grade: str = Field(..., description="Grade category (Excellent/Good/Satisfactory/Needs Improvement/Poor)")
    criteria_scores: List[CriteriaScore] = Field(..., description="Detailed scores for each criteria")
    overall_feedback: str = Field(..., description="Overall evaluation feedback")
    major_strengths: List[str] = Field(default_factory=list, description="Major strengths identified")
    major_weaknesses: List[str] = Field(default_factory=list, description="Major weaknesses identified")
    priority_improvements: List[str] = Field(default_factory=list, description="Priority areas for improvement")
    recommendation: str = Field(..., description="Overall recommendation (Accept/Revise/Reject)")
    course_code: str = Field(..., description="Course code")
    week_number: int = Field(..., description="Week number")


class QuizEvaluationMetrics(BaseModel):
    """Metrics for quiz evaluation analysis"""
    content_coverage_percentage: float = Field(..., ge=0, le=100, description="Percentage of lecture content covered")
    question_difficulty_distribution: dict[str, int] = Field(..., description="Distribution of question difficulties")
    bloom_taxonomy_distribution: dict[str, int] = Field(..., description="Distribution of Bloom's taxonomy levels")
    average_estimated_accuracy: float = Field(..., ge=0, le=1, description="Average estimated right answer rate")
    total_questions_evaluated: int = Field(..., description="Total number of questions evaluated")


class DetailedQuestionEvaluation(BaseModel):
    """Detailed evaluation for individual question"""
    question_id: Optional[str] = Field(None, description="Question identifier")
    question_text: str = Field(..., description="The question text")
    content_alignment_score: int = Field(..., ge=0, le=10, description="How well question aligns with content")
    difficulty_appropriateness_score: int = Field(..., ge=0, le=10, description="Appropriateness of difficulty level")
    clarity_score: int = Field(..., ge=0, le=10, description="Clarity and understandability")
    pedagogical_value_score: int = Field(..., ge=0, le=10, description="Educational value")
    specific_feedback: str = Field(..., description="Specific feedback for this question")
    suggested_improvements: List[str] = Field(default_factory=list, description="Specific improvement suggestions")


class ComprehensiveQuizEvaluationOutput(QuizEvaluationOutput):
    """Extended evaluation output with detailed metrics"""
    metrics: QuizEvaluationMetrics = Field(..., description="Evaluation metrics")
    question_evaluations: List[DetailedQuestionEvaluation] = Field(..., description="Individual question evaluations")
    content_gaps: List[str] = Field(default_factory=list, description="Topics not covered in quiz")
    redundant_content: List[str] = Field(default_factory=list, description="Overly repetitive content areas")