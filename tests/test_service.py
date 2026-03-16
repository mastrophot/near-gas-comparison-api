from __future__ import annotations

import pytest

from near_gas_compare.config import settings
from near_gas_compare.providers import ProviderError
from near_gas_compare.service import GasComparisonService


class FakeProvider:
    def __init__(self):
        self.fail = False

    async def near_gas_price_yocto(self) -> int:
        if self.fail:
            raise ProviderError("near rpc down")
        return 100_000_000

    async def near_transfer_gas_units(self) -> int:
        return 600

    async def near_avg_block_time_seconds(self, sample_size: int) -> float:
        return 1.0

    async def eth_gas_price_wei(self) -> int:
        return 1_000_000_000

    async def eth_avg_block_time_seconds(self, sample_size: int) -> float:
        return 12.0

    async def prices_usd(self) -> dict[str, float]:
        return {"near": 3.0, "ethereum": 3000.0}


@pytest.mark.asyncio
async def test_stale_cache_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = FakeProvider()
    service = GasComparisonService(provider=provider)

    monkeypatch.setattr(settings, "cache_ttl_seconds", 1)

    fresh = await service.compare()
    assert fresh.is_stale is False

    service._cached_at_monotonic -= 10
    provider.fail = True

    stale = await service.compare()
    assert stale.is_stale is True
    assert stale.stale_reason is not None
    assert stale.near.cost_usd == fresh.near.cost_usd
