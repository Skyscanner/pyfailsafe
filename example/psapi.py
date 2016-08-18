import aiohttp
from failsafe import Failsafe, RetryPolicy, CircuitBreaker, RetriesExhausted, CircuitOpen


class PsaAPI:
    def __init__(self):
        self.path = "/v1/relevance/partner/{0}/market/{1}/device/{2}/hotel/{3}"
        self.endpoint_main = "http://hbe-psa.eu-west-1.prod.aws.skyscanner.local"
        self.endpoint_secondary = "http://hbe-psa.eu-central-1.prod.aws.skyscanner.local"

        policy = RetryPolicy(retries=4)

        circuit_breaker = CircuitBreaker(maximum_failures=2)
        self.failsafe = Failsafe(retry_policy=policy, circuit_breaker=circuit_breaker)

        circuit_breaker_backup = CircuitBreaker(maximum_failures=2)
        self.failsafe_backup = Failsafe(retry_policy=policy, circuit_breaker=circuit_breaker_backup)

    async def get_deal(self, partner, market, device, hotel_id):
        url = self.endpoint_main + self.path.format(partner, market, device, hotel_id)
        try:
            return await self.failsafe.run(lambda: self._request(url))
        except (RetriesExhausted, CircuitOpen):
            url = self.endpoint_secondary + self.path.format(partner, market, device, hotel_id)
            return await self.failsafe_backup.run(lambda: self._request(url))

    async def _request(self, url):
        with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise Exception()
                return await resp.json()

if __name__ == "__main__":

    async def print_response():
        from pprint import pprint
        psa = PsaAPI()
        result = await psa.get_deal('h_bc', 'ES', 'DESKTOP', 47088622)
        pprint(result)

    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(print_response())
    loop.close()
