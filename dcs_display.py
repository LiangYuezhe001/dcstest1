import time
import pprint
from typing import List, Dict, Any


class DCSDisplayFormatter:
    """DCS数据显示格式化器，负责所有数据展示逻辑"""
    
    def __init__(self, debug=False):
        self.debug = debug
        
        # 国家和联盟映射（可根据需要扩展）
        self.country_mapping = {
            1: "美国", 2: "俄罗斯", 3: "中国", 4: "英国", 5: "法国",
            16: "格鲁吉亚"
        }
        self.coalition_mapping = {1: "友方", 2: "敌方", 3: "中立"}
        
        # 类型映射
        self.type_level4_mapping = {
            47: "C-17A",
            283: "L-39C",
            39: "An-26B"
        }
    
    def display_objects(self, objects: List[Dict[str, Any]], update_interval: float):
        """显示所有物体信息"""
        self._clear_screen()
        self._print_header(update_interval, len(objects))
        self._print_object_table(objects)
        self._print_footer(update_interval)
    
    def _clear_screen(self):
        """清屏操作"""
        print("\033c", end="")
    
    def _print_header(self, update_interval: float, total_objects: int):
        """打印头部信息"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] DCS物体信息显示")
        print(f"总物体数: {total_objects} | 调试模式: {'开启' if self.debug else '关闭'}")
        print("=" * 220)
    
    def _print_object_table(self, objects: List[Dict[str, Any]]):
        """打印物体表格"""
        # 打印表头
        print(f"{'ID':<10} | {'名称':<20} | {'国家':<10} | {'联盟':<10} | "
              f"{'纬度(Lat)':<15} | {'经度(Long)':<15} | {'高度(Alt)':<12} | {'类型':<20}")
        print("-" * 220)
        
        # 打印每行数据
        for obj in objects:
            self._print_object_row(obj)
    
    def _print_object_row(self, obj: Dict[str, Any]):
        """打印单个物体行"""
        obj_id = obj.get("id", "未知ID")
        name = self._get_object_name(obj)
        country = self._get_country_name(obj.get('Country'))
        coalition = self._get_coalition_name(obj.get('Coalition'), obj.get('CoalitionID'))
        
        pos = self._get_position_info(obj)
        lat, lon, alt = pos["lat"], pos["lon"], pos["alt"]
        
        # 格式化位置数据
        lat = self._format_coordinate(lat)
        lon = self._format_coordinate(lon)
        alt = self._format_altitude(alt)
        
        obj_type = self._get_type_info(obj)
        
        # 打印行
        print(f"{obj_id:<10} | {self._truncate_text(name, 20):<20} | "
              f"{country:<10} | {coalition:<10} | {lat:<15} | {lon:<15} | {alt:<12} | "
              f"{self._truncate_text(obj_type, 20):<20}")
    
    def _print_footer(self, update_interval: float):
        """打印底部信息"""
        print("\n" + "=" * 220)
        print(f"按 Ctrl+C 停止 | 下次更新: {update_interval}秒后")
    
    def print_debug_info(self, raw_data: str, parsed_objects: List[Dict[str, Any]]):
        """打印调试信息"""
        if not self.debug:
            return
            
        print("\n[原始数据]")
        print(raw_data[:500] + "...")
        
        print("\n[解析后的数组]")
        pprint.pprint(parsed_objects, indent=2, width=120)
        
        if parsed_objects:
            first_obj = parsed_objects[0]
            print("\n[调试信息]")
            print(f"首个物体结构: {list(first_obj.keys())}")
            print(f"ID字段: {first_obj.get('id')}, 名称字段: {first_obj.get('Name')}")
    
    # 辅助方法：获取位置信息
    def _get_position_info(self, obj_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "lat": obj_data.get("Lat", "未找到"),
            "lon": obj_data.get("Long", "未找到"),
            "alt": obj_data.get("Alt", "未找到")
        }
    
    # 辅助方法：获取类型信息
    def _get_type_info(self, obj_data: Dict[str, Any]) -> str:
        level4 = obj_data.get("level4", "未知ID")
        return self.type_level4_mapping.get(level4, f"类型ID:{level4}")
    
    # 辅助方法：获取物体名称
    def _get_object_name(self, obj_data: Dict[str, Any]) -> str:
        name_fields = ['Name', 'GroupName', 'UnitName']
        for field in name_fields:
            if field in obj_data and obj_data[field]:
                return str(obj_data[field])
        return "未知名称"
    
    # 辅助方法：格式化坐标
    def _format_coordinate(self, value: Any) -> str:
        if isinstance(value, (int, float)):
            return f"{value:.6f}"
        return str(value)
    
    # 辅助方法：格式化高度
    def _format_altitude(self, value: Any) -> str:
        if isinstance(value, (int, float)):
            return f"{value:.1f}m"
        return str(value)
    
    # 辅助方法：截断过长文本
    def _truncate_text(self, text: str, max_length: int) -> str:
        if len(text) > max_length:
            return text[:max_length-3] + "..."
        return text
    
    # 辅助方法：获取国家名称
    def _get_country_name(self, country_code):
        if isinstance(country_code, int):
            return self.country_mapping.get(country_code, f"代码:{country_code}")
        return country_code or "未知"
    
    # 辅助方法：获取联盟名称
    def _get_coalition_name(self, coalition_info, coalition_id):
        if coalition_info:
            return coalition_info
        if isinstance(coalition_id, int):
            return self.coalition_mapping.get(coalition_id, f"ID:{coalition_id}")
        return "未知"
