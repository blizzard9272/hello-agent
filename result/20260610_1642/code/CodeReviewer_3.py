if usd_price is None or not isinstance(usd_price, (int, float)):
            raise KeyError("'usd' 字段缺失或格式异常")
        if usd_24h_change is None or not isinstance(usd_24h_change, (int, float)):
            raise KeyError("'usd_24h_change' 字段缺失或格式异常")
        if usd_24h_change_percentage is None or not isinstance(usd_24h_change_percentage, (int, float)):
            raise KeyError("'usd_24h_change_percentage' 字段缺失或格式异常")
