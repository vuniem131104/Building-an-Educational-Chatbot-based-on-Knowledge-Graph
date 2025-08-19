from chatbot.shared.state.chatbot_state import ChatbotState
from typing import Any
from chatbot.domain.main_agent.direct_answer.prompts import TRADITIONAL_CHATBOT_PROMPT
from base import BaseService
from base import BaseModel
from lite_llm import LiteLLMService
from lite_llm import LiteLLMInput
from lite_llm import Role 
from lite_llm import CompletionMessage

class Direct_Answer_Schema(BaseModel):
    answer: str


class DirectAnswerService(BaseService):

    litellm_service: LiteLLMService

    async def process(self, state: ChatbotState) -> dict[str, Any]:
        output = await self.litellm_service.process_async(
            inputs=LiteLLMInput(
                messages=[
                    CompletionMessage(
                        role=Role.SYSTEM,
                        content=TRADITIONAL_CHATBOT_PROMPT
                    ),
                    CompletionMessage(
                        role=Role.USER,
                        content=f"The question is: {state['rephrased_question']}. Here is the conversation history: {state['conversation_history']}."
                    )
                ],
                response_format=Direct_Answer_Schema,
            )
        )

        return {
            "answer": output.response.answer
        }

