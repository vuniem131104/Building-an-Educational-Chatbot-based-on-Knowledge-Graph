from pydantic import BaseModel
from chatbot.domain.main_agent.decomposer.prompts import QUESTION_DECOMPOSITION_PROMPT
from base import BaseService
from base import BaseModel
from lite_llm import LiteLLMService
from lite_llm import LiteLLMInput
from lite_llm import Role 
from lite_llm import CompletionMessage
from typing import List
from typing import Any
from chatbot.shared.state.chatbot_state import ChatbotState

class Decomposer_Schema(BaseModel):
    sub_questions: List[str]
    
class DecomposerService(BaseService):
    
    litellm_service: LiteLLMService

    async def process(self, state: ChatbotState) -> dict[str, Any]:
        output = await self.litellm_service.process_async(
            inputs=LiteLLMInput(
                messages=[
                    CompletionMessage(
                        role=Role.SYSTEM,
                        content=QUESTION_DECOMPOSITION_PROMPT
                    ),
                    CompletionMessage(
                        role=Role.USER,
                        content=f"Decompose this question into specific sub-questions: {state['rephrased_question']}"
                    )
                ],
                response_format=Decomposer_Schema,
            )
        )
        
        return {
            "sub_questions": output.response.sub_questions  
        }
    