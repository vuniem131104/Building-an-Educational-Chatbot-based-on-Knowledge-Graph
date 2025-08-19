from base import BaseModel
from lite_llm import LiteLLMService
from langgraph.graph import StateGraph
from typing import Any 
from langgraph.graph import START, END
import httpx
from logger import get_logger 
from chatbot.shared.utils.chatbot_utils import format_context

from chatbot.shared.state.sub_agent_state import SubAgentState
from chatbot.domain.main_agent.sub_agent.context_refinement import ContextRefinementService
            
logger = get_logger(__name__)
class SubAgentService(BaseModel):
    
    litellm_service: LiteLLMService
    
    def rag(self, state: SubAgentState) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    "http://localhost:3005/v1/local_search",
                    json={"query": state["sub_question"]}
                )
                if response.status_code == 200:
                    return {
                        "raw_context": format_context(response.json())
                    }
                else:
                    return {
                        "raw_context": ""
                    }
        except httpx.TimeoutException:
            return {
                "raw_context": ""
            }
        except httpx.ConnectError:
            return {
                "raw_context": ""
            }
        except Exception as e:
            return {
                "raw_context": ""
            }
    
    @property
    def context_refinement(self) -> ContextRefinementService:
        return ContextRefinementService(litellm_service=self.litellm_service)

    @property
    def compiled_graph(self):
        graph = StateGraph(SubAgentState)

        graph.add_node("rag", self.rag)
        graph.add_node("context_refinement", self.context_refinement.process)
        graph.add_edge(START, "rag")
        graph.add_edge("rag", "context_refinement")
        graph.add_edge("context_refinement", END)
        return graph.compile()
    