from chatbot.domain.main_agent.rephraser.prompts import REPHRASED_QUESTION_PROMPT
from base import BaseService
from base import BaseModel
from lite_llm import LiteLLMService
from lite_llm import LiteLLMInput
from lite_llm import Role 
from lite_llm import CompletionMessage
from typing import Any
from chatbot.shared.state.chatbot_state import ChatbotState

class Rephraser_Schema(BaseModel):
    rephrased_question: str
    need_rag: bool
    
class RephraserService(BaseService):
    
    litellm_service: LiteLLMService

    async def process(self, state: ChatbotState) -> dict[str, Any]:

        conversation_history = self.convert_history_to_string(state["conversation_history"])
        output = await self.litellm_service.process_async(
            inputs=LiteLLMInput(
                messages=[
                    CompletionMessage(
                        role=Role.SYSTEM,
                        content=REPHRASED_QUESTION_PROMPT
                    ),
                    CompletionMessage(
                        role=Role.USER,
                        content=f"The raw question is: {state['raw_question']}. The history is: {conversation_history}. The sub questions are: {state['sub_questions']}. The refined contexts are: {state['refined_contexts']}. Please rephrase the question and determine if it needs RAG."
                    )
                ],
                response_format=Rephraser_Schema,
            )
        )
    
        return {
            "rephrased_question": output.response.rephrased_question,
            "need_rag": output.response.need_rag
        }
    def convert_history_to_string(self, history: list[dict[str, Any]]) -> str:
        return "\n".join(
            f"{msg['type']}: {msg['content']}" for msg in history
        ) if history else "No conversation history available."