# app.py

import streamlit as st
import requests
from datetime import datetime
import time

# 配置页面
st.set_page_config(
    page_title="比特币价格监控",
    page_icon="₿",
    layout="centered"
)

# --- 数据获取函数 (P0) ---
def fetch_bitcoin_data():
    """
    从 CoinGecko API 获取比特币当前价格和24小时变化。
    返回: dict {'price': float, 'change_24h': float, 'change_percentage_24h': float}
           如果失败返回 None
    """
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # 检查请求是否成功 (状态码 200-399)
        
        data = response.json()
        bitcoin_data = data.get("bitcoin", {})
        
        # 检查返回数据的完整性
        if "usd" not in bitcoin_data or "usd_24h_change" not in bitcoin_data:
            st.error("API返回数据格式异常")
            return None
        
        return {
            "price": bitcoin_data["usd"],
            "change_24h": bitcoin_data["usd_24h_change"],
            "change_percentage_24h": bitcoin_data["usd_24h_change_percentage"]
        }
        
    except requests.exceptions.RequestException as e:
        st.error(f"网络请求失败: {e}")
        return None
    except ValueError as e:
        st.error(f"数据解析错误: {e}")
        return None
    except Exception as e:
        st.error(f"未知错误: {e}")
        return None

# --- 界面展示函数 (P0) ---
def display_price_card(bitcoin_data):
    """
    使用 Streamlit 的 st.metric 组件展示比特币价格卡片。
    """
    if bitcoin_data is None:
        st.warning("暂无数据")
        return

    # 提取数据
    price = bitcoin_data["price"]
    change_24h = bitcoin_data["change_24h"]
    change_percentage = bitcoin_data["change_percentage_24h"]
    
    # 使用 st.metric 展示主要指标
    # delta 为正时显示绿色，负时显示红色
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="比特币 (BTC) / USD",
            value=f"${price:,.2f}",
            delta=f"{change_24h:+.2f} ({change_percentage:+.2f}%)",
            delta_color="normal"  # 自动根据正负显示颜色
        )
    
    # 显示数据更新时间
    with col3:
        current_time = datetime.now().strftime("%H:%M:%S")
        st.caption(f"数据更新于: {current_time}")

# --- 主程序逻辑 (P0) ---
def main():
    # 页面标题
    st.title("₿ 比特币实时价格监控")
    
    # 初始化 session_state 存储数据 (用于错误时保留上次数据)
    if "bitcoin_data" not in st.session_state:
        st.session_state.bitcoin_data = None
    
    # 刷新按钮 (P0)
    if st.button("🔄 刷新价格", type="primary"):
        with st.spinner("正在更新数据..."):
            new_data = fetch_bitcoin_data()
            if new_data:
                st.session_state.bitcoin_data = new_data
            # 如果获取失败，保留旧数据
        # 强制重新运行以更新界面 (Streamlit 机制)
        st.rerun()

    # 如果 session_state 中有数据，则显示；否则首次加载
    if st.session_state.bitcoin_data is not None:
        display_price_card(st.session_state.bitcoin_data)
    else:
        # 初次加载自动获取数据
        with st.spinner("首次加载，请稍候..."):
            initial_data = fetch_bitcoin_data()
            if initial_data:
                st.session_state.bitcoin_data = initial_data
                st.rerun()  # 重新运行以显示数据
    
    # 页脚信息
    st.divider()
    st.markdown("**数据来源**: [CoinGecko API](https://www.coingecko.com/en/api)")
    st.markdown("**注意事项**: 价格数据存在约30秒的延迟，仅供参考。")

if __name__ == "__main__":
    main()
