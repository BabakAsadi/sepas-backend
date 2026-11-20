from pydantic import BaseModel, Field


class WalletTopUpPayload(BaseModel):
    amount: int = Field(gt=0)
    description: str | None = Field(default=None, max_length=500)


class WalletAllocationPayload(BaseModel):
    enrollment_id: int = Field(gt=0)
    amount: int = Field(gt=0)
    description: str | None = Field(default=None, max_length=500)
