from __future__ import annotations

from typing import Optional

import httpx

from src.config.settings import OPEN_METEO_GEOCODING_URL
from src.models import GeocodingResult


class GeolocationService:
    async def search(self, query: str, count: int = 5) -> list[GeocodingResult]:
        params = {"name": query, "count": count, "language": "pl", "format": "json"}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    OPEN_METEO_GEOCODING_URL, params=params, timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPError as exc:
                raise ConnectionError(f"Geocoding API error: {exc}") from exc

        results = data.get("results", []) if data else []
        return [
            GeocodingResult(
                name=(
                    f"{r.get('name', '')}, {r.get('admin1', '')}, {r.get('country', '')}"
                ),
                latitude=r.get("latitude", 0.0),
                longitude=r.get("longitude", 0.0),
                timezone=r.get("timezone", "UTC"),
                country=r.get("country", ""),
                admin1=r.get("admin1", ""),
            )
            for r in results
        ]
