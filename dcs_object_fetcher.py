# dcs_object_fetcher.py
import logging
import time
from typing import List, Dict, Any, Optional, Callable
from dcs_client import DCSClient
from dcs_data_parser import DCSDataParser  # 导入数据解析器
from dcs_api_parser import DCSAPI  # 用于处理API对象


class DCSObjectFetcher:
    """通过ID获取指定物体参数的模块"""
    
    def __init__(self, 
                 host: str = "127.0.0.1", 
                 port: int = 7790, 
                 debug: bool = False):
        """
        初始化物体获取器
        :param host: DCS服务器地址
        :param port: 连接端口
        :param debug: 是否启用调试模式
        """
        self.client = DCSClient(host, port, log_level=logging.WARNING)
        self.parser = DCSDataParser()  # 初始化数据解析器
        self.debug = debug
        self.connected = False
        self._target_object: Optional[Dict[str, Any]] = None  # 存储获取到的物体数据
        self._fetch_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        
        # 注册回调函数
        self._setup_callbacks()

    def _setup_callbacks(self) -> None:
        """设置回调函数处理连接状态和API返回数据"""
        self.client.event_handler.on_connection_changed = self._on_connection_changed
        self.client.event_handler.on_api_data_received = self._on_api_data_received
        self.client.event_handler.on_error_received = self._on_error_received

    def _on_connection_changed(self, connected: bool) -> None:
        """处理连接状态变化"""
        self.connected = connected
        if connected:
            if self.debug:
                print("已连接到DCS服务器")
        else:
            print("与DCS服务器的连接已断开")

    def _on_api_data_received(self, api: DCSAPI) -> None:
        """处理API返回数据（仅关注ID=10的LoGetObjectById结果）"""
        if api.id == 10 and api.result:
            try:
                # 使用dcs_data_parser解析返回的物体数据
                # 注意：API返回的单个物体数据格式与批量数据一致，可直接用parse_data解析
                parsed_objects: List[Dict[str, Any]] = self.parser.parse_data(api.result)
                
                # 提取第一个物体（因按ID查询应只返回一个结果）
                if parsed_objects:
                    self._target_object = parsed_objects[0]
                    if self.debug:
                        print(f"成功解析ID为{self._target_object.get('id')}的物体数据")
                    
                    # 触发外部回调（如果设置）
                    if self._fetch_callback:
                        self._fetch_callback(self._target_object)
                else:
                    print("未解析到物体数据（可能ID不存在）")

            except Exception as e:
                print(api.result)
                print(f"解析物体数据失败: {str(e)}")

    def _on_error_received(self, error_type: str, message: str) -> None:
        """处理错误信息"""
        print(f"[错误] {error_type}: {message}")

    def get_object_by_id(self, object_id: int, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
        """
        通过ID获取物体参数
        :param object_id: 目标物体ID
        :param timeout: 超时时间（秒）
        :return: 解析后的物体参数字典，超时或失败返回None
        """
        if not self.connected:
            print("未连接到服务器，请先调用connect()")
            return None
        
        # 重置上一次的结果
        self._target_object = None
        
        # 发送ID=10的API命令，传入object_id参数
        self.client.send_command(10, {"object_id": object_id})
        
        # 等待结果（超时机制）
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._target_object is not None:
                return self._target_object
            time.sleep(0.1)
        
        print(f"获取物体ID={object_id}超时（{timeout}秒）")
        return None

    def set_fetch_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """设置获取到物体数据后的回调函数（异步处理用）"""
        self._fetch_callback = callback

    def connect(self) -> bool:
        """连接到DCS服务器"""
        return self.client.connect()

    def disconnect(self) -> None:
        """断开与服务器的连接"""
        self.client.disconnect()


# 使用示例
if __name__ == "__main__":
    # 初始化获取器
    fetcher = DCSObjectFetcher(debug=True)
    
    # 连接服务器
    if not fetcher.connect():
        print("无法连接到DCS服务器，退出程序")
        exit(1)
    
    try:
        # 示例：获取ID为16788480的物体数据（可替换为实际存在的ID）
        target_id = 16788480
        print(f"正在获取物体ID={target_id}的参数...")
        obj_data = fetcher.get_object_by_id(target_id)
        
        
        if obj_data:
            print("\n获取到的物体参数：")
            print(f"ID: {obj_data.get('id')}")
            print(f"名称: {obj_data.get('Name', '未知')}")
            print(f"国家: {obj_data.get('Country', '未知')}")
            print(f"位置: {obj_data.get('Position', {})}")
            print(f"经纬度: {obj_data.get('LatLongAlt', {})}")
    except KeyboardInterrupt:
        print("\n用户中断操作")
    finally:
        fetcher.disconnect()
