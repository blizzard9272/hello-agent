if not all(isinstance(val, (int, float)) for val in [usd_price, usd_24h_change, usd_24h_change_percentage]):
            raise ValueError("API 返回的数量格式异常")
