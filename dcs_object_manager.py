import logging
import time
import threading
from typing import Dict, Any, Optional, Callable, List, Set
from dataclasses import dataclass
from contextlib import contextmanager
from dcs_client import DCSClient
from dcs_data_parser import DCSDataParser
from dcs_api_parser import DCSAPI


@dataclass
class MonitorConfig:
    """监控配置数据类"""
    batch_interval: float = 5.0
    single_interval: float = 2.0
    self_interval: float = 1.0
    enabled: bool = False


class DCSObjectManager:
    """
    简化版的DCS物体管理模块，支持批量获取物体列表、单个物体查询和自身数据获取功能
    """
    
    def __init__(self,
                 host: str = "127.0.0.1",
                 port: int = 7790,
                 batch_update_interval: float = 5.0,
                 single_update_interval: float = 2.0,
                 self_update_interval: float = 1.0,
                 debug: bool = False):
        """
        初始化物体管理器
        :param host: DCS服务器地址
        :param port: 连接端口
        :param batch_update_interval: 批量数据自动更新间隔(秒)
        :param single_update_interval: 单个物体自动更新间隔(秒)
        :param self_update_interval: 自身数据自动更新间隔(秒)
        :param debug: 是否启用调试模式
        """
        # 配置日志
        self.logger = self._setup_logger(debug)
        
        # 核心组件
        self.client = DCSClient(host, port, log_level=logging.WARNING)
        self.parser = DCSDataParser()
        
        # 监控配置
        self.batch_monitor = MonitorConfig(batch_update_interval, enabled=False)
        self.self_monitor = MonitorConfig(self_update_interval, enabled=False)
        self.single_monitor_config = MonitorConfig(single_update_interval, enabled=False)
        
        # 状态标志
        self.connected = False
        self.running = False
        
        # 数据存储
        self._all_objects: List[Dict[str, Any]] = []
        self._monitored_objects: Dict[int, Dict[str, Any]] = {}
        self._self_data: Optional[Dict[str, Any]] = None
        
        # 查询状态
        self._pending_queries: Set[int] = set()
        self._pending_self_query = False
        
        # 事件回调
        self.callbacks = {
            'all_objects': None,
            'single_object': None,
            'self_data': None,
            'error': None
        }
        
        # 设置回调
        self._setup_callbacks()

    def _setup_logger(self, debug: bool) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("DCSObjectManager")
        logger.setLevel(logging.DEBUG if debug else logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    def _setup_callbacks(self) -> None:
        """设置回调函数"""
        self.client.event_handler.on_connection_changed = self._on_connection_changed
        self.client.event_handler.on_api_data_received = self._on_api_data_received
        self.client.event_handler.on_error_received = self._on_error_received

    def _on_connection_changed(self, connected: bool) -> None:
        """处理连接状态变化"""
        self.connected = connected
        status = "已连接" if connected else "已断开"
        self.logger.debug(f"与DCS服务器的连接{status}")

    def _on_api_data_received(self, api: DCSAPI) -> None:
        """处理API响应数据"""
        try:
            if api.id == 52 and api.result is not None:
                self._handle_batch_data(api.result)
            elif api.id == 10:
                self._handle_single_data(api.result)
            elif api.id == 17 and self._pending_self_query:
                self._handle_self_data(api.result)
        except Exception as e:
            self._handle_error(f"处理API响应失败: {str(e)}")

    def _handle_batch_data(self, raw_data: Any) -> None:
        """处理批量获取的物体数据"""
        parsed_data = self.parser.parse_data(raw_data)
        self._all_objects = parsed_data
        
        self.logger.debug(f"已更新物体列表，共{len(parsed_data)}个物体")
        
        if self.callbacks['all_objects']:
            self.callbacks['all_objects'](parsed_data)

    def _handle_single_data(self, raw_data: Any) -> None:
        """处理单个物体查询的数据"""
        parsed_data = self.parser.parse_data(raw_data)
        
        if parsed_data and isinstance(parsed_data, list) and len(parsed_data) > 0:
            object_data = parsed_data[0]
            object_id = object_data.get('id')
            
            if object_id and object_id in self._pending_queries:
                self._monitored_objects[object_id] = object_data
                self._pending_queries.discard(object_id)
                
                self.logger.debug(f"物体ID={object_id}数据更新")
                
                if self.callbacks['single_object']:
                    self.callbacks['single_object'](object_data)

    def _handle_self_data(self, raw_data: Any) -> None:
        """处理自身数据查询的响应"""
        parsed_data = self.parser.parse_data(raw_data)
        
        if parsed_data:
            if isinstance(parsed_data, list) and len(parsed_data) > 0:
                self._self_data = parsed_data[0]
            elif isinstance(parsed_data, dict):
                self._self_data = parsed_data
                
            self._pending_self_query = False
            self.logger.debug("自身数据更新")
            
            if self.callbacks['self_data']:
                self.callbacks['self_data'](self._self_data)

    def _on_error_received(self, error_type: str, message: str) -> None:
        """处理错误信息"""
        self._handle_error(f"{error_type}: {message}")

    def _handle_error(self, message: str) -> None:
        """错误处理"""
        self.logger.error(message)
        if self.callbacks['error']:
            self.callbacks['error'](message)

    def _start_monitoring(self) -> bool:
        """启动监控线程"""
        if not self.connect():
            return False
            
        if not self.running:
            self.running = True
            threading.Thread(
                target=self._monitor_loop, 
                daemon=True,
                name="DCSObjectMonitor"
            ).start()
            self.logger.debug("监控线程已启动")
            
        return True

    def _monitor_loop(self) -> None:
        """监控循环"""
        last_batch_time = 0.0
        last_self_time = 0.0
        last_single_times: Dict[int, float] = {}
        
        while self.running and self.connected:
            current_time = time.time()
            
            # 批量数据查询
            if (self.batch_monitor.enabled and 
                current_time - last_batch_time >= self.batch_monitor.batch_interval):
                self.client.send_command(52)
                last_batch_time = current_time
            
            # 自身数据查询
            if (self.self_monitor.enabled and 
                not self._pending_self_query and
                current_time - last_self_time >= self.self_monitor.self_interval):
                self.client.send_command(17)
                self._pending_self_query = True
                last_self_time = current_time
            
            # 单个物体查询
            if self.single_monitor_config.enabled:
                for obj_id in list(self._monitored_objects.keys()):
                    last_time = last_single_times.get(obj_id, 0.0)
                    if (obj_id not in self._pending_queries and
                        current_time - last_time >= self.single_monitor_config.single_interval):
                        self.client.send_command(10, {"object_id": obj_id})
                        self._pending_queries.add(obj_id)
                        last_single_times[obj_id] = current_time
            
            time.sleep(0.1)
        
        self.logger.debug("监控循环已退出")

    def _send_command_and_wait(self, command_id: int, params: Dict = None, 
                              timeout: float = 10.0) -> bool:
        """发送命令并等待响应"""
        if not self.connected:
            self._handle_error("未连接到DCS服务器")
            return False
        
        try:
            self.client.send_command(command_id, params)
            
            # 根据命令类型设置等待标志
            if command_id == 17:
                self._pending_self_query = True
                wait_condition = lambda: not self._pending_self_query
            elif command_id == 10 and params and 'object_id' in params:
                obj_id = params['object_id']
                self._pending_queries.add(obj_id)
                wait_condition = lambda: obj_id not in self._pending_queries
            else:  # 批量查询
                original_count = len(self._all_objects)
                wait_condition = lambda: len(self._all_objects) != original_count
            
            # 等待响应
            start_time = time.time()
            while time.time() - start_time < timeout:
                if wait_condition():
                    return True
                time.sleep(0.1)
            
            self._handle_error(f"命令{command_id}响应超时")
            return False
            
        except Exception as e:
            self._handle_error(f"发送命令失败: {str(e)}")
            return False

    def set_callback(self, event_type: str, callback: Callable) -> None:
        """设置事件回调"""
        if event_type in self.callbacks:
            self.callbacks[event_type] = callback
        else:
            self._handle_error(f"未知的事件类型: {event_type}")

    def start_monitoring(self, monitor_type: str = "all") -> bool:
        """启动监控"""
        if monitor_type == "all" or monitor_type == "batch":
            self.batch_monitor.enabled = True
        if monitor_type == "all" or monitor_type == "self":
            self.self_monitor.enabled = True
        if monitor_type == "all" or monitor_type == "single":
            self.single_monitor_config.enabled = True
            
        return self._start_monitoring()

    def stop_monitoring(self, monitor_type: str = "all") -> None:
        """停止监控"""
        if monitor_type == "all" or monitor_type == "batch":
            self.batch_monitor.enabled = False
        if monitor_type == "all" or monitor_type == "self":
            self.self_monitor.enabled = False
        if monitor_type == "all" or monitor_type == "single":
            self.single_monitor_config.enabled = False

    def fetch_all_objects(self, timeout: float = 10.0) -> Optional[List[Dict[str, Any]]]:
        """查询所有物体数据"""
        if self._send_command_and_wait(52, timeout=timeout):
            return self._all_objects.copy()
        return None

    def get_all_objects(self) -> List[Dict[str, Any]]:
        """获取所有物体数据"""
        return self._all_objects.copy()
    def monitor_object(self, object_id: Any) -> bool:
        """监控指定物体"""
        try:
            # 尝试转换为整数
            object_id_int = int(object_id)
            if object_id_int <= 0:
                self._handle_error(f"无效的物体ID: {object_id}")
                return False
        except (ValueError, TypeError):
            self._handle_error(f"无效的物体ID: {object_id}")
            return False

        self._monitored_objects[object_id_int] = {}
        self.single_monitor_config.enabled = True

        # 立即尝试获取一次数据
        self.fetch_object(object_id_int)

        return self._start_monitoring()    
    

    def unmonitor_object(self, object_id: int) -> None:
        """停止监控指定物体"""
        if object_id in self._monitored_objects:
            del self._monitored_objects[object_id]
            
        # 如果没有监控的物体，禁用单个监控
        if not self._monitored_objects:
            self.single_monitor_config.enabled = False

    def fetch_object(self, object_id: int, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
        """查询指定物体数据"""
        if not isinstance(object_id, int) or object_id <= 0:
            self._handle_error(f"无效的物体ID: {object_id}")
            return None
            
        if self._send_command_and_wait(10, {"object_id": object_id}, timeout):
            return self._monitored_objects.get(object_id, {}).copy()
        return None

    def get_object(self, object_id: int) -> Optional[Dict[str, Any]]:
        """获取指定物体数据"""
        return self._monitored_objects.get(object_id, {}).copy()

    def fetch_self_data(self, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
        """查询自身数据"""
        if self._send_command_and_wait(17, timeout=timeout):
            return self._self_data.copy() if self._self_data else None
        return None

    def get_self_data(self) -> Optional[Dict[str, Any]]:
        """获取自身数据"""
        return self._self_data.copy() if self._self_data else None

    def connect(self) -> bool:
        """连接到DCS服务器"""
        if self.connected:
            return True
            
        try:
            self.connected = self.client.connect()
            return self.connected
        except Exception as e:
            self._handle_error(f"连接服务器失败: {str(e)}")
            return False

    def disconnect(self) -> None:
        """断开连接"""
        self.running = False
        self.client.disconnect()
        self.connected = False
        
        # 清空数据
        self._all_objects = []
        self._monitored_objects = {}
        self._self_data = None
        self._pending_queries = set()
        self._pending_self_query = False


# 使用示例
if __name__ == "__main__":
    # 初始化管理器
    manager = DCSObjectManager(debug=True)
    
    # 设置回调
    def on_objects_updated(objects):
        print(f"物体列表更新: {len(objects)}个物体")
    
    def on_self_updated(self_data):
        print(f"自身数据更新: {self_data.get('Name', '未知')}")
    
    def on_error(message):
        print(f"发生错误: {message}")
    
    manager.set_callback('all_objects', on_objects_updated)
    manager.set_callback('self_data', on_self_updated)
    manager.set_callback('error', on_error)
    
    # 连接服务器
    if not manager.connect():
        print("无法连接到DCS服务器")
        exit(1)
    
    try:
        # 启动监控
        manager.start_monitoring()
        
        # 等待初始数据
        time.sleep(2)
        
        # 获取所有物体
        objects = manager.get_all_objects()
        if objects:
            print(f"找到{len(objects)}个物体")
            
            # 监控第一个物体
            first_id = objects[0].get('id')
            if first_id:
                manager.monitor_object(int(first_id))
                print(f"开始监控物体ID={first_id}")
        
        # 获取自身数据
        self_data = manager.fetch_self_data()
        if self_data:
            print(f"自身名称: {self_data.get('Name', '未知')}")
            
        # 运行一段时间
        print("监控10秒...")
        time.sleep(10)
        
    except KeyboardInterrupt:
        print("用户中断")
    finally:
        manager.disconnect()
        print("已断开连接")