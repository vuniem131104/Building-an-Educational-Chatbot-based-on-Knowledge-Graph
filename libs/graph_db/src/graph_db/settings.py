from base import BaseModel

class Neo4jSetting(BaseModel):
    uri: str
    username: str
    password: str