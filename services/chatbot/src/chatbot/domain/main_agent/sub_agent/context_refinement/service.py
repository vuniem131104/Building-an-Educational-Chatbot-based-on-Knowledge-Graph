from chatbot.domain.main_agent.sub_agent.context_refinement.prompts import CONTEXT_REFINEMENT_PROMPT
from base import BaseService
from base import BaseModel
from lite_llm import LiteLLMService
from lite_llm import LiteLLMInput
from lite_llm import Role 
from lite_llm import CompletionMessage
from typing import Any
from chatbot.shared.state.sub_agent_state import SubAgentState

class ContextRefinement_Schema(BaseModel):
    refined_context: str
    references: list[str]

class ContextRefinementService(BaseService):
    
    litellm_service: LiteLLMService

    async def process(self, state: SubAgentState) -> dict[str, Any]:
        output = await self.litellm_service.process_async(
            inputs=LiteLLMInput(
                messages=[
                    CompletionMessage(
                        role=Role.SYSTEM,
                        content=CONTEXT_REFINEMENT_PROMPT
                    ),
                    CompletionMessage(
                        role=Role.USER,
                        content=f"Refine the context for the sub-question '{state['sub_question']}': {state['raw_context']}"
                    )
                ],
                response_format=ContextRefinement_Schema,
            )
        )
        return {
            "refined_context": output.response.refined_context,
            "references": output.response.references
        }