# dcs_object_monitor.py
import logging
import time
from typing import List, Dict, Any, Callable
from dcs_client import DCSClient
from dcs_data_parser import DCSDataParser
from dcs_display import DCSDisplayFormatter


class DCSObjectMonitor:
    """DCS物体监控模块，负责获取、解析DCS物体数据并提供数组访问接口"""
    
    def __init__(self, 
                 host: str = "127.0.0.1", 
                 port: int = 7790, 
                 update_interval: float = 5.0, 
                 debug: bool = False):
        """
        初始化监控器
        :param host: DCS服务器地址
        :param port: 连接端口
        :param update_interval: 数据更新间隔(秒)
        :param debug: 是否启用调试模式
        """
        self.client = DCSClient(host, port, log_level=logging.WARNING)
        self.parser = DCSDataParser()
        self.update_interval = update_interval
        self.debug = debug
        self.running = False
        self._objects: List[Dict[str, Any]] = []  # 存储物体数据的数组
        self._display = DCSDisplayFormatter(debug=debug)
        
        # 注册回调函数
        self._setup_callbacks()
        
        # 外部回调（可选）
        self.on_objects_updated: Callable[[List[Dict[str, Any]]], None] = None

    def _setup_callbacks(self) -> None:
        """设置内部回调函数"""
        self.client.event_handler.on_connection_changed = self._on_connection_changed
        self.client.event_handler.on_api_data_received = self._on_api_data_received
        self.client.event_handler.on_error_received = self._on_error_received

    def _on_connection_changed(self, connected: bool) -> None:
        """处理连接状态变化"""
        if connected:
            print("已连接到DCS服务器，开始获取物体数据...")
        else:
            print("\n与DCS服务器的连接已断开")

    def _on_api_data_received(self, api) -> None:
        """处理接收到的API数据并更新物体数组"""
        if api.id == 52 and api.result:
            try:
                # 解析数据并更新内部数组
                self._objects = self.parser.parse_data(api.result)
                
                # 触发外部回调（如果有）
                if self.on_objects_updated:
                    self.on_objects_updated(self._objects.copy())
                
                # 调试模式下显示数据
                if self.debug:
                    self._display.display_objects(self._objects, self.update_interval)
                    self._display.print_debug_info(api.result, self._objects)

            except Exception as e:
                print(f"处理数据出错: {str(e)}")

    def _on_error_received(self, error_type: str, message: str) -> None:
        """处理错误信息"""
        print(f"\n[错误] {error_type}: {message}")

    def get_objects(self) -> List[Dict[str, Any]]:
        """
        获取当前解析后的物体数组
        :return: 物体字典列表，每个字典包含物体详细信息
        """
        return self._objects.copy()  # 返回副本避免外部修改内部数据

    def start(self) -> None:
        """启动监控循环"""
        self.running = True
        if not self.client.connect():
            print("无法连接到DCS服务器")
            return

        try:
            while self.running and self.client.is_connected:
                self.client.send_command(52)  # 请求物体列表数据
                time.sleep(self.update_interval)
        except KeyboardInterrupt:
            print("\n用户中断监控")
        finally:
            self.stop()

    def stop(self) -> None:
        """停止监控并断开连接"""
        self.running = False
        print("停止监控...")
        self.client.disconnect()


# 使用示例
if __name__ == "__main__":
    # 示例1：基础使用（获取物体数组）
    monitor = DCSObjectMonitor(update_interval=5.0, debug=False)
    
    # 启动监控（在单独线程中运行可避免阻塞）
    import threading
    monitor_thread = threading.Thread(target=monitor.start, daemon=True)
    monitor_thread.start()
    
    # 主循环中获取数据
    try:
        while True:
            objects = monitor.get_objects()
            if objects:
                print(f"\n当前物体数量: {len(objects)}")
                # 打印第一个物体的简要信息
                print(f"首个物体: ID={objects[0]['id']}, 名称={objects[0].get('Name', '未知')}")
            time.sleep(2)
    except KeyboardInterrupt:
        monitor.stop()
        monitor_thread.join()
