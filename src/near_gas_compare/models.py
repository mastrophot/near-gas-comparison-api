from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ChainGasSnapshot(BaseModel):
    chain: str
    cost_native: float = Field(ge=0)
    cost_usd: float = Field(ge=0)
    speed: str
    speed_seconds: float = Field(ge=0)
    gas_price: str
    transfer_gas_units: int = Field(gt=0)


class ComparisonSummary(BaseModel):
    near_is_cheaper_by_usd: float
    near_is_cheaper_by_percent: float
    cost_ratio_eth_over_near: float


class SimpleChainSnapshot(BaseModel):
    cost_usd: float = Field(ge=0)
    speed: str


class SimpleGasComparisonResponse(BaseModel):
    near: SimpleChainSnapshot
    ethereum: SimpleChainSnapshot


class GasComparisonResponse(BaseModel):
    generated_at: str
    near: ChainGasSnapshot
    ethereum: ChainGasSnapshot
    summary: ComparisonSummary
    methodology: dict[str, str]
    sources: dict[str, list[str]]
    is_stale: bool = False
    stale_reason: Optional[str] = None
