from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str
    description: str 
    price: float
    tax: float | None
    
print(Item.model_json_schema())