import aiohttp

BASE_URL = "https://api.earthmc.net/v4/"

async def post_request(session: aiohttp.ClientSession, category: str, data: list[str]):
    async with session.post(f"{BASE_URL}{category}", json={"query": data}) as response:
        return await response.json()

async def get_request(session: aiohttp.ClientSession, category: str):
    async with session.get(f"{BASE_URL}{category}") as response:
        return await response.json()

async def position_request(session: aiohttp.ClientSession):
    async with session.get('https://map.earthmc.net/tiles/players.json') as response:
        return await response.json()