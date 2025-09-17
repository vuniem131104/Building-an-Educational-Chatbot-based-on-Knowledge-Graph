from typing import Any
from generation.shared.states import ValidatorState
from generation.shared.settings import QuizValidatorSetting
from generation.shared.models import QuizQuestion 
from generation.domain.quiz_generation.modules.validator.multi_agents.factual import FactualService
from generation.domain.quiz_generation.modules.validator.multi_agents.pedagogical import PedagogicalService
from generation.domain.quiz_generation.modules.validator.multi_agents.psychometric import PsychometricService
from easydict import EasyDict
from functools import cached_property

from base import BaseService
from lite_llm import LiteLLMService
from logger import get_logger

from langgraph.graph import StateGraph
from langgraph.graph import START
from langgraph.graph import END

logger = get_logger(__name__)


class QuizValidatorService(BaseService):
    litellm_service: LiteLLMService
    settings: QuizValidatorSetting
    
    @property
    def factual_service(self) -> FactualService:
        return FactualService(
            settings=self.settings.factual,
            litellm_service=self.litellm_service
        )

    @property
    def pedagogical_service(self) -> PedagogicalService:
        return PedagogicalService(
            settings=self.settings.pedagogical,
            litellm_service=self.litellm_service
        )

    @property
    def psychometric_service(self) -> PsychometricService:
        return PsychometricService(
            settings=self.settings.psychometric,
            litellm_service=self.litellm_service
        )
        
    @property
    def psychometric_service(self) -> PsychometricService:
        return PsychometricService(
            settings=self.settings.psychometric,
            litellm_service=self.litellm_service
        )
        
    def aggregate(self, state: ValidatorState) -> dict[str]:
        return {
            "score": int((
                state['factual_score'] +
                state['pedagogical_score'] +
                state['psychometric_score']
            ) / 3),
            "feedback": "\n\n".join([
                "The feedback from factual validator:" + "\n" + state['factual_message'],
                "The feedback from pedagogical validator:" + "\n" + state['pedagogical_message'],
                "The feedback from psychometric validator:" + "\n" + state['psychometric_message']
            ])
        }

    @property
    def nodes(self) -> EasyDict:
        return EasyDict({
            "factual": self.factual_service.process,
            "pedagogical": self.pedagogical_service.process,
            "psychometric": self.psychometric_service.process,
            "aggregator": self.aggregate,
        })
    
    @cached_property
    def compiled_graph(self):
        graph = StateGraph(ValidatorState)
        
        for key, tool in self.nodes.items():
            graph.add_node(key, tool)
            
        graph.add_edge(START, "factual")
        graph.add_edge(START, "pedagogical")
        graph.add_edge(START, "psychometric")
        
        graph.add_edge("factual", "aggregator")
        graph.add_edge("pedagogical", "aggregator")
        graph.add_edge("psychometric", "aggregator")
        
        graph.add_edge("aggregator", END)
        
        return graph.compile()
    
    async def process(self, inputs: ValidatorState) -> dict[str, Any]:
        try:
            result = await self.compiled_graph.ainvoke(inputs)
            return result
        except Exception as e:
            logger.exception(
                'Error in QuizValidatorService process',
                extra={
                    'state': inputs,
                    'error': str(e),
                },
            )
            return {
                "score": 100,
                "feedback": "",
            }
    
    
# if __name__ == "__main__":
#     from lite_llm import LiteLLMSetting
#     import asyncio
#     from pydantic import HttpUrl, SecretStr
#     import json
#     from generation.shared.settings import FactualSetting
#     from generation.shared.settings import PsychometricSetting
#     from generation.shared.settings import PedagogicalSetting
    
#     litellm_setting = LiteLLMSetting(
#         url=HttpUrl("http://localhost:9510"),
#         token=SecretStr("abc123"),
#         model="claude-sonnet-4-20250514",
#         frequency_penalty=0.0,
#         n=1,
#         temperature=0.0,
#         top_p=1.0,
#         max_completion_tokens=10000,
#         dimension=1536,
#         embedding_model="gemini-embedding"
#     )

#     factual_settings = FactualSetting(
#         model="claude-sonnet-4-20250514",
#         temperature=1.0,  # Must be 1.0 when reasoning is enabled for Claude
#         top_p=1.0,
#         n=1,
#         frequency_penalty=0.0,
#         max_completion_tokens=10000,
#         reasoning_effort="medium"
#     )

#     pedagogical_settings = PedagogicalSetting(
#         model="claude-sonnet-4-20250514",
#         temperature=1.0,  # Must be 1.0 when reasoning is enabled for Claude
#         top_p=1.0,
#         n=1,
#         frequency_penalty=0.0,
#         max_completion_tokens=10000,
#         reasoning_effort="medium"
#     )

#     psychometric_settings = PsychometricSetting(
#         model="claude-sonnet-4-20250514",
#         temperature=1.0,  # Must be 1.0 when reasoning is enabled for Claude
#         top_p=1.0,
#         n=1,
#         frequency_penalty=0.0,
#         max_completion_tokens=10000,
#         reasoning_effort="medium"
#     )

#     litellm_service = LiteLLMService(litellm_setting=litellm_setting)
#     validator_service = QuizValidatorService(
#         litellm_service=litellm_service,
#         settings=QuizValidatorSetting(
#             factual=factual_settings,
#             pedagogical=pedagogical_settings,
#             psychometric=psychometric_settings
#         )
#     )
    

#     async def test():
#         with open('/home/vuiem/KLTN/quiz_generation_test_output.json', 'r', encoding='utf-8') as f:
#             data = json.load(f)
            
#         for index in range(len(data['quiz_questions'])):
#             output = await validator_service.process(
#                 inputs=ValidatorState(
#                     quiz_question=QuizQuestion(
#                         **(data['quiz_questions'][index])
#                     ),
#                     factual_message="",
#                     factual_score=0,
#                     psychometric_message="",
#                     psychometric_score=0,
#                     pedagogical_message="",
#                     pedagogical_score=0,
#                     score=0,
#                     feedback="",
#                 )
#             )
#             output = {
#                 "factual_message": output.get("factual_message"),
#                 "factual_score": output.get("factual_score"),
#                 "pedagogical_message": output.get("pedagogical_message"),
#                 "pedagogical_score": output.get("pedagogical_score"),
#                 "psychometric_message": output.get("psychometric_message"),
#                 "psychometric_score": output.get("psychometric_score"),
#                 "score": output.get("score"),
#                 "feedback": output.get("feedback"),
#             }
#             with open(f"validator/validation_output_{index}.json", "w", encoding='utf-8') as f:
#                 json.dump(output, f, ensure_ascii=False, indent=4)
                
#     asyncio.run(test())
