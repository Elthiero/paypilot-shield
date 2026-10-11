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


class KeyIn(BaseModel):
    public_key: str  # base64 SPKI DER, P-256


class PrepareIn(BaseModel):
    policy_text: str
    rules: Rules


class SignIn(BaseModel):
    signature: str  # base64, 64 raw bytes


class RejectIn(BaseModel):
    reason: str = ""


class TamperIn(BaseModel):
    amount: Decimal | None = None
    payee_email: str | None = None


class PaymentIn(BaseModel):
    invoice_number: str
