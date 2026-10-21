from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    name: str
    vendor: str
    input_price: float
    output_price: float


class EstimateRequest(BaseModel):
    model: str
    requests_per_day: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    days: int = Field(default=30, ge=0)
