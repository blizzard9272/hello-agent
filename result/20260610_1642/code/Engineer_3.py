# app.py
import streamlit as st
import time
from datetime import datetime

# 引入数据服务
from services.price_service import price_service
from config import COIN_ID, VS_CURRENCY

# --- 页面配置 ---
st.set_page_config(
    page_title="比特币价格监测器",
    page_icon="₿",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 自定义 CSS 样式 (可选，用于美化) ---
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #f39c12;
        font-size: 2.5em;
        margin-bottom: 0.5em;
    }
    .price-display {
        font-size: 3em;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0.5em;
    }
    .change-positive {
        color: #00ff00;
    }
    .change-negative {
        color: #ff0000;
    }
    .metric-container {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .info-text {
        text-align: center;
        color: #888;
        font-size: 0.8em;
    }
</style>
""", unsafe_allow_html=True)

# --- 标题 ---
st.markdown("<h1 class='main-title'>₿ 比特币价格监测器 ₿</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- 初始化 session_state ---
# 用于存储价格数据、加载状态、错误信息和上次更新时间
if 'price_data' not in st.session_state:
    st.session_state.price_data = None
if 'loading' not in st.session_state:
    st.session_state.loading = False
if 'error_message' not in st.session_state:
    st.session_state.error_message = None
if 'last_updated' not in st.session_state:
    st.session_state.last_updated = None

# --- 定义数据获取函数 ---
def fetch_and_update_data():
    """
    从数据服务获取最新价格数据，并更新 session_state。
    处理加载状态和错误状态。
    """
    st.session_state.loading = True
    st.session_state.error_message = None  # 清除之前的错误
    
    try:
        # 调用服务获取数据
        data = price_service.fetch_bitcoin_data()  # 使用 fetch_bitcoin_data 确保获取最新数据
        st.session_state.price_data = data
        st.session_state.last_updated = datetime.now()
        st.session_state.error_message = None
        
    except Exception as e:
        # 捕获所有异常，设置为错误消息
        st.session_state.error_message = str(e)
        # 如果之前有缓存数据，保留它，以便 UI 仍然可以展示
        if price_service.last_successful_data:
            st.session_state.price_data = price_service.last_successful_data
            st.session_state.last_updated = datetime.now()  # 更新时间为最后成功加载的时间？这里保持不更新更合理
            # 最好保留上次成功加载的时间
    finally:
        st.session_state.loading = False

# --- 页面逻辑 ---

# 1. 显示价格变化卡片
price_container = st.container()

with price_container:
    # 创建一个三列布局，用于显示价格和变化数据
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("#### 当前价格")
        if st.session_state.price_data:
            usd_price = st.session_state.price_data.get('usd', 0)
            # 格式化价格，保留两位小数
            price_formatted = f"${usd_price:,.2f}"
            st.markdown(f"<p class='price-display'>{price_formatted}</p>", unsafe_allow_html=True)
            st.write(f"币种: 比特币 (BTC)")  # 显示币种信息
            st.write(f"计价货币: {VS_CURRENCY.upper()}")
        else:
            st.markdown("<p class='price-display'>---</p>", unsafe_allow_html=True)
            if st.session_state.error_message:
                st.info("🔄 点击刷新按钮获取价格")
            else:
                st.info("⏳ 等待首次加载...")

    # 显示24h涨跌额
    with col2:
        st.markdown("#### 24小时变化")
        if st.session_state.price_data:
            change_24h = st.session_state.price_data.get('usd_24h_change', 0)
            change_percentage = st.session_state.price_data.get('usd_24h_change_percentage', 0)
            
            # 格式化变化额
            change_formatted = f"${change_24h:+.2f}"
            percentage_formatted = f"{change_percentage:+.2f}%"
            
            # 根据涨跌选择颜色和符号
            if change_24h >= 0:
                arrow = "▲"
                color_class = "change-positive"
            else:
                arrow = "▼"
                color_class = "change-negative"
            
            # 使用 unsafe_allow_html=True 来应用自定义CSS
            st.markdown(f"<p class='{color_class}' style='font-size:1.5em; font-weight:bold;'>{arrow} {change_formatted}</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='{color_class}' style='font-size:1.2em;'>{arrow} {percentage_formatted}</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='font-size:1.5em;'>---</p>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:1.2em;'>---</p>", unsafe_allow_html=True)

    # 显示加载状态和信息
    with col3:
        st.markdown("#### 状态信息")
        if st.session_state.loading:
            st.info("🔄 正在加载...")
        elif st.session_state.error_message:
            st.error(f"⚠️ {st.session_state.error_message}")
            if st.session_state.price_data:
                st.warning("📦 显示的是上次缓存的数据")
        else:
            if st.session_state.last_updated:
                st.success(f"✅ 数据正常")
                last_time = st.session_state.last_updated.strftime("%H:%M:%S")
                st.write(f"上次更新: {last_time}")
            else:
                st.info("⏳ 等待首次加载...")

# 2. 刷新按钮和自动刷新选项
st.markdown("---")
col_refresh, col_auto = st.columns([1, 1])

with col_refresh:
    # 刷新按钮，点击时触发数据获取
    if st.button("🔄 刷新价格", use_container_width=True):
        fetch_and_update_data()
        st.rerun()  # 立即重运行以更新UI

with col_auto:
    # 自动刷新选项（定时器）
    auto_refresh = st.checkbox("🕒 自动刷新 (每60秒)", value=True)  # 默认启用自动刷新
    
    if auto_refresh:
        # 使用 st.empty 占位，并配合定时器
        placeholder = st.empty()
        # 每秒更新一次计时，每60秒触发一次数据获取
        if 'refresh_counter' not in st.session_state:
            st.session_state.refresh_counter = 0
        
        st.session_state.refresh_counter += 1
        
        # 强制 UI 每秒更新以显示计时器
        time.sleep(0.5)
        
        if st.session_state.refresh_counter >= 120:  # 60秒 * 2 (因为sleep 0.5s)
            st.session_state.refresh_counter = 0
            # 触发数据更新
            fetch_and_update_data()
            st.rerun()
        
        # 显示下次刷新倒计时
        remaining = 60 - (st.session_state.refresh_counter // 2)  # 转换为秒
        placeholder.write(f"下次自动刷新: {remaining}秒")

# 3. 其他信息（例如数据来源、温馨提示）
st.markdown("---")
st.caption(f"📊 数据来源: CoinGecko 免费公开 API | 更新时间: 实时 (按需刷新)")
st.caption("🔒 本应用仅作信息展示，不构成任何投资建议。")

# --- 首次加载逻辑 ---
# 如果 session_state 中还没有数据且没有错误信息，则自动触发一次数据获取
if st.session_state.price_data is None and st.session_state.error_message is None:
    with st.spinner("⏳ 正在获取最新价格数据..."):
        fetch_and_update_data()
    st.rerun()  # 获取数据后重运行，显示UI
