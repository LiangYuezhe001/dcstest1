"""
DCS 网络通信模块
负责底层Socket连接、数据发送和接收
"""
import socket
import select
import logging
from typing import Optional, Callable

logger = logging.getLogger("DCSNetwork")

class DCSNetwork:
    def __init__(self, host: str = "127.0.0.1", port: int = 7777):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self._connected = False
        self.data_received_callback: Optional[Callable[[bytes], None]] = None
    
    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected
    
    def connect(self) -> bool:
        """建立连接"""
        try:
            logger.info(f"连接到 {self.host}:{self.port}")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(None)
            self._connected = True
            logger.info("连接成功")
            return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """断开连接"""
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.warning(f"关闭连接时出错: {e}")
            self.socket = None
        self._connected = False
        logger.info("已断开连接")
    
    def send_data(self, data: bytes) -> bool:
        """发送数据"""
        if not self._connected or not self.socket:
            logger.warning("未连接，无法发送数据")
            return False
        
        try:
            self.socket.sendall(data)
            return True
        except Exception as e:
            logger.error(f"发送数据失败: {e}")
            self._connected = False
            return False
    
    def start_listening(self, stop_event) -> None:
        """开始监听数据（应在单独线程中运行）"""
        logger.debug("开始监听数据")
        while not stop_event.is_set() and self._connected and self.socket:
            try:
                readable, _, _ = select.select([self.socket], [], [], 1.0)
                if not readable:
                    continue
                
                data = self.socket.recv(4096)
                if not data:
                    logger.debug("未收到数据，连接可能已关闭")
                    self._connected = False
                    break
                
                if self.data_received_callback:
                    self.data_received_callback(data)
                
            except Exception as e:
                logger.error(f"监听数据时出错: {e}")
                self._connected = False
                break
        
        logger.debug("监听结束")
