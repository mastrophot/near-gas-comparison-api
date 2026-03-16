from __future__ import annotations

from datetime import datetime, timezone
import asyncio
import time

from .config import settings
from .models import ChainGasSnapshot, ComparisonSummary, GasComparisonResponse
from .providers import DataProvider


class GasComparisonService:
    def __init__(self, provider: DataProvider | None = None):
        self.provider = provider or DataProvider()
        self._cache_lock = asyncio.Lock()
        self._cached_payload: GasComparisonResponse | None = None
        self._cached_at_monotonic: float = 0.0

    async def compare(self) -> GasComparisonResponse:
        if settings.cache_ttl_seconds > 0 and self._cached_payload is not None:
            if (time.monotonic() - self._cached_at_monotonic) < settings.cache_ttl_seconds:
                return self._cached_payload

        async with self._cache_lock:
            if settings.cache_ttl_seconds > 0 and self._cached_payload is not None:
                if (time.monotonic() - self._cached_at_monotonic) < settings.cache_ttl_seconds:
                    return self._cached_payload

            payload = await self._compute_once()
            if settings.cache_ttl_seconds > 0:
                self._cached_payload = payload
                self._cached_at_monotonic = time.monotonic()
            return payload

    async def _compute_once(self) -> GasComparisonResponse:
        sample = settings.block_sample_size

        near_gas_price_yocto = await self.provider.near_gas_price_yocto()
        near_transfer_gas_units = await self.provider.near_transfer_gas_units()
        near_speed_s = await self.provider.near_avg_block_time_seconds(sample)

        eth_gas_price_wei = await self.provider.eth_gas_price_wei()
        eth_transfer_gas_units = 21_000
        eth_speed_s = await self.provider.eth_avg_block_time_seconds(sample)

        prices = await self.provider.prices_usd()

        near_cost_native = (near_gas_price_yocto * near_transfer_gas_units) / 1e24
        eth_cost_native = (eth_gas_price_wei * eth_transfer_gas_units) / 1e18

        near_cost_usd = near_cost_native * prices["near"]
        eth_cost_usd = eth_cost_native * prices["ethereum"]

        cheaper_usd = max(0.0, eth_cost_usd - near_cost_usd)
        cheaper_pct = 0.0 if eth_cost_usd <= 0 else (cheaper_usd / eth_cost_usd) * 100
        ratio = float("inf") if near_cost_usd <= 0 else eth_cost_usd / near_cost_usd

        near = ChainGasSnapshot(
            chain="near",
            cost_native=round(near_cost_native, 12),
            cost_usd=round(near_cost_usd, 6),
            speed=f"{near_speed_s:.2f}s",
            speed_seconds=round(near_speed_s, 4),
            gas_price=f"{near_gas_price_yocto} yoctoNEAR/gas",
            transfer_gas_units=near_transfer_gas_units,
        )

        ethereum = ChainGasSnapshot(
            chain="ethereum",
            cost_native=round(eth_cost_native, 12),
            cost_usd=round(eth_cost_usd, 6),
            speed=f"{eth_speed_s:.2f}s",
            speed_seconds=round(eth_speed_s, 4),
            gas_price=f"{eth_gas_price_wei} wei/gas",
            transfer_gas_units=eth_transfer_gas_units,
        )

        summary = ComparisonSummary(
            near_is_cheaper_by_usd=round(cheaper_usd, 6),
            near_is_cheaper_by_percent=round(cheaper_pct, 2),
            cost_ratio_eth_over_near=(round(ratio, 2) if ratio != float("inf") else 9_999_999.0),
        )

        return GasComparisonResponse(
            generated_at=datetime.now(timezone.utc).isoformat(),
            near=near,
            ethereum=ethereum,
            summary=summary,
            methodology={
                "near_cost": "Calculated from NEAR protocol transfer fee components and current gas_price RPC.",
                "ethereum_cost": "Calculated as 21000 gas * current eth_gasPrice.",
                "speed": f"Average block time over latest {sample} blocks.",
                "prices": "CoinGecko near/usd and ethereum/usd spot prices.",
            },
        )
