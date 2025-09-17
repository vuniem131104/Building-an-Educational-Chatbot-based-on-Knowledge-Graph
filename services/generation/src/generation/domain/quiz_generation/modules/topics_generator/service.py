from __future__ import annotations
from pydantic import Field
from base import BaseModel
from base import BaseService
from lite_llm import LiteLLMService
from lite_llm import LiteLLMInput
from lite_llm import CompletionMessage
from lite_llm import Role
from generation.domain.quiz_generation.prompts import TOPIC_GENERATOR_SYSTEM_PROMPT
from generation.domain.quiz_generation.prompts import TOPIC_GENERATOR_USER_PROMPT
from generation.domain.quiz_generation.modules.concept_card_extractor import ConceptCard
from generation.shared.settings import TopicGeneratorSetting
from generation.shared.models import Topic
from logger import get_logger

logger = get_logger(__name__)


class Topics(BaseModel):
    topics: list[Topic]
    

class TopicGeneratorInput(BaseModel):
    previous_lectures: list[str]
    lecture_learning_outcomes: list[str]
    concept_cards: list[ConceptCard]
    number_of_topics: int
    week_number: int
    course_code: str 

class TopicGeneratorOutput(BaseModel):
    topics: Topics
    week_number: int
    course_code: str
    

class TopicGeneratorService(BaseService):
    litellm_service: LiteLLMService
    settings: TopicGeneratorSetting

    async def process(self, inputs: TopicGeneratorInput) -> TopicGeneratorOutput:
        try:
            user_context = self._prepare_context(inputs)
            
            output = await self.litellm_service.process_async(
                inputs=LiteLLMInput(
                    model=self.settings.model,
                    messages=[
                        CompletionMessage(
                            role=Role.SYSTEM,
                            content=TOPIC_GENERATOR_SYSTEM_PROMPT
                        ),
                        CompletionMessage(
                            role=Role.USER,
                            content=TOPIC_GENERATOR_USER_PROMPT.format(
                                num_topics=inputs.number_of_topics,
                                user_context=user_context
                            )
                        )
                    ],
                    response_format=Topics,
                    temperature=self.settings.temperature,
                    top_p=self.settings.top_p,
                    n=self.settings.n,
                    frequency_penalty=self.settings.frequency_penalty,
                    max_completion_tokens=self.settings.max_completion_tokens,
                    reasoning_effort=self.settings.reasoning_effort,
                )
            )
            
            logger.info(
                "Topics generated successfully",
                extra={
                    "course_code": inputs.course_code,
                    "week_number": inputs.week_number,
                }
            )

            return TopicGeneratorOutput(
                topics=output.response,
                week_number=inputs.week_number,
                course_code=inputs.course_code
            )

        except Exception as e:
            logger.exception(
                "Error when processing topic generation with litellm",
                extra={
                    "week_number": inputs.week_number,
                    "course_code": inputs.course_code,
                    "error": str(e),
                } 
            )
            raise e

    def _prepare_context(self, inputs: TopicGeneratorInput) -> str:
        """Prepare comprehensive context from all input components"""
        context_parts = []
        
        # Add course and week information
        context_parts.append(f"Course: {inputs.course_code}")
        context_parts.append(f"Week: {inputs.week_number}")
        context_parts.append("")
        
        # Add learning outcomes for this week
        if inputs.lecture_learning_outcomes:
            context_parts.append("LEARNING OUTCOMES FOR THIS WEEK:")
            for i, outcome in enumerate(inputs.lecture_learning_outcomes, 1):
                context_parts.append(f"{i}. {outcome}")
            context_parts.append("")
        
        # Add previous lectures context
        if inputs.previous_lectures:
            context_parts.append("PREVIOUS LECTURES CONTEXT:")
            for lecture in inputs.previous_lectures:
                context_parts.append(lecture)
            context_parts.append("")
        
        # Add concept cards from current week
        if inputs.concept_cards:
            context_parts.append("CONCEPT CARDS FROM CURRENT LECTURE:")
            for i, card in enumerate(inputs.concept_cards, 1):
                context_parts.append(f"Concept {i}: {card.name}")
                context_parts.append(f"Summary: {'; '.join(card.summary)}")
                if card.formulae:
                    context_parts.append(f"Formulae: {'; '.join(card.formulae)}")
                if card.examples:
                    context_parts.append(f"Examples: {'; '.join(card.examples)}")
                context_parts.append("")
        
        return "\n".join(context_parts)