import logging
import time
from typing import List, Dict, Any
from dcs_client import DCSClient
from dcs_data_parser import DCSDataParser
from dcs_display import DCSDisplayFormatter  # 导入显示模块


class DCSObjectDisplay:
    """DCS物体监控主类，负责数据获取和解析，依赖外部模块进行显示"""
    
    def __init__(self, host="127.0.0.1", port=7790, update_interval=5.0, debug=False):
        """初始化主类"""
        self.client = DCSClient(host, port, log_level=logging.WARNING)
        self.parser = DCSDataParser()
        self.update_interval = update_interval
        self.running = False
        
        # 初始化显示模块
        self.display = DCSDisplayFormatter(debug=debug)
        
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """设置回调函数"""
        self.client.event_handler.on_connection_changed = self._on_connection_changed
        self.client.event_handler.on_api_data_received = self._on_api_data_received
        self.client.event_handler.on_error_received = self._on_error_received
    
    def _on_connection_changed(self, connected):
        """处理连接状态变化"""
        if connected:
            print("已连接到DCS服务器，开始获取物体数据...")
        else:
            print("\n与DCS服务器的连接已断开")
    
    def _on_api_data_received(self, api):
        """处理接收到的API数据"""
        if api.id == 52 and api.result:
            try:
                # 解析数据
                parsed_objects: List[Dict[str, Any]] = self.parser.parse_data(api.result)
                
                # 调用外部模块进行显示
                self.display.display_objects(parsed_objects, self.update_interval)
                
                # 打印调试信息（通过显示模块）
                self.display.print_debug_info(api.result, parsed_objects)
                
            except Exception as e:
                print(f"处理数据出错: {str(e)}")
    
    def _on_error_received(self, error_type, message):
        """处理错误信息"""
        print(f"\n[错误] {error_type}: {message}")
    
    def start(self):
        """启动监控"""
        self.running = True
        if not self.client.connect():
            print("无法连接到DCS服务器")
            return
        
        try:
            while self.running and self.client.is_connected:
                self.client.send_command(52)
                time.sleep(self.update_interval)
        except KeyboardInterrupt:
            print("\n用户中断监控")
        finally:
            self.stop()
    
    def stop(self):
        """停止监控"""
        self.running = False
        print("停止监控...")
        self.client.disconnect()


if __name__ == "__main__":
    # 实例化主类并启动
    display = DCSObjectDisplay(
        update_interval=5.0,
        debug=False
    )
    display.start()
