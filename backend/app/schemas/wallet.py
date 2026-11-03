from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field

class WithdrawalRequestModel(BaseModel):
    amount_usd: Decimal = Field(gt=0, decimal_places=2)
    method: str
    details: dict
    idempotency_key: str = Field(min_length=8, max_length=128)

class CheckinResponse(BaseModel):
    coins: int
    streak: int

class ReferralApplyRequest(BaseModel):
    code: str = Field(min_length=4, max_length=16)

class PayoutMethodResponse(BaseModel):
    id: UUID
    method: str

