from base import BaseModel 

class ChunkerSetting(BaseModel):
    max_token_per_chunk: int 
    min_token_per_chunk: int