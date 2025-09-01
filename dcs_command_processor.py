"""
DCS 命令处理模块
负责命令队列管理和命令发送逻辑
"""
import json
import logging
from typing import List, Dict, Optional, Callable, Any
from dcs_api_parser import DCSAPI

logger = logging.getLogger("DCSCommandProcessor")

class DCSCommandProcessor:
    def __init__(self):
        self.command_queue: List[DCSAPI] = []
        self.response_received = True
        self.send_data_callback: Optional[Callable[[bytes], bool]] = None
        self.command_completed_callback: Optional[Callable[[], None]] = None
    
    def queue_command(self, api: DCSAPI, params: Dict[str, Any] = None) -> bool:
        """将命令加入队列"""
        # 设置参数
        if params:
            for param_name, param_value in params.items():
                try:
                    api.set_parameter_value(param_name, param_value)
                except ValueError as e:
                    logger.error(f"设置参数失败: {e}")
                    return False
        
        self.command_queue.append(api)
        logger.debug(f"命令已加入队列: {api.api_syntax}, 队列长度: {len(self.command_queue)}")
        
        # 如果可以发送，立即尝试发送下一个命令
        if self.response_received and self.send_data_callback:
            self.send_next_command()
        
        return True
    
    def send_next_command(self) -> bool:
        """发送队列中的下一个命令"""
        if not self.command_queue or not self.response_received or not self.send_data_callback:
            return False
        
        try:
            api = self.command_queue.pop(0)
            json_str = json.dumps(api.to_dict()) + "\n"
            logger.debug(f"发送命令: {json_str.strip()}")
            
            success = self.send_data_callback(json_str.encode('utf-8'))
            if success:
                self.response_received = False
                return True
            return False
        except Exception as e:
            logger.error(f"发送命令失败: {e}")
            return False
    
    def mark_response_received(self) -> None:
        """标记响应已接收，准备发送下一个命令"""
        self.response_received = True
        logger.debug("响应已接收")
        
        # 如果有命令队列，发送下一个命令
        if self.command_queue and self.send_data_callback:
            self.send_next_command()
        elif self.command_completed_callback:
            self.command_completed_callback()
