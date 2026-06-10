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
