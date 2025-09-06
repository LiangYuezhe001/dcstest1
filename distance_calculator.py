from typing import Dict, Any, Tuple
import math


class DistanceCalculator:
    """距离计算器，提供三维空间中两点之间的距离和相对速度计算"""
    
    @staticmethod
    def get_position_coords(position: Dict[str, Any]) -> Tuple[float, float, float]:
        """
        从位置字典中提取坐标值
        
        参数:
            position: 包含x, y, z坐标的字典
            
        返回:
            包含x, y, z坐标的元组，默认值为0.0
        """
        if not isinstance(position, dict):
            return (0.0, 0.0, 0.0)
            
        return (
            float(position.get('x', 0.0)),
            float(position.get('y', 0.0)),
            float(position.get('z', 0.0))
        )
    
    @staticmethod
    def calculate_3d_distance(pos1: Dict[str, Any], pos2: Dict[str, Any]) -> float:
        """
        计算三维空间中两点之间的直线距离
        
        参数:
            pos1: 第一个点的位置字典
            pos2: 第二个点的位置字典
            
        返回:
            两点之间的距离，单位与输入坐标一致
        """
        x1, y1, z1 = DistanceCalculator.get_position_coords(pos1)
        x2, y2, z2 = DistanceCalculator.get_position_coords(pos2)
        
        # 三维空间距离公式: √[(x2-x1)² + (y2-y1)² + (z2-z1)²]
        distance = math.sqrt(
            (x2 - x1) **2 +
            (y2 - y1)** 2 +
            (z2 - z1) **2
        )
        
        return distance
    
    @staticmethod
    def calculate_horizontal_distance(pos1: Dict[str, Any], pos2: Dict[str, Any]) -> float:
        """
        计算水平面上两点之间的距离（忽略高度）
        
        参数:
            pos1: 第一个点的位置字典
            pos2: 第二个点的位置字典
            
        返回:
            水平距离，单位与输入坐标一致
        """
        x1, y1, _ = DistanceCalculator.get_position_coords(pos1)
        x2, y2, _ = DistanceCalculator.get_position_coords(pos2)
        
        # 二维平面距离公式: √[(x2-x1)² + (y2-y1)²]
        distance = math.sqrt(
            (x2 - x1)** 2 +
            (y2 - y1) **2
        )
        
        return distance
    
    @staticmethod
    def calculate_vertical_distance(pos1: Dict[str, Any], pos2: Dict[str, Any]) -> float:
        """
        计算两点之间的垂直距离（高度差）
        
        参数:
            pos1: 第一个点的位置字典
            pos2: 第二个点的位置字典
            
        返回:
            垂直距离，单位与输入坐标一致
        """
        _, _, z1 = DistanceCalculator.get_position_coords(pos1)
        _, _, z2 = DistanceCalculator.get_position_coords(pos2)
        
        return abs(z2 - z1)
