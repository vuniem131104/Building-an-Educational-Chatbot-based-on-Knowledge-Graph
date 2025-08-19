from base import BaseService, BaseModel
from typing import Dict, Any, List, Literal
import json
from lite_llm import LiteLLMService, LiteLLMInput, CompletionMessage, Role


class RouterInput(BaseModel):
    raw_question: str
    answer: str
    conversation_history: List[Dict[str, str]]


class RouterOutput(BaseModel):
    next_action: Literal["autofill_agent", "__end__"]
    confidence: float
    reasoning: str


class RouterLLMSchema(BaseModel):
    next_action: Literal["autofill_agent", "__end__"]
    confidence: float
    reasoning: str


class RouterService(BaseService):
    """LLM-based routing service để quyết định next action"""

    litellm_service: LiteLLMService

    def process(self, input: RouterInput) -> RouterOutput:
        """
        Sử dụng LLM để quyết định routing
        """
        # Always use fallback for now to test system stability
        if not hasattr(self, 'litellm_service') or not self.litellm_service:
            print("Using fallback routing: No LiteLLM service available")
            return self._fallback_routing(input)
        
        # Try LLM first, fallback on any error
        try:
            return self._llm_routing(input)
        except Exception as e:
            print(f"LLM routing failed, using fallback: {e}")
            return self._fallback_routing(input)

    def _llm_routing(self, input: RouterInput) -> RouterOutput:
        """
        LLM quyết định có nên route đến autofill agent không
        """
        prompt = f"""
        Bạn là một router agent trong hệ thống chatbot hỗ trợ thủ tục hành chính.
        
        Nhiệm vụ: Quyết định có nên chuyển hướng đến autofill agent để điền form tự động hay không.
        
        Thông tin đầu vào:
        - Câu hỏi của user: "{input.raw_question}"
        - Câu trả lời đã sinh: "{input.answer}"
        
        Quy tắc routing:
        1. Route đến "autofill_agent" nếu:
           - User chủ động yêu cầu điền form (điền form, fill form, làm đơn, tạo đơn)
           - User hỏi về thủ tục hành chính và answer đề cập đến form/hồ sơ/đơn
           - Context suggest user cần hỗ trợ điền thông tin
        
        2. Route đến "__end__" nếu:
           - Câu hỏi chung chung, không liên quan thủ tục
           - User chỉ hỏi thông tin, không có ý định làm thủ tục
           - Đã trả lời đầy đủ và không cần hỗ trợ thêm
        
        Trả về kết quả với next_action, confidence (0.0-1.0), và reasoning.
        """
        
        try:
            llm_input = LiteLLMInput(
                messages=[
                    CompletionMessage(
                        role=Role.SYSTEM,
                        content="Bạn là một router agent chuyên nghiệp. Phân tích và đưa ra quyết định routing."
                    ),
                    CompletionMessage(
                        role=Role.USER,
                        content=prompt
                    )
                ],
                response_format=RouterLLMSchema,
            )
            
            response = self.litellm_service.process(llm_input)
            
            # Access the structured response
            return RouterOutput(
                next_action=response.response.next_action,
                confidence=response.response.confidence,
                reasoning=response.response.reasoning
            )
            
        except Exception as e:
            print(f"LLM routing error: {e}")
            return self._fallback_routing(input)

    def _fallback_routing(self, input: RouterInput) -> RouterOutput:
        """
        Fallback routing logic nếu LLM không hoạt động
        """
        user_input = input.raw_question.lower()
        answer = input.answer.lower()
        
        # Check explicit keywords
        autofill_keywords = ["điền form", "fill form", "làm đơn", "tạo đơn", "điền đơn"]
        has_explicit_request = any(keyword in user_input for keyword in autofill_keywords)
        
        if has_explicit_request:
            return RouterOutput(
                next_action="autofill_agent",
                confidence=0.9,
                reasoning="Fallback: User chủ động yêu cầu autofill"
            )
        
        # Check context suggest
        procedure_keywords = ["cmnd", "cccd", "hộ chiếu", "đăng ký", "cấp"]
        form_keywords = ["hồ sơ", "đơn", "form", "biểu mẫu"]
        
        has_procedure_context = any(keyword in user_input for keyword in procedure_keywords)
        has_form_context = any(keyword in answer for keyword in form_keywords)
        
        if has_procedure_context and has_form_context:
            return RouterOutput(
                next_action="autofill_agent",
                confidence=0.6,
                reasoning="Fallback: Context về thủ tục + answer chứa form"
            )
        
        return RouterOutput(
            next_action="__end__",
            confidence=0.8,
            reasoning="Fallback: Không có trigger cho autofill"
        )

    def get_next_action(self, raw_question: str, answer: str) -> str:
        """
        Helper method để get routing decision nhanh
        """
        input_data = RouterInput(
            raw_question=raw_question,
            answer=answer,
            conversation_history=[]
        )
        
        result = self.process(input_data)
        return result.next_action
