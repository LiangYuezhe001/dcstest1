import time
import sys
import datetime  # 新增导入
import csv
from typing import Dict, Any, List, Tuple
from dcs_object_manager import DCSObjectManager
from distance_calculator import DistanceCalculator


class DCSTracker:
    """简化的DCS物体跟踪器，优化响应速度并添加数据记录"""
    
    def __init__(self, log_file: str = "dcs_data.csv"):
        self.manager = DCSObjectManager(debug=False)
        self.selected_id = None
        self.selected_name = None
        self.distance_calculator = DistanceCalculator()
        self.log_file = log_file
        self._init_log_file()  # 初始化日志文件
    
    def _init_log_file(self):
        """初始化CSV日志文件表头"""
        with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'object_id', 'object_name',
                'x', 'y', 'z',  # 位置数据
                'heading', 'pitch', 'bank',  # 方向数据
                'self_x', 'self_y', 'self_z',  # 自身位置
                'distance_3d'  # 三维距离
            ])
    
    def _get_timestamp(self) -> str:
        """获取格式化时间戳（包含毫秒）"""
        # 使用datetime模块，%f是微秒，[:-3]截取前三位作为毫秒
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    def connect(self, host: str = "127.0.0.1", port: int = 7790) -> bool:
        """连接到DCS服务器"""
        print(f"[{self._get_timestamp()}] 连接到 {host}:{port}...")
        return self.manager.connect()
    
    def fetch_all_objects(self) -> List[Dict[str, Any]]:
        """获取所有有效物体信息"""
        print(f"[{self._get_timestamp()}] 获取物体列表...")
        all_objects = self.manager.fetch_all_objects(timeout=5.0)
        return [
            obj for obj in (all_objects or [])
            if isinstance(obj, dict) and 'id' in obj and 'Name' in obj
        ]
    
    def select_object(self, valid_objects: List[Dict[str, Any]]) -> bool:
        """简化的物体选择流程"""
        if not valid_objects:
            return False
            
        print("\n可跟踪物体:")
        for i, obj in enumerate(valid_objects[:10], 1):  # 限制显示数量加快响应
            print(f"{i}. ID: {obj['id']}, 名称: {obj['Name']}")
        
        try:
            choice = input("\n请输入跟踪编号 (0退出): ")
            choice_idx = int(choice)
            if choice_idx == 0:
                return False
            if 1 <= choice_idx <= len(valid_objects):
                selected = valid_objects[choice_idx - 1]
                self.selected_id = selected['id']
                self.selected_name = selected['Name']
                print(f"已选择: {self.selected_name} (ID: {self.selected_id})")
                return True
        except ValueError:
            pass
        return False
    
    def start_monitoring(self, update_interval: float = 0.1):
        """简化监控流程，优化响应速度"""
        if not self.selected_id:
            print("未选择跟踪物体")
            return
        
        latest_data = {
            'target': {'Position': {}, 'Heading': 0, 'Pitch': 0, 'Bank': 0},
            'self': {'Position': {}}
        }
        
        # 简化回调函数
        def on_object_updated(data: Dict[str, Any]):
            if data.get('id') == self.selected_id:
                latest_data['target'] = data
                self._log_data(latest_data)  # 记录数据
                # 简洁输出
                ts = self._get_timestamp()
                pos = data.get('Position', {})
                print(f"[{ts}] 目标: {pos.get('x',0):.1f},{pos.get('y',0):.1f},{pos.get('z',0):.1f} "
                      f"方向: H={data.get('Heading',0):.1f}, P={data.get('Pitch',0):.1f}")
        
        def on_self_updated(data: Dict[str, Any]):
            latest_data['self'] = data
        
        def on_error(message: str):
            print(f"[{self._get_timestamp()}] 错误: {message}")
        
        # 设置回调
        self.manager.set_callback('single_object', on_object_updated)
        self.manager.set_callback('self_data', on_self_updated)
        self.manager.set_callback('error', on_error)
        
        print(f"[{self._get_timestamp()}] 开始监控 (间隔: {update_interval}s)")
        try:
            while True:
                self.manager.fetch_object(self.selected_id)
                self.manager.fetch_self_data()
                time.sleep(update_interval)
        except KeyboardInterrupt:
            print("\n监控已停止")
    
    def _log_data(self, data: Dict[str, Any]):
        """将数据写入CSV文件"""
        target = data['target']
        self_data = data['self']
        pos = target.get('Position', {})
        self_pos = self_data.get('Position', {})
        
        # 计算三维距离
        distance = self.distance_calculator.calculate_3d_distance(
            pos, self_pos
        )
        
        # 写入数据
        with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                self._get_timestamp(),
                self.selected_id,
                self.selected_name,
                self_pos.get('x', ''),
                self_pos.get('y', ''),
                self_pos.get('z', ''),
                self_data.get('Heading', ''),
                self_data.get('Pitch', ''),
                self_data.get('Bank', ''),
                self_pos.get('x', ''),
                self_pos.get('y', ''),
                self_pos.get('z', ''),
                f"{distance:.2f}"
            ])
    
    def disconnect(self):
        """断开连接"""
        self.manager.disconnect()
        print(f"[{self._get_timestamp()}] 已断开连接")


def main():
    tracker = DCSTracker()
    try:
        if not tracker.connect():
            print("连接失败")
            return
        
        valid_objects = tracker.fetch_all_objects()
        if not valid_objects:
            print("未找到有效物体")
            return
        
        if not tracker.select_object(valid_objects):
            return
        
        tracker.start_monitoring(update_interval=0.1)  # 0.1秒间隔提升响应速度
    
    finally:
        tracker.disconnect()


if __name__ == "__main__":
    main()