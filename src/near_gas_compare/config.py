from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="near-gas-comparison-api")
    app_env: str = Field(default="production")

    near_mainnet_rpc_urls: str = Field(default="https://rpc.mainnet.near.org,https://free.rpc.fastnear.com")
    eth_mainnet_rpc_urls: str = Field(
        default="https://ethereum-rpc.publicnode.com,https://eth.llamarpc.com,https://1rpc.io/eth"
    )
    coingecko_price_url: str = Field(
        default="https://api.coingecko.com/api/v3/simple/price?ids=near,ethereum&vs_currencies=usd"
    )

    request_timeout_seconds: float = Field(default=15.0)
    block_sample_size: int = Field(default=100, ge=10, le=500)
    cache_ttl_seconds: int = Field(default=30, ge=0, le=600)

    model_config = SettingsConfigDict(env_prefix="NEAR_GAS_COMPARE_")


settings = Settings()
