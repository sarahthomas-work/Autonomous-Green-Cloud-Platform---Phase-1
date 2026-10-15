import httpx


class PrometheusService:
    """
    Client for communicating with the Prometheus HTTP API.
    """

    def __init__(self, base_url: str = "http://localhost:9090"):
        self.base_url = base_url.rstrip("/")

    async def query(self, promql: str):
        """
        Execute an instant PromQL query against Prometheus.
        """

        url = f"{self.base_url}/api/v1/query"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                url,
                params={"query": promql},
            )

        response.raise_for_status()

        return response.json()

    async def query_value(self, promql: str):
        """
        Execute a PromQL query and return the first numeric result.
        """

        data = await self.query(promql)

        results = data.get("data", {}).get("result", [])

        if not results:
            return None

        value = results[0].get("value")

        if not value or len(value) < 2:
            return None

        return float(value[1])


prometheus_service = PrometheusService()