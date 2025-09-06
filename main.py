import time
import sys
from typing import Dict, Any, List, Tuple
from dcs_object_manager import DCSObjectManager
from distance_calculator import DistanceCalculator


def print_separator():
    """打印分隔线，增强输出可读性"""
    print("\n" + "="*60)


def format_position(pos: Dict[str, Any]) -> str:
    """格式化位置信息以便显示"""
    if not isinstance(pos, dict):
        return "位置数据无效"
    
    return (f"X: {pos.get('x', '未知'):.2f}, "
            f"Y: {pos.get('y', '未知'):.2f}, "
            f"Z: {pos.get('z', '未知'):.2f}")


def format_latlong(latlong: Dict[str, Any]) -> str:
    """格式化经纬度信息以便显示"""
    if not isinstance(latlong, dict):
        return "经纬度数据无效"
    
    return (f"纬度: {latlong.get('Lat', '未知'):.6f}, "
            f"经度: {latlong.get('Long', '未知'):.6f}, "
            f"高度: {latlong.get('Alt', '未知'):.2f}")


class DCSTracker:
    """DCS物体跟踪器，支持计算两机之间的距离和相对速度"""
    
    def __init__(self):
        # 初始化管理器
        self.manager = DCSObjectManager(debug=False)
        
        # 跟踪状态
        self.selected_id = None
        self.selected_name = None
        
        # 用于计算速度的历史数据
        self.prev_positions = {
            'target': None,
            'self': None,
            'timestamp': None
        }
        
        # 距离计算器实例
        self.distance_calculator = DistanceCalculator()
    
    def connect(self, host: str = "127.0.0.1", port: int = 7790) -> bool:
        """连接到DCS服务器"""
        print("连接到DCS服务器...")
        return self.manager.connect()
    
    def fetch_all_objects(self) -> List[Dict[str, Any]]:
        """获取所有物体信息"""
        print_separator()
        print("获取所有物体信息...")
        all_objects = self.manager.fetch_all_objects(timeout=15.0)
        
        if not all_objects or not isinstance(all_objects, list):
            return []
        
        # 筛选出有ID和名称的有效物体
        return [
            obj for obj in all_objects 
            if isinstance(obj, dict) and 'id' in obj and 'Name' in obj
        ]
    
    def select_object(self, valid_objects: List[Dict[str, Any]]) -> bool:
        """让用户选择要跟踪的物体"""
        if not valid_objects:
            return False
        
        print_separator()
        print("发现以下可跟踪物体：")
        for i, obj in enumerate(valid_objects, 1):
            print(f"{i}. ID: {obj['id']}, 名称: {obj['Name']}")
        
        # 获取用户选择
        while True:
            try:
                choice = input("\n请输入要跟踪的物体编号 (输入0退出): ")
                choice_idx = int(choice)
                
                if choice_idx == 0:
                    print("程序退出")
                    return False
                
                if 1 <= choice_idx <= len(valid_objects):
                    selected_obj = valid_objects[choice_idx - 1]
                    self.selected_id = selected_obj['id']
                    self.selected_name = selected_obj['Name']
                    print(f"已选择跟踪: ID={self.selected_id}, 名称={self.selected_name}")
                    return True
                else:
                    print(f"请输入1到{len(valid_objects)}之间的数字")
            except ValueError:
                print("请输入有效的数字")
    
    def calculate_relative_speed(self, current_positions: Dict[str, Dict[str, Any]]) -> Tuple[float, float]:
        """
        计算两机之间的相对速度
        
        参数:
            current_positions: 包含目标和自身当前位置的字典
            
        返回:
            相对速度元组 (三维空间相对速度, 水平相对速度)
        """
        # 获取当前时间戳
        current_time = time.time()
        
        # 如果没有历史数据，初始化并返回0速度
        if not self.prev_positions['timestamp']:
            self.prev_positions = {
                'target': current_positions['target'],
                'self': current_positions['self'],
                'timestamp': current_time
            }
            return (0.0, 0.0)
        
        # 计算时间差
        time_diff = current_time - self.prev_positions['timestamp']
        if time_diff <= 0:
            return (0.0, 0.0)
        
        # 计算三维空间中的相对位移
        distance_3d = self.distance_calculator.calculate_3d_distance(
            current_positions['target'], 
            self.prev_positions['target']
        )
        
        # 计算水平面上的相对位移
        distance_horizontal = self.distance_calculator.calculate_horizontal_distance(
            current_positions['target'], 
            self.prev_positions['target']
        )
        
        # 计算相对自身的位移（目标位移减去自身位移）
        self_distance_3d = self.distance_calculator.calculate_3d_distance(
            current_positions['self'], 
            self.prev_positions['self']
        )
        
        relative_distance_3d = abs(distance_3d - self_distance_3d)
        
        # 计算速度 (距离/时间)
        speed_3d = relative_distance_3d / time_diff
        speed_horizontal = distance_horizontal / time_diff
        
        # 更新历史数据
        self.prev_positions = {
            'target': current_positions['target'],
            'self': current_positions['self'],
            'timestamp': current_time
        }
        
        return (speed_3d, speed_horizontal)
    
    def start_monitoring(self, update_interval: float = 2.0):
        """开始监控选定物体和自身信息，并计算距离和相对速度"""
        if not self.selected_id:
            print("未选择要跟踪的物体")
            return
        
        # 存储最新的位置数据
        latest_positions = {
            'target': None,
            'self': None
        }
        
        # 显示监控数据的回调函数
        def on_object_updated(data: Dict[str, Any]):
            if isinstance(data, dict) and data.get('id') == self.selected_id:
                latest_positions['target'] = data.get('Position', {})
                print_separator()
                print(f"[物体更新] ID: {data.get('id')}, 名称: {data.get('Name', '未知')}")
                print(f"  位置: {format_position(data.get('Position', {}))}")
                print(f"  经纬度: {format_latlong(data.get('LatLongAlt', {}))}")
                print(f"  航向: {data.get('Heading', '未知'):.4f}")
                print(f"  俯仰角: {data.get('Pitch', '未知'):.4f}")
                print(f"  坡度: {data.get('Bank', '未知'):.4f}")
                
                # 如果已有自身位置数据，计算距离
                if latest_positions['self']:
                    distance_3d = self.distance_calculator.calculate_3d_distance(
                        latest_positions['target'], 
                        latest_positions['self']
                    )
                    distance_horizontal = self.distance_calculator.calculate_horizontal_distance(
                        latest_positions['target'], 
                        latest_positions['self']
                    )
                    distance_vertical = self.distance_calculator.calculate_vertical_distance(
                        latest_positions['target'], 
                        latest_positions['self']
                    )
                    
                    print(f"  与本机距离: 直线={distance_3d:.2f}, 水平={distance_horizontal:.2f}, 垂直={distance_vertical:.2f}")
        
        def on_self_updated(data: Dict[str, Any]):
            if isinstance(data, dict):
                latest_positions['self'] = data.get('Position', {})
                print_separator()
                print(f"[自身更新] 名称: {data.get('Name', '未知')}")
                print(f"  位置: {format_position(data.get('Position', {}))}")
                print(f"  经纬度: {format_latlong(data.get('LatLongAlt', {}))}")
                print(f"  航向: {data.get('Heading', '未知'):.4f}")
                print(f"  速度: {data.get('Velocity', '未知')}")
                
                # 如果已有目标位置数据，计算相对速度
                if latest_positions['target']:
                    # 计算相对速度
                    speed_3d, speed_horizontal = self.calculate_relative_speed(latest_positions)
                    print(f"  相对目标速度: 三维={speed_3d:.2f}/s, 水平={speed_horizontal:.2f}/s")
        
        def on_error(message: str):
            print_separator()
            print(f"[错误] {message}")
        
        # 设置回调
        self.manager.set_callback('single_object', on_object_updated)
        self.manager.set_callback('self_data', on_self_updated)
        self.manager.set_callback('error', on_error)
        
        # 启动监控
        print_separator()
        print("启动监控系统...")
        print("正在获取初始数据...")
        print("(按Ctrl+C停止监控)")
        
        # 先获取一次初始数据
        self.manager.fetch_object(self.selected_id)
        self.manager.fetch_self_data()
        time.sleep(1)
        
        # 持续监控
        try:
            while True:
                # 查询选定物体
                self.manager.fetch_object(self.selected_id)
                
                # 查询自身信息
                self.manager.fetch_self_data()
                
                # 等待下一次更新
                time.sleep(update_interval)
        except KeyboardInterrupt:
            print("\n用户中断监控")
    
    def disconnect(self):
        """断开与服务器的连接"""
        self.manager.disconnect()
        print_separator()
        print("已断开与服务器的连接，程序退出")


def main():
    tracker = DCSTracker()
    
    try:
        # 连接服务器
        if not tracker.connect():
            print("连接失败，程序退出")
            return
        
        # 获取所有物体
        valid_objects = tracker.fetch_all_objects()
        if not valid_objects:
            print("未找到有效的物体数据，程序退出")
            return
        
        # 选择跟踪物体
        if not tracker.select_object(valid_objects):
            return
        
        # 开始监控
        tracker.start_monitoring(update_interval=0.1)
    
    except Exception as e:
        print(f"发生错误: {str(e)}")
    finally:
        tracker.disconnect()


if __name__ == "__main__":
    main()
