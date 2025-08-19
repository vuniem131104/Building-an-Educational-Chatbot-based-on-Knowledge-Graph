from chatbot.shared.state.chatbot_state import ChatbotState
from typing import Any
from base import BaseService
from base import BaseModel
from lite_llm import LiteLLMService
from lite_llm import LiteLLMInput
from lite_llm import Role 
from lite_llm import CompletionMessage
from chatbot.domain.main_agent.aggregator.prompts import ANSWER_AGGREGATION_PROMPT

class Aggregator_Schema(BaseModel):
    final_answer: str


class AggregatorService(BaseService):
    
    litellm_service: LiteLLMService

    async def process(self, state: ChatbotState) -> dict[str, Any]:
        try:
            user_message = f"""
            Main Question: {state['rephrased_question']}
            Sub-questions and related information:
            """

            sub_questions = state.get('sub_questions', [])
            refined_contexts = state.get('refined_contexts', [])
            
            for i, (sub_q, context) in enumerate(zip(sub_questions, refined_contexts), 1):
                user_message += f"""
                {i}. {sub_q}
                Context:
                {context}
                """

            user_message += """
            Please answer the main question based on the information from the sub-questions and context provided.
            """

            output = await self.litellm_service.process_async(
                inputs=LiteLLMInput(
                    messages=[
                        CompletionMessage(
                            role=Role.SYSTEM,
                            content=ANSWER_AGGREGATION_PROMPT
                        ),
                        CompletionMessage(
                            role=Role.USER,
                            content=user_message
                        )
                    ],
                    response_format=Aggregator_Schema,
                )
            )
            
            return {
                "answer": output.response.final_answer,
            }

        except Exception as e:
            return {
                "answer": f"Error occurred while aggregating answer: {str(e)}",
            }

