from __future__ import annotations

from typing import Any, Dict

import httpx

from .config import settings


class ProviderError(RuntimeError):
    pass


class DataProvider:
    def __init__(self, *, timeout_seconds: float | None = None):
        self.timeout_seconds = timeout_seconds or settings.request_timeout_seconds

    @staticmethod
    def _parse_urls(raw: str) -> list[str]:
        return [x.strip() for x in raw.split(",") if x.strip()]

    async def _post_json(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    async def _post_json_fallback(self, urls: list[str], payload: dict[str, Any]) -> dict[str, Any]:
        errors: list[str] = []
        for url in urls:
            try:
                data = await self._post_json(url, payload)
                if "error" in data:
                    errors.append(f"{url}: {data['error']}")
                    continue
                return data
            except (httpx.HTTPError, ValueError) as exc:
                errors.append(f"{url}: {exc}")
        raise ProviderError("RPC fallback exhausted: " + " | ".join(errors))

    async def _get_json(self, url: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def near_gas_price_yocto(self) -> int:
        data = await self._post_json_fallback(
            self._parse_urls(settings.near_mainnet_rpc_urls),
            {"jsonrpc": "2.0", "id": "near-gas-compare", "method": "gas_price", "params": [None]},
        )
        return int(data["result"]["gas_price"])

    async def near_transfer_gas_units(self) -> int:
        data = await self._post_json_fallback(
            self._parse_urls(settings.near_mainnet_rpc_urls),
            {
                "jsonrpc": "2.0",
                "id": "near-gas-compare",
                "method": "EXPERIMENTAL_protocol_config",
                "params": {"finality": "final"},
            },
        )
        tx_cfg = data["result"]["runtime_config"]["transaction_costs"]
        arc = tx_cfg["action_receipt_creation_config"]
        trf = tx_cfg["action_creation_config"]["transfer_cost"]

        # Simple transfer total fee components (gas units):
        # action receipt creation (send + execution) + transfer action (send + execution)
        return int(arc["send_not_sir"]) + int(arc["execution"]) + int(trf["send_not_sir"]) + int(trf["execution"])

    async def near_avg_block_time_seconds(self, sample_size: int) -> float:
        near_urls = self._parse_urls(settings.near_mainnet_rpc_urls)
        latest = await self._post_json_fallback(
            near_urls,
            {"jsonrpc": "2.0", "id": "near-gas-compare", "method": "block", "params": {"finality": "final"}},
        )
        latest_h = int(latest["result"]["header"]["height"])
        latest_ts_ns = int(latest["result"]["header"]["timestamp_nanosec"])

        prev_h = max(0, latest_h - sample_size)
        prev = await self._post_json_fallback(
            near_urls,
            {"jsonrpc": "2.0", "id": "near-gas-compare", "method": "block", "params": {"block_id": prev_h}},
        )
        prev_ts_ns = int(prev["result"]["header"]["timestamp_nanosec"])
        delta_blocks = max(1, latest_h - prev_h)
        return (latest_ts_ns - prev_ts_ns) / 1_000_000_000 / delta_blocks

    async def eth_gas_price_wei(self) -> int:
        data = await self._post_json_fallback(
            self._parse_urls(settings.eth_mainnet_rpc_urls),
            {"jsonrpc": "2.0", "id": 1, "method": "eth_gasPrice", "params": []},
        )
        return int(data["result"], 16)

    async def eth_avg_block_time_seconds(self, sample_size: int) -> float:
        eth_urls = self._parse_urls(settings.eth_mainnet_rpc_urls)
        bn = await self._post_json_fallback(
            eth_urls,
            {"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []},
        )
        latest_h = int(bn["result"], 16)
        prev_h = max(0, latest_h - sample_size)

        latest_block = await self._post_json_fallback(
            eth_urls,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_getBlockByNumber",
                "params": [hex(latest_h), False],
            },
        )
        prev_block = await self._post_json_fallback(
            eth_urls,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_getBlockByNumber",
                "params": [hex(prev_h), False],
            },
        )

        latest_ts = int(latest_block["result"]["timestamp"], 16)
        prev_ts = int(prev_block["result"]["timestamp"], 16)
        delta_blocks = max(1, latest_h - prev_h)
        return (latest_ts - prev_ts) / delta_blocks

    async def prices_usd(self) -> Dict[str, float]:
        data = await self._get_json(settings.coingecko_price_url)
        try:
            return {
                "near": float(data["near"]["usd"]),
                "ethereum": float(data["ethereum"]["usd"]),
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderError("Invalid price response payload") from exc
