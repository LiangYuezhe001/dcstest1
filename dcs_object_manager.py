import logging
import time
from typing import Dict, Any, Optional, Callable, List
from dcs_client import DCSClient
from dcs_data_parser import DCSDataParser
from dcs_api_parser import DCSAPI


class DCSObjectManager:
    """
    DCS物体管理模块，修复单个物体查询问题
    全部使用单次查询方式
    """
    
    def __init__(self,
                 host: str = "127.0.0.1",
                 port: int = 7790,
                 debug: bool = False):
        """
        初始化物体管理器
        :param host: DCS服务器地址
        :param port: 连接端口
        :param debug: 是否启用调试模式
        """
        # 配置日志
        self.logger = self._setup_logger(debug)
        
        # 核心组件
        self.client = DCSClient(host, port, log_level=logging.WARNING)
        self.parser = DCSDataParser()
        self.debug = debug
        
        # 状态标志
        self.connected = False
        
        # 数据存储
        self._all_objects: List[Dict[str, Any]] = []
        self._cached_objects: Dict[int, Dict[str, Any]] = {}  # 缓存的单个物体数据
        self._self_data: Optional[Dict[str, Any]] = None
        
        # 查询状态
        self._pending_queries: set = set()  # 当前正在查询的物体ID
        self._pending_self_query = False
        
        # 事件回调
        self.callbacks = {
            'all_objects': None,
            'single_object': None,
            'self_data': None,
            'error': None
        }
        
        # 初始化回调关系
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
        try:
            parsed_data = self.parser.parse_data(raw_data)
            self._all_objects = parsed_data
            
            self.logger.debug(f"已更新物体列表，共{len(parsed_data)}个物体")
            
            if self.callbacks['all_objects']:
                self.callbacks['all_objects'](parsed_data)
        except Exception as e:
            self._handle_error(f"批量数据解析失败: {str(e)}")

    def _handle_single_data(self, raw_data: Any) -> None:
        """处理单个物体查询的数据 - 修复ID字段问题"""
        try:
            parsed_data = self.parser.parse_data(raw_data)
            
            if parsed_data and isinstance(parsed_data, list) and len(parsed_data) > 0:
                object_data = parsed_data[0]
                
                # 关键修复: 检查并确保数据中包含ID字段
                if 'id' not in object_data:
                    # 尝试从原始数据中提取ID
                    self.logger.warning("解析的物体数据中没有ID字段，尝试从原始数据中提取")
                    
                    # 如果是字符串数据，尝试解析ID
                    if isinstance(raw_data, str):
                        # 查找ID行
                        id_line = None
                        for line in raw_data.split('\n'):
                            if line.strip().endswith(':') and line.strip()[:-1].isdigit():
                                id_line = line.strip()
                                break
                        
                        if id_line:
                            object_id = int(id_line[:-1])
                            object_data['id'] = object_id
                            self.logger.debug(f"从原始数据中提取ID: {object_id}")
                        else:
                            self.logger.error("无法从原始数据中提取ID")
                            
                            return
                    else:
                        self.logger.error("原始数据不是字符串格式，无法提取ID")
                        return
                
                object_id = object_data.get('id')
                
                if object_id:
                    # 更新缓存的物体数据
                    self._cached_objects[object_id] = object_data
                    
                    # 如果是待处理的查询，标记为已完成
                    if object_id in self._pending_queries:
                        self._pending_queries.discard(object_id)
                    
                    self.logger.debug(f"物体ID={object_id}数据查询完成")
                    
                    if self.callbacks['single_object']:
                        self.callbacks['single_object'](object_data)
                else:
                    self.logger.warning("解析的物体数据中没有ID字段")
                    
        except Exception as e:
            self._handle_error(f"单个物体数据解析失败: {str(e)}")

    def _handle_self_data(self, raw_data: Any) -> None:
        """处理自身数据查询的响应"""
        try:
            parsed_data = self.parser.parse_data(raw_data)
            
            if parsed_data:
                if isinstance(parsed_data, list) and len(parsed_data) > 0:
                    self._self_data = parsed_data[0]
                elif isinstance(parsed_data, dict):
                    self._self_data = parsed_data
                
                self._pending_self_query = False
                self.logger.debug("自身数据查询完成")
                
                if self.callbacks['self_data']:
                    self.callbacks['self_data'](self._self_data)
        except Exception as e:
            self._handle_error(f"自身数据解析失败: {str(e)}")

    def _on_error_received(self, error_type: str, message: str) -> None:
        """处理错误信息"""
        self._handle_error(f"{error_type}: {message}")

    def _handle_error(self, message: str) -> None:
        """错误处理"""
        self.logger.error(message)
        if self.callbacks['error']:
            self.callbacks['error'](message)

    def set_callback(self, event_type: str, callback: Callable) -> None:
        """设置事件回调"""
        if event_type in self.callbacks:
            self.callbacks[event_type] = callback
        else:
            self._handle_error(f"未知的事件类型: {event_type}")

    def fetch_all_objects(self, timeout: float = 10.0) -> Optional[List[Dict[str, Any]]]:
        """查询所有物体数据"""
        if not self.connected:
            self._handle_error("未连接到DCS服务器")
            return None
        
        try:
            # 发送批量查询命令
            self.client.send_command(52)
            
            # 等待结果
            start_time = time.time()
            while time.time() - start_time < timeout:
                # 检查是否有新数据
                if len(self._all_objects) > 0:
                    return self._all_objects.copy()
                time.sleep(0.1)
            
            self._handle_error(f"批量查询超时（{timeout}秒）")
            return None
            
        except Exception as e:
            self._handle_error(f"批量查询失败: {str(e)}")
            return None

    def get_all_objects(self) -> List[Dict[str, Any]]:
        """获取所有物体数据"""
        return self._all_objects.copy()

    def fetch_object(self, object_id: int, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
        """查询指定物体数据"""
        if not isinstance(object_id, int) or object_id <= 0:
            self._handle_error(f"无效的物体ID: {object_id}，必须是正整数")
            return None
            
        if not self.connected:
            self._handle_error("未连接到DCS服务器")
            return None
        
        try:
            # 标记为正在查询
            self._pending_queries.add(object_id)
            
            # 发送单个查询命令
            self.client.send_command(10, {"object_id": object_id})
            
            # 等待结果
            start_time = time.time()
            while time.time() - start_time < timeout:
                # 检查查询是否完成
                if object_id not in self._pending_queries:
                    # 返回缓存的数据
                    return self._cached_objects.get(object_id, {}).copy()
                time.sleep(0.1)
            
            # 超时处理
            self._handle_error(f"查询物体ID={object_id}超时（{timeout}秒）")
            self._pending_queries.discard(object_id)
            return None
            
        except Exception as e:
            self._handle_error(f"查询物体失败: {str(e)}")
            self._pending_queries.discard(object_id)
            return None

    def get_object(self, object_id: int) -> Optional[Dict[str, Any]]:
        """获取缓存的物体数据"""
        return self._cached_objects.get(object_id, {}).copy()

    def fetch_self_data(self, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
        """查询自身数据"""
        if not self.connected:
            self._handle_error("未连接到DCS服务器")
            return None
        
        try:
            # 标记为正在查询
            self._pending_self_query = True
            
            # 发送自身数据查询命令
            self.client.send_command(17)
            
            # 等待结果
            start_time = time.time()
            while time.time() - start_time < timeout:
                # 检查查询是否完成
                if not self._pending_self_query:
                    return self._self_data.copy() if self._self_data else None
                time.sleep(0.1)
            
            # 超时处理
            self._handle_error(f"自身数据查询超时（{timeout}秒）")
            self._pending_self_query = False
            return None
            
        except Exception as e:
            self._handle_error(f"自身数据查询失败: {str(e)}")
            self._pending_self_query = False
            return None

    def get_self_data(self) -> Optional[Dict[str, Any]]:
        """获取缓存的自身数据"""
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
        self.client.disconnect()
        self.connected = False
        
        # 清空数据
        self._all_objects = []
        self._cached_objects = {}
        self._self_data = None
        self._pending_queries = set()
        self._pending_self_query = False


# 调试主函数
if __name__ == "__main__":
    # 初始化管理器
    manager = DCSObjectManager(debug=True)
    
    # 设置回调
    def on_objects_updated(objects):
        print(f"物体列表更新: {len(objects)}个物体")
    
    def on_object_updated(object_data):
        print(f"物体更新: ID={object_data.get('id')}, 名称={object_data.get('Name', '未知')}")
    
    def on_self_updated(self_data):
        print(f"自身数据更新: 名称={self_data.get('Name', '未知')}")
    
    def on_error(message):
        print(f"错误: {message}")
    
    manager.set_callback('all_objects', on_objects_updated)
    manager.set_callback('single_object', on_object_updated)
    manager.set_callback('self_data', on_self_updated)
    manager.set_callback('error', on_error)
    
    # 连接服务器
    print("连接服务器...")
    if not manager.connect():
        print("连接失败")
        exit(1)
    
    try:
        # 测试批量查询
        print("测试批量查询...")
        objects = manager.fetch_all_objects()
        if objects:
            print(f"获取到 {len(objects)} 个物体")
            
            # 显示前几个物体
            for i, obj in enumerate(objects[:5]):
                print(f"{i+1}. ID={obj.get('id')}, 名称={obj.get('Name', '未知')}")
            
            # 测试单个物体查询
            if objects:
                test_id = objects[1].get('id')
                print(objects[1])
                print(f"\n测试单个物体查询: ID={test_id}")
                
                obj_data = manager.fetch_object(test_id)
                if obj_data:
                    print(f"查询成功: 名称={obj_data.get('Name', '未知')}")
                    print(f"位置: {obj_data.get('Position', {})}")
                else:
                    print("查询失败")
                
                # 测试自身数据查询
                print("\n测试自身数据查询...")
                self_data = manager.fetch_self_data()
                if self_data:
                    print(f"自身数据查询成功: 名称={self_data.get('Name', '未知')}")
                    print(f"位置: {self_data.get('Position', {})}")
                else:
                    print("自身数据查询失败")
                
                # 测试获取缓存数据
                print(f"\n测试获取缓存数据: ID={test_id}")
                cached_data = manager.get_object(test_id)
                if cached_data:
                    print(f"缓存数据: 名称={cached_data.get('Name', '未知')}")
                else:
                    print("无缓存数据")
                    
        else:
            print("批量查询失败")
            
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        manager.disconnect()
        print("已断开连接")