# API Directory Submission Pack

This package contains all metadata needed to list the API in public API directories.

## API

- Name: NEAR Gas Comparison API
- Base URL (self-host): `https://<your-host>`
- Main endpoint: `GET /api/gas/compare`
- Compact endpoint: `GET /api/gas/compare/simple`
- Health endpoint: `GET /health`
- OpenAPI spec: `GET /openapi.json`

## Description

Real-time API for comparing transfer gas costs between NEAR and Ethereum using live on-chain fee data and live USD price data.

## Value Proposition

- Shows cost gap between NEAR and Ethereum in USD
- Includes chain speed metric (avg block time)
- Uses multiple RPC providers with fallback
- Supports stale-cache serving to improve uptime

## Auth

No auth required by default (self-hosted). You can add API key auth in a gateway/proxy layer.

## Pricing

Free/self-hosted reference implementation.

## Source Repository

- GitHub: https://github.com/mastrophot/near-gas-comparison-api

## Example Response (`/api/gas/compare/simple`)

```json
{
  "near": { "cost_usd": 0.0012, "speed": "1.2s" },
  "ethereum": { "cost_usd": 0.56, "speed": "12.3s" }
}
```
