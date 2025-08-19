from langgraph.graph import StateGraph
from langgraph.graph import START
from langgraph.graph import END 
from chatbot.domain.main_agent.memory import MemoryService
from chatbot.domain.main_agent.rephraser import RephraserService
from chatbot.domain.main_agent.decomposer import DecomposerService
from chatbot.domain.main_agent.sub_agent import SubAgentService
from chatbot.domain.main_agent.aggregator import AggregatorService
from chatbot.domain.main_agent.direct_answer import DirectAnswerService
from chatbot.domain.geoadmin_agent import GeoadminService
from chatbot.domain.autofill_agent import AutofillService
from chatbot.domain.profile_agent import ProfileService
from typing import Dict
import asyncio
from fastapi import Request
from functools import cached_property
from lite_llm.models import LiteLLMInput, CompletionMessage, Role
from typing_extensions import Literal
from langchain_core.runnables import RunnableLambda
from concurrent.futures import ThreadPoolExecutor
from fastapi import BackgroundTasks
from chatbot.shared.state.chatbot_state import ChatbotState 
from chatbot.shared.state.sub_agent_state import SubAgentState
from typing import Any
from base import BaseApplication
from base import BaseModel


class ChatbotApplicationInput(BaseModel):
    raw_question: str 
    user_id: str 
    conversation_id: str 
    conversation_history: list[Any]

class ChatbotApplicationOutput(BaseModel):
    raw_question: str 
    rephrased_question: str
    sub_questions: list[str]
    refined_contexts: list[str]
    answer: str 
    references: list[str]
    filled_profile_info: dict[str, Any] = {}
    detected_fields:  Dict[str, str]


class ChatbotApplication(BaseApplication):

    request: Request

    @property
    def memory_service(self) -> MemoryService:
        return MemoryService(database=self.request.app.state.database_service)
    @property
    def rephraser(self) -> RephraserService:
        return RephraserService(litellm_service=self.request.app.state.litellm_service)
    @property
    def profile_agent(self) -> ProfileService:
        return ProfileService()
    @property
    def autofill_agent(self) -> AutofillService:
        return AutofillService(litellm_service=self.request.app.state.litellm_service)

    @property
    def decomposer(self) -> DecomposerService:
        return DecomposerService(litellm_service=self.request.app.state.litellm_service)

    @cached_property
    def sub_agent(self) -> SubAgentService:
        return SubAgentService(litellm_service=self.request.app.state.litellm_service)
    
    @property
    def geoadmin_agent(self) -> GeoadminService:
        return GeoadminService()

    @property
    def aggregator(self) -> AggregatorService:
        return AggregatorService(litellm_service=self.request.app.state.litellm_service)
    
    @property
    def direct_answer(self) -> DirectAnswerService:
        return DirectAnswerService(litellm_service=self.request.app.state.litellm_service)
    
    
    # @property
    # def memory_service(self) -> MemoryService:
    #     return MemoryService()

    @property
    def nodes(self) -> dict[str, Any]:
        return {
            "conversation_history": self.memory_service.process,
            "direct_answer": self.direct_answer.process,
            "rephrase_question": self.rephraser.process,
            "decompose_question": self.decomposer.process,
            "sub_agent": self.gather_refined_contexts,
            "answer_aggregator": self.aggregator.process,
            "geoadmin_agent": self.geoadmin_agent.run,
            'autofill_agent': self.autofill_agent.process,
            'profile_agent': self.profile_agent.process,
            # "memory_retrieval": self.memory_service.retrieve_memory,
        }
    
    def route_agent(self, state: ChatbotState) -> Literal["rephrase_question", "geoadmin_agent", 'autofill_agent']:
        """
        LLM-based Router - quyết định routing câu hỏi đến agent phù hợp
        """
        PROMPT = """
        <role>
        Bạn là một router agent trong hệ thống chatbot hỗ trợ thủ tục hành chính.
        Nhiệm vụ của bạn là phân tích CÂU HỎI HIỆN TẠI và routing đến agent phù hợp.
        </role>
        
        <instruction>
        QUAN TRỌNG: Phân tích câu hỏi HIỆN TẠI, nhưng có thể tham khảo context từ lịch sử nếu câu hỏi hiện tại cần ngữ cảnh để hiểu đầy đủ.
        
        Với câu hỏi follow-up (như "Thế còn X thì sao?", "Còn Y thì thế nào?"), hãy xem xét ngữ cảnh từ câu hỏi trước để hiểu intent đầy đủ.
        </instruction>

        <constraint>
        Quy tắc routing THÔNG MINH:
        
        1. Route đến "autofill_agent" NẾU:
           - Câu hỏi hiện tại chứa từ khóa: "điền form", "làm đơn", "tạo đơn", "điền thông tin", "biểu mẫu"
           - User trực tiếp yêu cầu hỗ trợ điền form/đơn từ
           - Hỏi về cách thức điền form cụ thể
           
        2. Route đến "geoadmin_agent" NẾU:
           - Câu hỏi hiện tại chứa từ khóa địa lý: "địa chỉ", "ở đâu", "vị trí", "bản đồ", "tọa độ"
           - Hỏi về location của cơ quan, trụ sở, chi nhánh
           - Cần thông tin địa danh, định vị
           - Câu hỏi về chia tách/sáp nhập đơn vị hành chính (tỉnh, huyện, xã)
           - Follow-up questions về địa danh/đơn vị hành chính (VD: "Thế còn tỉnh X thì sao?")
           
        3. Route đến "rephrase_question" cho TẤT CẢ các trường hợp khác:
           - Câu hỏi về thủ tục hành chính chung
           - Câu hỏi thông tin, tư vấn
           - Mọi câu hỏi không rõ ràng thuộc 2 category trên
        </constraint>

        <input>
        Câu hỏi HIỆN TẠI cần phân tích: "{raw_question}"
        
        Ngữ cảnh hội thoại (để hiểu follow-up questions): {conversation_history}
        
        LƯU Ý: Nếu câu hỏi hiện tại là follow-up (như "Thế còn X thì sao?"), hãy kết hợp với ngữ cảnh để hiểu intent đầy đủ.
        </input>
        
        <output>
        Dựa trên phân tích câu hỏi HIỆN TẠI, trả về CHÍNH XÁC một trong:
        - "autofill_agent"
        - "geoadmin_agent" 
        - "rephrase_question"
        </output>
        """

        # Limit conversation history để tránh bias quá nhiều
        conversation_history = state.get('conversation_history', [])
        # Chỉ lấy 2-3 turns gần nhất để có context nhưng không bị overwhelm
        limited_history = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
        # print("Conversation History", limited_history)
        prompt = PROMPT.format(
            raw_question=state.get('raw_question', ''),
            conversation_history=limited_history if limited_history else "Không có lịch sử hội thoại"
        )

        response = self.request.app.state.litellm_service.process(
            LiteLLMInput(
                messages=[
                    CompletionMessage(
                        role=Role.SYSTEM,
                        content="Bạn là một router agent thông minh. Phân tích câu hỏi hiện tại và tham khảo ngữ cảnh khi cần thiết để hiểu follow-up questions. Đưa ra quyết định routing chính xác dựa trên intent thật sự của user."
                    ),
                    CompletionMessage(
                        role=Role.USER,
                        content=prompt
                    )
                ],
                reasoning_effort="medium",
            )
        )

        # Parse response để lấy routing decision
        next_action = response.response.strip().replace('"', '').replace("'", "")
        
        # Validate routing decision
        valid_routes = ["autofill_agent", "geoadmin_agent", "rephrase_question"]
        if next_action not in valid_routes:
            next_action = "rephrase_question"  # Default fallback
            
        print(f"🔀 LLM Router decision for '{state.get('raw_question', '')[:50]}...': {next_action}")
        print(f"📝 Limited conversation history length: {len(limited_history)}")
        return next_action

        
    async def gather_refined_contexts(self, state: ChatbotState) -> dict[str, Any]:
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(5)
        
        async def process_sub_question(sub_question: str) -> str:
            async with semaphore:
                # Use ainvoke directly since it's async
                result = await self.sub_agent.compiled_graph.ainvoke(
                    SubAgentState(
                        sub_question=sub_question,
                        raw_context="",
                        refined_context="",
                        references=[],
                    )
                )
                if result and 'refined_context' in result and 'references' in result:
                    return result['refined_context'], result['references']
                return "", []

        # Process all sub-questions concurrently with semaphore control
        tasks = [process_sub_question(sub_question) for sub_question in state['sub_questions']]
        results = await asyncio.gather(*tasks)
        
        # Filter out empty results
        refined_contexts = [result[0] for result in results if result]
        references = [ref for result in results for ref in result[1]]

        return {
            "refined_contexts": refined_contexts,
            "references": references
        }
            
    @property
    def compiled_graph(self) -> StateGraph:
        graph = StateGraph(ChatbotState)
        for key, tool in self.nodes.items():
            graph.add_node(key, tool)
            
        def route_rephraser(state: ChatbotState) -> Literal["decompose_question", "direct_answer"]:
            need_rag = state.get('need_rag', False)
            if need_rag:
                return "decompose_question"
            else:
                return "direct_answer"
        
        graph.add_edge(START, "conversation_history")
        graph.add_conditional_edges(
            "conversation_history",
            self.route_agent,
        )
        
        # Edges từ các agent đến END
        graph.add_edge("autofill_agent",  "profile_agent")
        graph.add_edge("profile_agent", END)
        graph.add_edge("geoadmin_agent", END)

        # Flow cho rephrase_question
        graph.add_conditional_edges(
            "rephrase_question",
            route_rephraser,
        )
        graph.add_edge("decompose_question", "sub_agent")
        graph.add_edge("sub_agent", "answer_aggregator")
        graph.add_edge("direct_answer", END)
        graph.add_edge("answer_aggregator", END)
        
        return graph.compile()

    async def run(self, input: ChatbotApplicationInput, background_tasks: BackgroundTasks) -> ChatbotApplicationOutput:
        result = await self.compiled_graph.ainvoke(
            ChatbotState(
                raw_question=input.raw_question,
                rephrased_question="",
                sub_questions=[],
                answer="",
                conversation_history=[],
                refined_contexts=[],
                references=[],
                detected_fields={},
                filled_profile_info={},
            )
        )
        background_tasks.add_task(
            self.memory_service.save_conversation_history,
            input.raw_question,
            result.get('rephrased_question', ''),
            result.get('sub_questions', []),
            result.get('answer', ''),
        )


        return ChatbotApplicationOutput(
            raw_question=input.raw_question,
            rephrased_question=result.get('rephrased_question', ''),
            sub_questions=result.get('sub_questions', []),
            answer=result.get('answer', ''),
            refined_contexts=result.get('refined_contexts', []),
            references=list(set(result.get('references', []))),
            filled_profile_info=result.get('filled_profile_info', {}),
            detected_fields=result.get('detected_fields', {})
        )