"""
简化版DCS API客户端
提供核心的连接、命令发送和数据接收功能
"""
import threading
import time
import logging
from typing import Dict, List, Optional, Callable, Any
from dcs_api_parser import DCSAPI, load_predefined_apis
from dcs_network import DCSNetwork
from dcs_command_processor import DCSCommandProcessor
from dcs_event_handler import DCSEventHandler
from dcs_data_processor import DCSDataProcessor
from dcs_api_definitions import DCS_APIS

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DCSClient")

class DCSClient:
    """简化版DCS客户端，专注于核心功能"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7777, log_level: int = logging.INFO):
        # 基础配置
        self.host = host
        self.port = port
        logger.setLevel(log_level)
        
        # 核心子模块
        self.network = DCSNetwork(host, port)
        self.cmd_processor = DCSCommandProcessor()
        self.event_handler = DCSEventHandler()
        self.data_processor = DCSDataProcessor()
        
        # 加载API定义
        self.api_list = load_predefined_apis(DCS_APIS)
        logger.info(f"已加载 {len(self.api_list)} 个API定义")
        
        # 状态管理
        self._stop_event = threading.Event()
        self._listener_thread: Optional[threading.Thread] = None
        
        # 初始化回调链
        self._setup_callbacks()
    
    def _setup_callbacks(self) -> None:
        """设置模块间回调关系（简化版）"""
        # 网络数据 → 数据处理器
        self.network.data_received_callback = self.data_processor.handle_raw_data
        
        # 数据处理结果 → 事件触发
        self.data_processor.api_data_callback = self.event_handler.trigger_api_data_received
        self.data_processor.error_callback = self.event_handler.trigger_error_received
        
        # 命令发送回调
        self.cmd_processor.send_data_callback = self.network.send_data
        self.data_processor.api_data_callback = self._on_api_response  # 响应处理
    
    def _on_api_response(self, api: DCSAPI) -> None:
        """API响应处理（合并事件触发和命令队列推进）"""
        self.event_handler.trigger_api_data_received(api)
        self.cmd_processor.mark_response_received()
    
    def connect(self) -> bool:
        """连接到服务器（简化重连逻辑）"""
        if self.network.connect():
            self._stop_event.clear()
            self._listener_thread = threading.Thread(
                target=self.network.start_listening,
                args=(self._stop_event,)
            )
            self._listener_thread.daemon = True
            self._listener_thread.start()
            self.event_handler.trigger_connection_changed(True)
            return True
        
        self.event_handler.trigger_connection_changed(False)
        return False
    
    def disconnect(self) -> None:
        """断开连接（简化资源清理）"""
        self._stop_event.set()
        self.network.disconnect()
        if self._listener_thread:
            self._listener_thread.join(timeout=1.0)
        self.event_handler.trigger_connection_changed(False)
    
    def send_command(self, api_id: int, params: Dict[str, Any] = None) -> bool:
        """发送命令（简化API查找逻辑）"""
        if not self.is_connected:
            logger.warning("未连接，无法发送命令")
            return False
        
        # 查找API
        api_def = next((a for a in self.api_list if a.id == api_id), None)
        if not api_def:
            logger.error(f"未找到API ID: {api_id}")
            return False
        
        # 创建并发送命令
        api = DCSAPI(
            id=api_def.id,
            returns_data=api_def.returns_data,
            api_syntax=api_def.api_syntax,
            parameter_count=api_def.parameter_count,
            parameter_defs=api_def.parameters
        )
        return self.cmd_processor.queue_command(api, params)
    
    # 简化API查询方法
    def get_api(self, api_id: int = None, api_name: str = None) -> Optional[DCSAPI]:
        """统一的API查询方法"""
        if api_id is not None:
            return next((a for a in self.api_list if a.id == api_id), None)
        if api_name is not None:
            return next((a for a in self.api_list if a.api_syntax == api_name), None)
        return None
    
    def get_apis_matching(self, pattern: str) -> List[DCSAPI]:
        """按模式匹配API"""
        pattern = pattern.lower()
        return [a for a in self.api_list if pattern in a.api_syntax.lower()]
    
    @property
    def is_connected(self) -> bool:
        """连接状态属性（替代方法调用）"""
        return self.network.is_connected

# 示例用法
if __name__ == "__main__":
    # 创建客户端
    client = DCSClient("127.0.0.1", 7790, logging.DEBUG)
    
    # 简单回调
    client.event_handler.on_connection_changed = lambda connected: print(f"连接状态: {connected}")
    client.event_handler.on_api_data_received = lambda api: print(f"收到数据: {api.api_syntax}")
    
    # 连接并发送命令
    if client.connect():
        print("连接成功，发送测试命令...")
        client.send_command(17)  # 发送LoGetSelfData命令
        
        # 保持运行
        try:
            while client.is_connected:
                time.sleep(1)
        except KeyboardInterrupt:
            print("用户中断")
        finally:
            client.disconnect()
    else:
        print("连接失败")
