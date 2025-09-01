"""
DCS 事件处理模块
负责管理各种事件回调
"""
import logging
from typing import Optional, Callable
from dcs_api_parser import DCSAPI

logger = logging.getLogger("DCSEventHandler")

class DCSEventHandler:
    def __init__(self):
        # 连接状态变化回调
        self.on_connection_changed: Optional[Callable[[bool], None]] = None
        # API数据接收回调
        self.on_api_data_received: Optional[Callable[[DCSAPI], None]] = None
        # 错误接收回调
        self.on_error_received: Optional[Callable[[str, str], None]] = None
    
    def trigger_connection_changed(self, connected: bool) -> None:
        """触发连接状态变化事件"""
        if self.on_connection_changed:
            try:
                self.on_connection_changed(connected)
            except Exception as e:
                logger.error(f"连接状态回调执行失败: {e}")
    
    def trigger_api_data_received(self, api: DCSAPI) -> None:
        """触发API数据接收事件"""
        if self.on_api_data_received:
            try:
                self.on_api_data_received(api)
            except Exception as e:
                logger.error(f"API数据接收回调执行失败: {e}")
    
    def trigger_error_received(self, error_type: str, message: str) -> None:
        """触发错误接收事件"""
        logger.error(f"{error_type}: {message}")
        if self.on_error_received:
            try:
                self.on_error_received(error_type, message)
            except Exception as e:
                logger.error(f"错误回调执行失败: {e}")
