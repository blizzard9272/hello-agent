# Engineer 的输出

## 第 1 轮

好的，收到产品经理的需求分析和技术方案。我是负责开发的软件工程师，现在开始实现。

我将按照确定的优先级，一步步构建这个比特币价格显示应用。

首先，我会从 **P0 核心功能** 开始，确保基本的API调用、数据显示和刷新功能跑通。然后逐步迭代优化。

以下是初始版本的代码实现：

```python
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
```

---

**代码审查员请检查。**

以上代码完成了 **P0 核心功能**：
1.  ✅ 调用 CoinGecko API 获取数据
2.  ✅ 使用 `st.metric` 展示价格和涨跌
3.  ✅ 刷新按钮功能
4.  ✅ 基本的网络错误处理（显示错误信息，但UI还有改进空间）

**接下来计划进行 P1 和 P2 的优化**：

*   **P1改进**:
    *   **锁定刷新按钮**: 数据加载时禁用按钮（使用 `st.button` 的 `disabled` 参数或用 `session_state` 控制）。
    *   **更优雅的加载状态**: 当前 `st.spinner` 已经基本满足，可以增加加载时的进度条动画或更明确的文字提示。
    *   **UI美化**: 使用 `st.columns` 来更精细地布局，添加一些 CSS 来美化价格卡片。

*   **P2改进**:
    *   **数据缓存**: 使用 `@st.cache_data(ttl=10)` 缓存API结果，减少请求频率。
    *   **显示最新数据时间**: 目前已经显示，但可以更精确（如：几秒前）。
    *   **优雅降级**: 错误状态下，`display_price_card` 已经可以 `return` 避免崩溃，但后续可以改进为保留上次成功的数据。

**请注意**，当前代码在初次加载时可能会有一个短暂的空白等待，这是 Streamlit 的工作机制（`st.rerun()` 会重新执行整个脚本）。在后续版本中，我会优化这个首次加载体验。

请继续审查。

---

