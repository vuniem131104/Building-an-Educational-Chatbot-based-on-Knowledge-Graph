from __future__ import annotations

from base import BaseModel
from base import BaseService
from lite_llm import LiteLLMService
from lite_llm import LiteLLMInput
from lite_llm import CompletionMessage
from lite_llm import Role
from generation.domain.parser.concept_card_extractor.prompts import CONCEPT_CARD_EXTRACTOR_SYSTEM_PROMPT
from generation.shared.settings.parser import ParserSetting
from logger import get_logger

logger = get_logger(__name__)


class ConceptCard(BaseModel):
    name: str
    summary: list[str]
    formulae: list[str]
    examples: list[str]
    common_pitfalls: list[str]
    page: list[int] 
    

class ConceptCards(BaseModel):
    concept_cards: list[ConceptCard]
    outcomes: list[str]
    lecture_summary: str
    

class ConceptCardExtractorInput(BaseModel):
    contents: str 
    week_number: int
    course_code: str 
    

class ConceptCardExtractorOutput(BaseModel):
    concept_cards: list[ConceptCard]
    outcomes: list[str]
    lecture_summary: str
    week_number: int
    course_code: str
    

class ConceptCardExtractorService(BaseService):
    litellm_service: LiteLLMService
    settings: ParserSetting
    
    async def process(self, inputs: ConceptCardExtractorInput) -> ConceptCardExtractorOutput:
        try:
            output = await self.litellm_service.process_async(
                inputs=LiteLLMInput(
                    model=self.settings.concept_card_extractor.model,
                    messages=[
                        CompletionMessage(
                            role=Role.SYSTEM,
                            content=CONCEPT_CARD_EXTRACTOR_SYSTEM_PROMPT
                        ),
                        CompletionMessage(
                            role=Role.USER,
                            content=inputs.contents
                        )
                    ],
                    response_format=ConceptCards,
                    temperature=self.settings.concept_card_extractor.temperature,
                    top_p=self.settings.concept_card_extractor.top_p,
                    n=self.settings.concept_card_extractor.n,
                    frequency_penalty=self.settings.concept_card_extractor.frequency_penalty,
                    max_completion_tokens=self.settings.concept_card_extractor.max_completion_tokens,
                    reasoning_effort=self.settings.concept_card_extractor.reasoning_effort,
                )
            )

            return ConceptCardExtractorOutput(
                concept_cards=output.response.concept_cards,
                outcomes=output.response.outcomes,
                lecture_summary=output.response.lecture_summary,
                week_number=inputs.week_number,
                course_code=inputs.course_code
            )

        except Exception as e:
            logger.exception(
                "Error when processing concept card extraction",
                extra={
                    "week_number": inputs.week_number,
                    "course_code": inputs.course_code,
                    "error": str(e),
                } 
            )
    