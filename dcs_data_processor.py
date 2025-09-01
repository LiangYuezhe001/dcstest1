"""
DCS 数据处理与解析模块
负责网络数据的解码、JSON解析和处理
"""
import json
import logging
from typing import Dict, Callable, Optional, Any
from dcs_api_parser import create_api_from_dict, DCSAPI

logger = logging.getLogger("DCSDataProcessor")

class DCSDataProcessor:
    def __init__(self):
        self.current_buffer = ""
        self.json_decoder = json.JSONDecoder()
        self.api_data_callback: Optional[Callable[[DCSAPI], None]] = None
        self.error_callback: Optional[Callable[[str, str], None]] = None
    
    def handle_raw_data(self, data: bytes) -> None:
        """处理原始字节数据，进行解码并尝试解析"""
        try:
            # 尝试解码数据
            decoded_data = data.decode('utf-8')
        except UnicodeDecodeError:
            try:
                decoded_data = data.decode('latin-1')
            except UnicodeDecodeError:
                if self.error_callback:
                    self.error_callback(
                        "解码错误", f"无法解码数据: {data.hex()}")
                return
        
        # 累积数据并尝试解析
        self.current_buffer += decoded_data
        self._try_parse_json()
    
    def _try_parse_json(self) -> None:
        """尝试解析缓冲区中的JSON数据"""
        while self.current_buffer:
            try:
                obj, index = self.json_decoder.raw_decode(self.current_buffer)
                self._handle_parsed_json(obj)
                self.current_buffer = self.current_buffer[index:].lstrip()
            except json.JSONDecodeError:
                # 不完整的JSON，等待更多数据
                break
            except Exception as e:
                if self.error_callback:
                    self.error_callback(
                        "解析错误", f"解析JSON失败: {str(e)}")
                self.current_buffer = ""
                break
    
    def _handle_parsed_json(self, data: Dict[str, Any]) -> None:
        """处理解析后的JSON数据"""
        try:
            api = create_api_from_dict(data)
            if self.api_data_callback:
                self.api_data_callback(api)
        except Exception as e:
            if self.error_callback:
                self.error_callback(
                    "数据处理错误", f"处理API数据失败: {str(e)}")
