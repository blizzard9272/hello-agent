price = bitcoin_data.get("usd")
    change_24h = bitcoin_data.get("usd_24h_change", 0.0)
    change_percentage = bitcoin_data.get("usd_24h_change_percentage", 0.0)
    
    # 在 display_price_card 中对数据进行校验
    if price is None or not isinstance(price, (int, float)):
        st.error("获取到的价格数据无效")
        return
