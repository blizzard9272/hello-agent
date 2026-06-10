# config.py
# 集中管理所有配置常量

# CoinGecko API 配置
# 免费 API，无需 key，但有速率限制 (10-30 calls/min)
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
COINGECKO_SIMPLE_PRICE_ENDPOINT = f"{COINGECKO_BASE_URL}/simple/price"

# 查询参数
COIN_ID = "bitcoin"
VS_CURRENCY = "usd"

# 完整的 API URL（包含查询参数）
API_URL = f"{COINGECKO_SIMPLE_PRICE_ENDPOINT}?ids={COIN_ID}&vs_currencies={VS_CURRENCY}&include_24hr_change=true"
