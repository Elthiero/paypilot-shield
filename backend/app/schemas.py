from decimal import Decimal
from pydantic import BaseModel, Field


class Rules(BaseModel):
    # The LLM may only draft these values. The owner reviews and signs them.
    auto_limit: Decimal = Field(ge=0, le=100000)
    currency: str = "USD"
    monthly_budget: Decimal = Field(ge=0, le=1000000)
    require_verified: bool = True
    valid_until: str  # ISO date


class LoginIn(BaseModel):
    email: str
    password: str


class ChatIn(BaseModel):
    message: str
