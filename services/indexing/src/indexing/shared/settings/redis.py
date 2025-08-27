from pydantic import BaseModel


class RedisSetting(BaseModel):
    host: str
    port: int
    db: int
    password: str | None
