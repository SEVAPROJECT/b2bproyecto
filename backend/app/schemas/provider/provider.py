from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class ProfileBusinessModel(BaseModel):
    id: UUID = Field(default_factory=UUID, alias="id")
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    business_name: str = Field(..., min_length=2, max_length=100)
    tax_id: str = Field(..., min_length=2, max_length=100)