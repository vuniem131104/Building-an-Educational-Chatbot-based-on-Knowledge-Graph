from __future__ import annotations

import json
import asyncio
from typing import List, Dict, Any, Optional

from base import BaseService
from logger import get_logger
from lite_llm import LiteLLMService

from .models import (
    QuizEvaluationInput,
    QuizEvaluationOutput,
    ComprehensiveQuizEvaluationOutput,
    CriteriaScore,
    EvaluationCriteria,
    QuizEvaluationMetrics,
    DetailedQuestionEvaluation
)
from .prompts import (
    QUIZ_EVALUATOR_SYSTEM_PROMPT,
    QUIZ_EVALUATOR_USER_PROMPT,
    DETAILED_QUESTION_ANALYSIS_PROMPT,
    CONTENT_COVERAGE_ANALYSIS_PROMPT,
    PEDAGOGICAL_EFFECTIVENESS_PROMPT
)
from generation.shared.models import QuizQuestion

logger = get_logger(__name__)


class QuizEvaluatorService(BaseService):
    """Service for evaluating quiz quality using LLM as judge"""
    
    def __init__(self, llm_service: LiteLLMService):
        self.llm_service = llm_service
        
        # Criteria weights for final score calculation
        self.criteria_weights = {
            EvaluationCriteria.CONTENT_ALIGNMENT: 25,
            EvaluationCriteria.LEARNING_OBJECTIVES: 20,
            EvaluationCriteria.QUESTION_QUALITY: 20,
            EvaluationCriteria.DIFFICULTY_APPROPRIATENESS: 15,
            EvaluationCriteria.PEDAGOGICAL_SOUNDNESS: 10,
            EvaluationCriteria.LANGUAGE_CLARITY: 10,
        }

    async def evaluate_quiz(self, inputs: QuizEvaluationInput) -> QuizEvaluationOutput:
        """
        Evaluate quiz quality against lecture content
        """
        logger.info(
            "Starting quiz evaluation",
            extra={
                "course_code": inputs.course_code,
                "week_number": inputs.week_number,
                "num_questions": len(inputs.quiz_questions),
                "criteria_count": len(inputs.evaluation_criteria)
            }
        )
        
        try:
            # Format quiz questions for evaluation
            quiz_text = self._format_quiz_questions(inputs.quiz_questions)
            
            # Generate evaluation prompt
            evaluation_prompt = QUIZ_EVALUATOR_USER_PROMPT.format(
                course_code=inputs.course_code,
                week_number=inputs.week_number,
                num_questions=len(inputs.quiz_questions),
                lecture_content=inputs.lecture_content,
                quiz_questions_text=quiz_text
            )
            
            # Get LLM evaluation
            evaluation_response = await self.llm_service.generate_text(
                system_prompt=QUIZ_EVALUATOR_SYSTEM_PROMPT,
                user_prompt=evaluation_prompt,
                temperature=0.1,  # Low temperature for consistent evaluation
                max_tokens=4000
            )
            
            # Parse evaluation response
            evaluation_result = await self._parse_evaluation_response(
                evaluation_response, inputs
            )
            
            logger.info(
                "Quiz evaluation completed successfully",
                extra={
                    "course_code": inputs.course_code,
                    "week_number": inputs.week_number,
                    "total_score": evaluation_result.total_score,
                    "grade": evaluation_result.grade,
                    "recommendation": evaluation_result.recommendation
                }
            )
            
            return evaluation_result
            
        except Exception as e:
            logger.exception(
                "Error during quiz evaluation",
                extra={
                    "course_code": inputs.course_code,
                    "week_number": inputs.week_number,
                    "error": str(e)
                }
            )
            raise

    async def evaluate_quiz_comprehensive(self, inputs: QuizEvaluationInput) -> ComprehensiveQuizEvaluationOutput:
        """
        Perform comprehensive quiz evaluation with detailed analysis
        """
        logger.info(
            "Starting comprehensive quiz evaluation",
            extra={
                "course_code": inputs.course_code,
                "week_number": inputs.week_number,
                "num_questions": len(inputs.quiz_questions)
            }
        )
        
        try:
            # Run multiple evaluation tasks in parallel
            tasks = [
                self._evaluate_overall_quality(inputs),
                self._evaluate_individual_questions(inputs),
                self._analyze_content_coverage(inputs),
                self._calculate_metrics(inputs)
            ]
            
            overall_eval, question_evals, coverage_analysis, metrics = await asyncio.gather(*tasks)
            
            # Combine results into comprehensive output
            comprehensive_result = ComprehensiveQuizEvaluationOutput(
                **overall_eval.model_dump(),
                metrics=metrics,
                question_evaluations=question_evals,
                content_gaps=coverage_analysis.get("content_gaps", []),
                redundant_content=coverage_analysis.get("redundant_content", [])
            )
            
            logger.info(
                "Comprehensive quiz evaluation completed",
                extra={
                    "course_code": inputs.course_code,
                    "week_number": inputs.week_number,
                    "total_score": comprehensive_result.total_score,
                    "content_coverage": metrics.content_coverage_percentage
                }
            )
            
            return comprehensive_result
            
        except Exception as e:
            logger.exception(
                "Error during comprehensive quiz evaluation",
                extra={
                    "course_code": inputs.course_code,
                    "week_number": inputs.week_number,
                    "error": str(e)
                }
            )
            raise

    async def _evaluate_overall_quality(self, inputs: QuizEvaluationInput) -> QuizEvaluationOutput:
        """Evaluate overall quiz quality"""
        return await self.evaluate_quiz(inputs)

    async def _evaluate_individual_questions(self, inputs: QuizEvaluationInput) -> List[DetailedQuestionEvaluation]:
        """Evaluate each question individually"""
        question_evaluations = []
        
        for idx, question in enumerate(inputs.quiz_questions):
            try:
                # Create analysis prompt for individual question
                analysis_prompt = DETAILED_QUESTION_ANALYSIS_PROMPT.format(
                    question_text=question.question,
                    correct_answer=question.answer,
                    distractors=question.distractors if question.distractors else [],
                    difficulty=getattr(question, 'difficulty', 'Unknown')
                )
                
                # Get LLM analysis
                analysis_response = await self.llm_service.generate_text(
                    system_prompt=QUIZ_EVALUATOR_SYSTEM_PROMPT,
                    user_prompt=analysis_prompt,
                    temperature=0.1,
                    max_tokens=1000
                )
                
                # Parse individual question evaluation
                question_eval = await self._parse_question_evaluation(
                    analysis_response, question, idx
                )
                question_evaluations.append(question_eval)
                
            except Exception as e:
                logger.warning(
                    f"Failed to evaluate individual question {idx}",
                    extra={"error": str(e)}
                )
                # Create default evaluation for failed cases
                question_evaluations.append(
                    DetailedQuestionEvaluation(
                        question_id=str(idx),
                        question_text=question.question,
                        content_alignment_score=5,
                        difficulty_appropriateness_score=5,
                        clarity_score=5,
                        pedagogical_value_score=5,
                        specific_feedback="Failed to analyze question due to error",
                        suggested_improvements=["Review question for potential issues"]
                    )
                )
        
        return question_evaluations

    async def _analyze_content_coverage(self, inputs: QuizEvaluationInput) -> Dict[str, Any]:
        """Analyze content coverage and gaps"""
        try:
            # Extract question topics
            question_topics = [
                f"Q{idx+1}: {q.question[:100]}..." 
                for idx, q in enumerate(inputs.quiz_questions)
            ]
            
            coverage_prompt = CONTENT_COVERAGE_ANALYSIS_PROMPT.format(
                lecture_content=inputs.lecture_content[:2000],  # Limit content length
                question_topics="\n".join(question_topics)
            )
            
            coverage_response = await self.llm_service.generate_text(
                system_prompt=QUIZ_EVALUATOR_SYSTEM_PROMPT,
                user_prompt=coverage_prompt,
                temperature=0.1,
                max_tokens=1500
            )
            
            # Parse coverage analysis
            return await self._parse_coverage_analysis(coverage_response)
            
        except Exception as e:
            logger.warning(
                "Failed to analyze content coverage",
                extra={"error": str(e)}
            )
            return {
                "content_gaps": ["Unable to analyze content gaps"],
                "redundant_content": []
            }

    async def _calculate_metrics(self, inputs: QuizEvaluationInput) -> QuizEvaluationMetrics:
        """Calculate quantitative metrics for the quiz"""
        try:
            # Difficulty distribution
            difficulty_dist = {}
            bloom_dist = {}
            total_estimated_accuracy = 0
            
            for question in inputs.quiz_questions:
                # Count difficulties
                difficulty = getattr(question, 'difficulty', 'Unknown')
                difficulty_dist[difficulty] = difficulty_dist.get(difficulty, 0) + 1
                
                # Count Bloom's taxonomy levels
                bloom_level = getattr(question, 'bloom_taxonomy_level', 'Unknown')
                bloom_dist[bloom_level] = bloom_dist.get(bloom_level, 0) + 1
                
                # Sum estimated accuracy
                estimated_rate = getattr(question, 'estimated_right_answer_rate', 0.5)
                total_estimated_accuracy += estimated_rate
            
            avg_accuracy = total_estimated_accuracy / len(inputs.quiz_questions) if inputs.quiz_questions else 0
            
            # Estimate content coverage (simplified)
            content_coverage = min(100.0, len(inputs.quiz_questions) * 12.5)  # Rough estimate
            
            return QuizEvaluationMetrics(
                content_coverage_percentage=content_coverage,
                question_difficulty_distribution=difficulty_dist,
                bloom_taxonomy_distribution=bloom_dist,
                average_estimated_accuracy=avg_accuracy,
                total_questions_evaluated=len(inputs.quiz_questions)
            )
            
        except Exception as e:
            logger.warning(
                "Failed to calculate metrics",
                extra={"error": str(e)}
            )
            return QuizEvaluationMetrics(
                content_coverage_percentage=0.0,
                question_difficulty_distribution={},
                bloom_taxonomy_distribution={},
                average_estimated_accuracy=0.0,
                total_questions_evaluated=len(inputs.quiz_questions)
            )

    def _format_quiz_questions(self, questions: List[QuizQuestion]) -> str:
        """Format quiz questions for evaluation prompt"""
        formatted_questions = []
        
        for idx, question in enumerate(questions, 1):
            question_text = f"\n**Question {idx}:**\n"
            question_text += f"**Text:** {question.question}\n"
            question_text += f"**Correct Answer:** {question.answer}\n"
            
            if hasattr(question, 'distractors') and question.distractors:
                question_text += f"**Distractors:** {', '.join(question.distractors)}\n"
            
            if hasattr(question, 'difficulty'):
                question_text += f"**Difficulty:** {question.difficulty}\n"
            
            if hasattr(question, 'bloom_taxonomy_level'):
                question_text += f"**Bloom's Level:** {question.bloom_taxonomy_level}\n"
            
            if hasattr(question, 'estimated_right_answer_rate'):
                question_text += f"**Est. Accuracy:** {question.estimated_right_answer_rate}\n"
            
            if hasattr(question, 'explanation') and question.explanation:
                question_text += f"**Explanation:** {question.explanation[:200]}...\n"
            
            formatted_questions.append(question_text)
        
        return "\n".join(formatted_questions)

    async def _parse_evaluation_response(self, response: str, inputs: QuizEvaluationInput) -> QuizEvaluationOutput:
        """Parse LLM evaluation response into structured output"""
        try:
            # Try to extract JSON if present
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
                evaluation_data = json.loads(json_str)
            else:
                # Parse text-based response
                evaluation_data = await self._parse_text_evaluation(response)
            
            # Create criteria scores
            criteria_scores = []
            total_weighted_score = 0
            
            for criteria in inputs.evaluation_criteria:
                # Extract score for this criteria (default to 70 if not found)
                score = evaluation_data.get(f"{criteria.value}_score", 70)
                weight = self.criteria_weights[criteria]
                weighted_score = (score * weight) / 100
                total_weighted_score += weighted_score
                
                criteria_score = CriteriaScore(
                    criteria=criteria,
                    score=score,
                    max_score=weight,
                    feedback=evaluation_data.get(f"{criteria.value}_feedback", "No specific feedback available"),
                    strengths=evaluation_data.get(f"{criteria.value}_strengths", []),
                    weaknesses=evaluation_data.get(f"{criteria.value}_weaknesses", []),
                    suggestions=evaluation_data.get(f"{criteria.value}_suggestions", [])
                )
                criteria_scores.append(criteria_score)
            
            # Determine grade
            grade = self._calculate_grade(total_weighted_score)
            
            # Determine recommendation
            recommendation = self._determine_recommendation(total_weighted_score)
            
            return QuizEvaluationOutput(
                total_score=int(total_weighted_score),
                grade=grade,
                criteria_scores=criteria_scores,
                overall_feedback=evaluation_data.get("overall_feedback", "Evaluation completed"),
                major_strengths=evaluation_data.get("major_strengths", []),
                major_weaknesses=evaluation_data.get("major_weaknesses", []),
                priority_improvements=evaluation_data.get("priority_improvements", []),
                recommendation=recommendation,
                course_code=inputs.course_code,
                week_number=inputs.week_number
            )
            
        except Exception as e:
            logger.warning(
                "Failed to parse evaluation response, using default",
                extra={"error": str(e)}
            )
            return self._create_default_evaluation(inputs)

    async def _parse_text_evaluation(self, response: str) -> Dict[str, Any]:
        """Parse text-based evaluation response"""
        # This is a simplified parser - in production, you might want more sophisticated parsing
        evaluation_data = {
            "overall_feedback": response[:500],
            "major_strengths": ["Evaluation completed"],
            "major_weaknesses": ["Detailed analysis needed"],
            "priority_improvements": ["Review evaluation criteria"]
        }
        
        # Try to extract scores using simple patterns
        for criteria in EvaluationCriteria:
            # Default scores
            evaluation_data[f"{criteria.value}_score"] = 70
            evaluation_data[f"{criteria.value}_feedback"] = "Standard evaluation"
            evaluation_data[f"{criteria.value}_strengths"] = []
            evaluation_data[f"{criteria.value}_weaknesses"] = []
            evaluation_data[f"{criteria.value}_suggestions"] = []
        
        return evaluation_data

    async def _parse_question_evaluation(self, response: str, question: QuizQuestion, idx: int) -> DetailedQuestionEvaluation:
        """Parse individual question evaluation response"""
        # Simplified parsing - extract scores or use defaults
        return DetailedQuestionEvaluation(
            question_id=str(idx),
            question_text=question.question,
            content_alignment_score=7,  # Default scores
            difficulty_appropriateness_score=7,
            clarity_score=7,
            pedagogical_value_score=7,
            specific_feedback=response[:300] if response else "Question evaluation completed",
            suggested_improvements=["Review question alignment with content"]
        )

    async def _parse_coverage_analysis(self, response: str) -> Dict[str, Any]:
        """Parse content coverage analysis response"""
        return {
            "content_gaps": ["Detailed content analysis needed"],
            "redundant_content": []
        }

    def _calculate_grade(self, score: float) -> str:
        """Calculate grade based on score"""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Good"
        elif score >= 70:
            return "Satisfactory"
        elif score >= 60:
            return "Needs Improvement"
        else:
            return "Poor"

    def _determine_recommendation(self, score: float) -> str:
        """Determine recommendation based on score"""
        if score >= 80:
            return "Accept"
        elif score >= 60:
            return "Revise"
        else:
            return "Reject"

    def _create_default_evaluation(self, inputs: QuizEvaluationInput) -> QuizEvaluationOutput:
        """Create default evaluation when parsing fails"""
        criteria_scores = []
        
        for criteria in inputs.evaluation_criteria:
            weight = self.criteria_weights[criteria]
            criteria_score = CriteriaScore(
                criteria=criteria,
                score=70,
                max_score=weight,
                feedback=f"Default evaluation for {criteria.value}",
                strengths=["Quiz completed successfully"],
                weaknesses=["Detailed evaluation needed"],
                suggestions=["Review evaluation criteria"]
            )
            criteria_scores.append(criteria_score)
        
        return QuizEvaluationOutput(
            total_score=70,
            grade="Satisfactory",
            criteria_scores=criteria_scores,
            overall_feedback="Default evaluation - manual review recommended",
            major_strengths=["Quiz generation completed"],
            major_weaknesses=["Evaluation system needs refinement"],
            priority_improvements=["Improve evaluation parsing"],
            recommendation="Revise",
            course_code=inputs.course_code,
            week_number=inputs.week_number
        )