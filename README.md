# near-gas-comparison-api

FastAPI service that provides real-time gas cost comparison between **NEAR** and **Ethereum**.

## Endpoint

- `GET /api/gas/compare`
- `GET /api/gas/compare/simple` (compact response for quick integration)
- In-memory cache (30s default) to reduce upstream RPC load
- Stale-cache fallback if upstream RPCs are temporarily unavailable

Example response:

```json
{
  "near": { "cost_usd": 0.0012, "speed": "1.2s" },
  "ethereum": { "cost_usd": 0.56, "speed": "12.3s" }
}
```

Simple format:

```json
{
  "near": { "cost_usd": 0.0012, "speed": "1.2s" },
  "ethereum": { "cost_usd": 0.56, "speed": "12.3s" }
}
```


## API Directory Pack

Included in `docs/` for faster listing submission:

- `docs/api-directory-submission-pack.md`
- `docs/postman_collection.json`

## Data Sources

- NEAR RPC (with fallback): `rpc.mainnet.near.org`, `free.rpc.fastnear.com`
- Ethereum RPC (with fallback): `ethereum-rpc.publicnode.com`, `eth.llamarpc.com`, `1rpc.io/eth`
- RPC methods: `gas_price`, `EXPERIMENTAL_protocol_config`, `block`, `eth_gasPrice`, `eth_blockNumber`, `eth_getBlockByNumber`
- USD prices: CoinGecko (`near`, `ethereum`)

## Cost Methodology

- NEAR transfer cost is computed from protocol config fee components:
  - action receipt creation (send + execution)
  - transfer action (send + execution)
- Ethereum transfer baseline uses 21,000 gas at current `eth_gasPrice`.
- Block speed is sampled from the latest 100 blocks.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
near-gas-compare-api --host 0.0.0.0 --port 8080
```

Docs:

- Swagger: `http://localhost:8080/docs`
- OpenAPI: `http://localhost:8080/openapi.json`

## Test

```bash
pytest -q
```

## License

MIT
