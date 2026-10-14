import httpx

response = httpx.post("https://api.earthmc.net/v4/players", json={'query': '2c6849de-85ac-4f9f-aaab-eb2c8396cf7e'})
print(response.status_code)