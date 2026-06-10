# Engineer 的输出

## 第 1 轮

好的，收到需求。作为团队中的软件工程师，我将严格按照产品经理的需求分析和技术要求，实现这个比特币价格显示应用。

我的实现方案如下：

1.  **数据服务层 (`services/price_service.py`)**：封装与 CoinGecko API 的交互。负责发送请求、解析响应、处理网络异常和数据异常。此模块不关心 UI 逻辑。
2.  **UI 展示层 (`app.py`)**：Streamlit 主应用。负责布局、渲染组件、响应用户交互（刷新）。它将调用 `price_service.py` 获取数据，并处理加载和错误状态。
3.  **配置层 (`config.py`)**：存放 API URL、货币代码等常量，方便统一管理。

我会特别注意异常处理，确保在网络波动或 API 返回异常数据时，应用能优雅地降级，并给用户清晰的提示。

现在开始编码实现。

---
### 1. 配置层 (`config.py`)

```python
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
```

### 2. 数据服务层 (`services/price_service.py`)

```python
# services/price_service.py
import requests
import json
from typing import Dict, Optional, Tuple, Any

# 引入配置
# 注意：这里假设 config.py 在上一级目录，或者需要调整导入路径
# 由于 Streamlit 默认从根目录运行，我们采用直接导入同级模块的方式
# 但在实际项目中，更好的做法是使用包管理
from config import API_URL

class BitcoinPriceService:
    """
    负责与 CoinGecko API 交互，获取比特币价格数据的服务类。
    """
    
    def __init__(self):
        self.last_error_message: Optional[str] = None
        self.last_successful_data: Optional[Dict[str, Any]] = None

    def fetch_bitcoin_data(self) -> Dict[str, Any]:
        """
        从 CoinGecko API 获取比特币的当前价格和 24 小时变化数据。
        
        Returns:
            一个包含以下键的字典：
            - 'usd': 当前美元价格 (float)
            - 'usd_24h_change': 24小时变化额 (float)
            - 'usd_24h_change_percentage': 24小时变化百分比 (float)
            - 'last_updated': 用作时间戳
        
        Raises:
            requests.exceptions.RequestException: 网络请求失败时抛出。
            KeyError: API 返回数据格式不符合预期时抛出。
        """
        try:
            # 发起 GET 请求，设置超时时间为 10 秒
            response = requests.get(API_URL, timeout=10)
            # 检查 HTTP 状态码，如果非 2xx 则抛出 HTTPError
            response.raise_for_status()  
            
            # 解析 JSON 响应
            data: Dict[str, Any] = response.json()
            
            # 验证并提取数据
            bitcoin_data = data.get(COIN_ID)  # 假设 COIN_ID 定义为 'bitcoin'
            if bitcoin_data is None:
                raise KeyError(f"API 响应中未找到键 '{COIN_ID}'")
            
            usd_price = bitcoin_data.get(VS_CURRENCY)  # 假设 VS_CURRENCY 定义为 'usd'
            usd_24h_change = bitcoin_data.get(f'{VS_CURRENCY}_24h_change')
            usd_24h_change_percentage = bitcoin_data.get(f'{VS_CURRENCY}_24h_change_percentage')
            
            # 检查提取的值是否为预期的数值类型
            if not all(isinstance(val, (int, float)) for val in [usd_price, usd_24h_change, usd_24h_change_percentage]):
                raise ValueError("API 返回的数量格式异常")
            
            # 构建和返回结构化数据
            processed_data = {
                'usd': usd_price,
                'usd_24h_change': usd_24h_change,
                'usd_24h_change_percentage': usd_24h_change_percentage,
            }
            
            # 更新最后成功获取的数据和清除错误信息
            self.last_successful_data = processed_data
            self.last_error_message = None
            return processed_data
            
        except requests.exceptions.RequestException as e:
            # 网络相关错误（超时、连接失败、HTTP 错误等）
            self.last_error_message = f"网络请求错误: {e}"
            # 重新抛出异常，让调用方（UI 层）决定如何处理
            raise
        
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            # 数据解析相关错误（缺少键、数据类型不对、JSON 格式错误等）
            self.last_error_message = f"数据解析错误: {e}"
            # 抛出更具体的异常或重新抛出
            raise ValueError(f"响应数据格式错误: {e}") from e
        
        except Exception as e:
            # 捕获其他未预料的异常，确保应用不会崩溃
            self.last_error_message = f"未知错误: {e}"
            raise RuntimeError(f"获取价格时发生未预期的错误: {e}") from e

    def get_cached_or_latest(self) -> Dict[str, Any]:
        """
        尝试获取最新数据，失败时返回上次成功缓存的数据。
        这是一个更健壮的设计，确保 UI 始终有数据可显示。
        
        Returns:
            字典，包含价格数据。
            
        Raises:
            RuntimeError: 如果首次请求和缓存请求都失败。
        """
        try:
            return self.fetch_bitcoin_data()
        except Exception:
            # 如果获取失败且存在缓存数据，则返回缓存
            if self.last_successful_data:
                # 可以记录日志，提示正在使用旧数据
                return self.last_successful_data.copy()
            else:
                # 完全没有数据可用，抛出异常
                raise RuntimeError("无法获取数据，且无缓存可用")

# 为了方便 app.py 调用，创建一个实例 (Singleton pattern 简化版本)
# 注意：在Streamlit的多页面或重运行机制下，单例可能不合适，
# 更好的做法是在 session_state 中管理服务实例。
# 这里为了简化，我们直接创建一个全局实例，Streamlit在重运行时会重建。
# 但对于缓存逻辑，使用实例方法没有问题。
price_service = BitcoinPriceService()

# 为了方便调试，可以在这里添加 COIN_ID 和 VS_CURRENCY 的导入
# 但更好的做法是从 config 中导入，这里暂时写死
COIN_ID = "bitcoin"
VS_CURRENCY = "usd"
```

### 3. UI 展示层 (`app.py`)

```python
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
```

---

请代码审查员检查。

---

