# dcs_object_manager.py
import logging
import time
from typing import Dict, Any, Optional, Callable, List
from dcs_client import DCSClient
from dcs_data_parser import DCSDataParser
from dcs_api_parser import DCSAPI


class DCSObjectManager:
    """
    DCS物体管理模块，整合批量获取物体列表与单个物体查询功能
    支持通过ID=52获取所有物体，通过ID=10查询指定ID物体
    """
    
    def __init__(self,
                 host: str = "127.0.0.1",
                 port: int = 7790,
                 update_interval: float = 5.0,
                 debug: bool = False):
        """
        初始化物体管理器
        :param host: DCS服务器地址
        :param port: 连接端口
        :param update_interval: 批量数据更新间隔(秒)
        :param debug: 是否启用调试模式
        """
        # 核心组件（复用原有模块的初始化逻辑）
        self.client = DCSClient(host, port, log_level=logging.WARNING)
        self.parser = DCSDataParser()
        self.debug = debug
        self.update_interval = update_interval
        self.connected = False
        self.running = False  # 用于控制批量监控循环
        
        # 数据存储（区分批量数据和单个查询数据）
        self._all_objects: List[Dict[str, Any]] = []  # 批量获取的物体数组
        self._current_object: Optional[Dict[str, Any]] = None  # 单个查询结果
        self._fetching_id: Optional[int] = None  # 当前正在查询的单个物体ID
        
        # 事件回调（区分两种功能的回调）
        # 批量数据回调
        self.on_all_objects_updated: Optional[Callable[[List[Dict[str, Any]]], None]] = None
        # 单个物体查询回调
        self.on_single_object_fetched: Optional[Callable[[Dict[str, Any]], None]] = None
        # 通用错误回调
        self.on_error_occurred: Optional[Callable[[str], None]] = None
        
        # 初始化回调关系（统一管理）
        self._setup_callbacks()

    def _setup_callbacks(self) -> None:
        """统一设置回调函数，处理连接状态和API响应"""
        self.client.event_handler.on_connection_changed = self._on_connection_changed
        self.client.event_handler.on_api_data_received = self._on_api_data_received
        self.client.event_handler.on_error_received = self._on_error_received

    def _on_connection_changed(self, connected: bool) -> None:
        """处理连接状态变化（复用原有逻辑）"""
        self.connected = connected
        if self.debug:
            status = "已连接" if connected else "已断开"
            print(f"与DCS服务器的连接{status}")

    def _on_api_data_received(self, api: DCSAPI) -> None:
        """区分处理两种API的响应数据（ID=52和ID=10）"""
        # 处理批量获取物体列表的响应（ID=52）
        if api.id == 52 and api.result:
            self._handle_batch_data(api.result)
        # 处理单个物体查询的响应（ID=10）
        elif api.id == 10 and self._fetching_id is not None:
            self._handle_single_data(api.result)

    def _handle_batch_data(self, raw_data: Any) -> None:
        """处理批量获取的物体数据（复用monitor的解析逻辑）"""
        try:
            parsed_data = self.parser.parse_data(raw_data)
            self._all_objects = parsed_data
            if self.debug:
                print(f"已更新物体列表，共{len(parsed_data)}个物体")
            
            # 触发批量数据更新回调
            if self.on_all_objects_updated:
                self.on_all_objects_updated(self._all_objects.copy())
                
        except Exception as e:
            error_msg = f"批量数据解析失败: {str(e)}"
            print(error_msg)
            if self.on_error_occurred:
                self.on_error_occurred(error_msg)

    def _handle_single_data(self, raw_data: Any) -> None:
        """处理单个物体查询的数据（复用fetcher的解析逻辑）"""
        try:
            parsed_data = self.parser.parse_data(raw_data)
            if parsed_data and len(parsed_data) > 0:
                self._current_object = parsed_data[0]
                if self.debug:
                    print(f"单个物体查询完成，ID={self._current_object.get('id')}")
                
                # 触发单个物体查询回调
                if self.on_single_object_fetched:
                    self.on_single_object_fetched(self._current_object)
            else:
                error_msg = f"未找到ID={self._fetching_id}的物体数据"
                print(error_msg)
                if self.on_error_occurred:
                    self.on_error_occurred(error_msg)
                    
        except Exception as e:
            error_msg = f"单个物体数据解析失败: {str(e)}"
            print(error_msg)
            if self.on_error_occurred:
                self.on_error_occurred(error_msg)
        finally:
            self._fetching_id = None  # 重置查询状态

    def _on_error_received(self, error_type: str, message: str) -> None:
        """统一处理错误信息"""
        error_msg = f"[错误] {error_type}: {message}"
        print(error_msg)
        if self.on_error_occurred:
            self.on_error_occurred(error_msg)

    # ------------------------------
    # 批量获取物体列表相关方法（源自monitor）
    # ------------------------------
    def start_monitoring(self) -> bool:
        """启动批量物体监控（定期获取所有物体）"""
        if not self.connect():
            return False
        self.running = True
        # 启动监控线程
        import threading
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        return True

    def _monitor_loop(self) -> None:
        """监控循环：定期发送批量查询命令"""
        while self.running and self.connected:
            self.client.send_command(52)  # 发送批量查询命令
            time.sleep(self.update_interval)

    def get_all_objects(self) -> List[Dict[str, Any]]:
        """获取当前所有物体的数组副本"""
        return self._all_objects.copy()

    # ------------------------------
    # 单个物体查询相关方法（源自fetcher）
    # ------------------------------
    def fetch_object_by_id(self, object_id: int, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
        """通过ID查询单个物体参数（同步方法）"""
        if not self.connected:
            error_msg = "未连接到DCS服务器，请先调用connect()"
            print(error_msg)
            if self.on_error_occurred:
                self.on_error_occurred(error_msg)
            return None
        
        # 重置状态并记录查询ID
        self._current_object = None
        self._fetching_id = object_id
        
        # 发送单个查询命令
        self.client.send_command(10, {"object_id": object_id})
        
        # 等待结果（超时处理）
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._current_object is not None:
                return self._current_object
            if self._fetching_id is None:  # 查询完成但无结果
                return None
            time.sleep(0.1)
        
        # 超时处理
        error_msg = f"查询物体ID={object_id}超时（{timeout}秒）"
        print(error_msg)
        if self.on_error_occurred:
            self.on_error_occurred(error_msg)
        self._fetching_id = None
        return None

    # ------------------------------
    # 通用连接管理方法（复用两个模块的设计）
    # ------------------------------
    def connect(self) -> bool:
        """连接到DCS服务器"""
        if not self.connected:
            return self.client.connect()
        return True

    def disconnect(self) -> None:
        """断开连接"""
        self.running = False  # 停止监控循环
        self.client.disconnect()

    def stop_monitoring(self) -> None:
        """停止批量监控"""
        self.running = False
        if hasattr(self, '_monitor_thread'):
            self._monitor_thread.join(timeout=2.0)


# 使用示例：同时展示批量监控和单个查询功能
if __name__ == "__main__":
    # 初始化管理器
    manager = DCSObjectManager(
        update_interval=5.0,
        debug=True
    )
    
    # 启动批量监控
    if not manager.start_monitoring():
        print("无法连接到DCS服务器，退出程序")
        exit(1)
    
    try:
        # 示例1：定期打印批量获取的物体数量
        print("\n----- 批量监控演示 -----")
        for _ in range(3):  # 演示3次更新
            objects = manager.get_all_objects()
            print(f"当前物体总数: {len(objects)}")
            time.sleep(2)
        
        # 示例2：从批量数据中取第一个ID进行单个查询
        print("\n----- 单个物体查询演示 -----")
        all_objects = manager.get_all_objects()
        if all_objects:
            target_id = all_objects[0]['id']  # 取第一个物体的ID
            print(f"查询物体ID={target_id}的详细信息...")
            obj_data = manager.fetch_object_by_id(target_id)
            
            if obj_data:
                print("查询结果：")
                print(f"ID: {obj_data.get('id')}")
                print(f"名称: {obj_data.get('Name', '未知')}")
                print(f"国家: {obj_data.get('Country', '未知')}")
                print(f"位置: {obj_data.get('Position', {})}")
                print(f"经纬度: {obj_data.get('LatLongAlt', {})}")
        else:
            print("没有获取到批量物体数据，无法进行单个查询演示")
            
    except KeyboardInterrupt:
        print("\n用户中断操作")
    finally:
        manager.stop_monitoring()
        manager.disconnect()
        print("程序已退出")
