from base import BaseApplication 
from fastapi import Request

from rag.domain.local_search import LocalSearchInput 
from rag.domain.local_search import LocalSearch
from rag.domain.local_search import LocalSearchOutput

class LocalSearchApplicationInput(LocalSearchInput):
    pass

class LocalSearchApplicationOutput(LocalSearchOutput):
    pass

class LocalSearchApplication(BaseApplication):
    
    request: Request
    
    @property
    def local_search(self) -> LocalSearch:
        return LocalSearch(
            neo4j_service=self.request.app.state.neo4j_service,
            litellm_service=self.request.app.state.litellm_service,
            local_search_settings=self.request.app.state.settings.local_search_settings,
        )

    async def run(self, inputs: LocalSearchApplicationInput) -> LocalSearchApplicationOutput:
        """
        Run the local search application with the provided inputs.

        Args:
            inputs (LocalSearchApplicationInput): The input containing the text to process.

        Returns:
            LocalSearchApplicationOutput: The output containing the search results.
        """
        return await self.local_search.process(inputs)