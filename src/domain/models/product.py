from pydantic import BaseModel
from typing import Optional, List


class Product(BaseModel):
    id: str
    name: str
    price: float
    description: Optional[str] = None
    colors: Optional[List[str]] = None
    capacity_oz: Optional[int] = None
    image_url: Optional[str] = None
