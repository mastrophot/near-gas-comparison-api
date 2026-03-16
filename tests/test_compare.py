from __future__ import annotations

import respx
from fastapi.testclient import TestClient
from httpx import Response

from near_gas_compare.app import create_app


@respx.mock
def test_gas_compare_success() -> None:
    near_rpc = "https://rpc.mainnet.near.org"
    eth_rpc = "https://ethereum-rpc.publicnode.com"
    prices_url = "https://api.coingecko.com/api/v3/simple/price?ids=near,ethereum&vs_currencies=usd"

    # NEAR RPC sequence
    near_gas_price_route = respx.post(near_rpc, json__method="gas_price").mock(
        return_value=Response(200, json={"jsonrpc": "2.0", "result": {"gas_price": "100000000"}, "id": "x"})
    )
    respx.post(near_rpc, json__method="EXPERIMENTAL_protocol_config").mock(
        return_value=Response(
            200,
            json={
                "jsonrpc": "2.0",
                "result": {
                    "runtime_config": {
                        "transaction_costs": {
                            "action_receipt_creation_config": {
                                "send_not_sir": 100,
                                "execution": 100,
                            },
                            "action_creation_config": {
                                "transfer_cost": {
                                    "send_not_sir": 200,
                                    "execution": 200,
                                }
                            },
                        }
                    }
                },
                "id": "x",
            },
        )
    )
    respx.post(near_rpc, json__method="block", json__params={"finality": "final"}).mock(
        return_value=Response(
            200,
            json={
                "jsonrpc": "2.0",
                "result": {"header": {"height": 1000, "timestamp_nanosec": "200000000000"}},
                "id": "x",
            },
        )
    )
    respx.post(near_rpc, json__method="block", json__params={"block_id": 900}).mock(
        return_value=Response(
            200,
            json={
                "jsonrpc": "2.0",
                "result": {"header": {"height": 900, "timestamp_nanosec": "100000000000"}},
                "id": "x",
            },
        )
    )

    # ETH RPC sequence
    respx.post(eth_rpc, json__method="eth_gasPrice").mock(
        return_value=Response(200, json={"jsonrpc": "2.0", "result": "0x3b9aca00", "id": 1})
    )
    respx.post(eth_rpc, json__method="eth_blockNumber").mock(
        return_value=Response(200, json={"jsonrpc": "2.0", "result": "0x3e8", "id": 1})
    )
    respx.post(eth_rpc, json__method="eth_getBlockByNumber", json__params=["0x3e8", False]).mock(
        return_value=Response(200, json={"jsonrpc": "2.0", "result": {"timestamp": "0xc8"}, "id": 1})
    )
    respx.post(eth_rpc, json__method="eth_getBlockByNumber", json__params=["0x384", False]).mock(
        return_value=Response(200, json={"jsonrpc": "2.0", "result": {"timestamp": "0x64"}, "id": 1})
    )

    # prices
    prices_route = respx.get(prices_url).mock(
        return_value=Response(200, json={"near": {"usd": 3.0}, "ethereum": {"usd": 3000.0}})
    )

    client = TestClient(create_app())
    response = client.get("/api/gas/compare")

    assert response.status_code == 200
    data = response.json()
    assert data["near"]["chain"] == "near"
    assert data["ethereum"]["chain"] == "ethereum"
    assert data["near"]["cost_usd"] < data["ethereum"]["cost_usd"]
    assert "methodology" in data
    assert "sources" in data
    assert data["is_stale"] is False
    assert data["stale_reason"] is None

    # Cached response (default 30s) should avoid repeated upstream calls.
    second = client.get("/api/gas/compare")
    assert second.status_code == 200
    assert near_gas_price_route.call_count == 1
    assert prices_route.call_count == 1

    # Compact endpoint should preserve the requested minimal shape.
    compact = client.get("/api/gas/compare/simple")
    assert compact.status_code == 200
    compact_data = compact.json()
    assert set(compact_data.keys()) == {"near", "ethereum"}
    assert "cost_usd" in compact_data["near"]
    assert "speed" in compact_data["near"]
