"""
简化版DCS API客户端（高性能优化版）
保留核心结构，减少不必要的性能开销
"""
import threading
import time
import logging
from typing import Dict, Optional, Callable, Any
from dcs_api_parser import DCSAPI, load_predefined_apis
from dcs_network import DCSNetwork
from dcs_command_processor import DCSCommandProcessor
from dcs_event_handler import DCSEventHandler
from dcs_data_processor import DCSDataProcessor
from dcs_api_definitions import DCS_APIS

# 配置日志（仅初始化一次，减少IO开销）
if not logging.getLogger("DCSClient").handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DCSClient")

class DCSClient:
    """简化版DCS客户端，专注于核心功能（性能优化）"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7777, log_level: int = logging.INFO):
        # 基础配置（减少属性查找层级）
        self.host = host
        self.port = port
        logger.setLevel(log_level)
        
        # 核心子模块（保持原有结构）
        self.network = DCSNetwork(host, port)
        self.cmd_processor = DCSCommandProcessor()
        self.event_handler = DCSEventHandler()
        self.data_processor = DCSDataProcessor()
        
        # 加载API定义并构建ID映射（O(1)查询优化）
        self.api_list = load_predefined_apis(DCS_APIS)
        self._api_id_map = {api.id: api for api in self.api_list}  # 替代线性查找
        logger.info(f"已加载 {len(self.api_list)} 个API定义")
        
        # 状态管理（精简变量）
        self._stop_event = threading.Event()
        self._listener_thread: Optional[threading.Thread] = None
        
        # 初始化回调链（保持原有逻辑，减少中间调用）
        self._setup_callbacks()
    
    def _setup_callbacks(self) -> None:
        """设置模块间回调关系（直接绑定，减少层级）"""
        self.network.data_received_callback = self.data_processor.handle_raw_data
        self.data_processor.api_data_callback = self._on_api_response
        self.data_processor.error_callback = self.event_handler.trigger_error_received
        self.cmd_processor.send_data_callback = self.network.send_data
    
    def _on_api_response(self, api: DCSAPI) -> None:
        """API响应处理（合并操作，减少函数调用）"""
        self.event_handler.trigger_api_data_received(api)
        self.cmd_processor.mark_response_received()
    
    def connect(self) -> bool:
        """连接到服务器（优化线程启动）"""
        if self.network.connect():
            self._stop_event.clear()
            # 直接启动守护线程，减少属性设置开销
            self._listener_thread = threading.Thread(
                target=self.network.start_listening,
                args=(self._stop_event,),
                daemon=True
            )
            self._listener_thread.start()
            self.event_handler.trigger_connection_changed(True)
            return True
        
        self.event_handler.trigger_connection_changed(False)
        return False
    
    def disconnect(self) -> None:
        """断开连接（快速清理资源）"""
        self._stop_event.set()
        self.network.disconnect()
        if self._listener_thread:
            self._listener_thread.join(timeout=0.5)  # 缩短超时，加速退出
            self._listener_thread = None  # 释放引用，帮助GC
        self.event_handler.trigger_connection_changed(False)
    
    def send_command(self, api_id: int, params: Dict[str, Any] = None) -> bool:
        """发送命令（优化API查找和参数处理）"""
        if not self.is_connected:
            logger.warning("未连接，无法发送命令")
            return False
        
        # O(1)查找API（替代原线性查找）
        api_def = self._api_id_map.get(api_id)
        if not api_def:
            logger.error(f"未找到API ID: {api_id}")
            return False
        
        # 简化参数处理（默认空字典，减少条件判断）
        params = params or {}
        
        # 减少对象创建开销（直接复用api_def属性）
        return self.cmd_processor.queue_command(
            DCSAPI(
                id=api_def.id,
                returns_data=api_def.returns_data,
                api_syntax=api_def.api_syntax,
                parameter_count=api_def.parameter_count,
                parameter_defs=api_def.parameters
            ),
            params
        )
    
    @property
    def is_connected(self) -> bool:
        """连接状态属性（直接返回，减少中间计算）"""
        return self.network.is_connected

# 示例用法（保持兼容）
if __name__ == "__main__":
    client = DCSClient("127.0.0.1", 7790, logging.DEBUG)
    
    # 简单回调
    client.event_handler.on_connection_changed = lambda connected: print(f"连接状态: {connected}")
    client.event_handler.on_api_data_received = lambda api: print(f"收到数据: {api.api_syntax}")
    
    if client.connect():
        print("连接成功，发送测试命令...")
        client.send_command(17)  # 发送LoGetSelfData命令
        
        try:
            while client.is_connected:
                time.sleep(0.1)  # 缩短等待间隔，减少响应延迟
        except KeyboardInterrupt:
            print("用户中断")
        finally:
            client.disconnect()
    else:
        print("连接失败")
