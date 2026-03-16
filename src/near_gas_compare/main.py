from __future__ import annotations

import argparse

import uvicorn


def cli() -> None:
    parser = argparse.ArgumentParser(description="Run NEAR Gas Comparison API service")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    uvicorn.run("near_gas_compare.app:create_app", host=args.host, port=args.port, reload=args.reload, factory=True)


if __name__ == "__main__":
    cli()
