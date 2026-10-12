from decimal import Decimal
from pydantic import BaseModel, Field

MAX_POLICY_TEXT = 2000


class Rules(BaseModel):
    # The LLM may only draft these values. The owner reviews and signs them.
    auto_limit: Decimal = Field(ge=0, le=100000)
    currency: str = Field("USD", pattern=r"^[A-Z]{3}$")
    monthly_budget: Decimal = Field(ge=0, le=1000000)
    require_verified: bool = True
    valid_until: str = Field(max_length=10)  # ISO date


class LoginIn(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(max_length=200)


class ChatIn(BaseModel):
    message: str = Field(max_length=2000)


class KeyIn(BaseModel):
    public_key: str = Field(max_length=300)  # base64 SPKI DER, P-256
    password: str | None = Field(None, max_length=200)  # required to replace an existing key


class PrepareIn(BaseModel):
    policy_text: str = Field(max_length=MAX_POLICY_TEXT)
    rules: Rules


class SignIn(BaseModel):
    signature: str = Field(max_length=200)  # base64, 64 raw bytes


class RejectIn(BaseModel):
    reason: str = Field("", max_length=500)


class TamperIn(BaseModel):
    amount: Decimal | None = None
    payee_email: str | None = None


class PaymentIn(BaseModel):
    invoice_number: str = Field(max_length=50)


class InvoiceIn(BaseModel):
    supplier_id: int
    number: str | None = Field(None, max_length=50, pattern=r"^[A-Za-z0-9._-]+$")  # blank = next INV-00N
    description: str = Field(min_length=1, max_length=MAX_POLICY_TEXT)
    amount: Decimal = Field(gt=0, le=100000, decimal_places=2)
    currency: str = Field("USD", pattern=r"^[A-Z]{3}$")
    payee_email: str = Field(max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
