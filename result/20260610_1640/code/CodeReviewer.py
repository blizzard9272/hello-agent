if "usd" not in bitcoin_data or "usd_24h_change" not in bitcoin_data:
        st.error("API返回数据格式异常")
        return None
