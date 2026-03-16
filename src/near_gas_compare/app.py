from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .config import settings
from .models import GasComparisonResponse
from .providers import ProviderError
from .service import GasComparisonService


def create_app() -> FastAPI:
    app = FastAPI(
        title="NEAR Gas Comparison API",
        version="0.1.0",
        description="Real-time NEAR vs Ethereum gas cost comparison API",
    )

    service = GasComparisonService()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name, "env": settings.app_env}

    @app.get("/api/gas/compare", response_model=GasComparisonResponse)
    async def gas_compare() -> GasComparisonResponse:
        try:
            return await service.compare()
        except ProviderError as exc:
            raise HTTPException(status_code=502, detail={"error": str(exc)}) from exc

    return app
