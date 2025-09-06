import time
import os
from typing import List, Dict, Any


class DCSDisplay:
    """显示模块，负责所有数据展示逻辑"""
    
    def __init__(self):
        # 国家和联盟映射表
        self.country_mapping = {
            1: "美国", 2: "俄罗斯", 3: "中国", 4: "英国", 5: "法国",
            16: "格鲁吉亚"
        }
        self.coalition_mapping = {1: "友方", 2: "敌方", 3: "中立"}

    def clear_screen(self) -> None:
        """跨平台清屏函数"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def format_type_info(self, type_dict: Any) -> str:
        """格式化显示Type信息（处理字典类型）"""
        if isinstance(type_dict, dict):
            # 提取关键级别信息 - 修复了此处的换行导致的字符串问题
            levels = [f"level{i}:{type_dict.get(f'level{i}', '?')}" for i in range(1, 5) if f'level{i}' in type_dict]
            return ", ".join(levels) if levels else "未知类型"
        return str(type_dict)[:15]  # 限制长度

    def show_object_list(self, objects: List[Dict[str, Any]]) -> None:
        """格式化显示物体列表（仅展示关键信息）"""
        if not objects:
            print("未获取到物体数据")
            return
        
        # 打印表头
        print("\n" + "="*80)
        print(f"{'ID':<12} | {'名称':<20} | {'国家':<10} | {'类型':<25} | 位置概要")
        print("-"*80)
        
        # 打印物体列表
        for obj in objects:
            obj_id = obj.get('id', '未知')
            name = str(obj.get('Name', '未知'))[:20]  # 限制长度
            country = self._get_country_name(obj.get('Country', '未知'))
            obj_type = self.format_type_info(obj.get('Type', '未知'))
            position = obj.get('Position', {})
            pos_summary = f"X:{position.get('x', 0):.1f}, Y:{position.get('y', 0):.1f}"
            
            print(f"{obj_id:<12} | {name:<20} | {country:<10} | {obj_type:<25} | {pos_summary}")
        
        print("="*80 + "\n")

    def show_tracking_info(self, obj_data: Dict[str, Any], target_id: int) -> None:
        """显示跟踪物体的详细信息"""
        # 清屏（跨平台兼容）
        self.clear_screen()
        print(f"===== 物体跟踪 (ID={target_id}) =====")
        print(f"名称: {obj_data.get('Name', '未知')}")
        print(f"国家: {self._get_country_name(obj_data.get('Country', '未知'))}")
        print(f"联盟: {self._get_coalition_name(obj_data.get('Coalition', '未知'), obj_data.get('CoalitionID'))}")
        print(f"类型: {self.format_type_info(obj_data.get('Type', '未知'))}")
        
        # 位置信息
        pos = obj_data.get('Position', {})
        print(f"坐标: X={pos.get('x', 0):.2f}, Y={pos.get('y', 0):.2f}, Z={pos.get('z', 0):.2f}")
        
        # 经纬度信息
        latlong = obj_data.get('LatLongAlt', {})
        print(f"经纬度: 纬度={latlong.get('Lat', 0):.6f}, 经度={latlong.get('Long', 0):.6f}")
        print(f"高度: {latlong.get('Alt', 0):.2f}米")
        
        # 姿态信息
        print(f"俯仰角: {obj_data.get('Pitch', 0):.6f}")
        print(f"横滚角: {obj_data.get('Bank', 0):.6f}")
        print(f"航向角: {obj_data.get('Heading', 0):.6f}")
        
        # 速度信息
        velocity = obj_data.get('Velocity', [0, 0, 0])
        if isinstance(velocity, list) and len(velocity) >= 3:
            print(f"速度: X={velocity[0]:.2f}, Y={velocity[1]:.2f}, Z={velocity[2]:.2f}")
        
        print(f"\n上次更新: {time.strftime('%H:%M:%S')}")
        print("-------------------------------------")
        print("按Ctrl+C返回物体列表")

    # 状态提示信息
    def show_connecting_message(self) -> None:
        """显示连接中消息"""
        print("连接到DCS服务器并获取所有物体...")

    def show_connection_failed(self) -> None:
        """显示连接失败消息"""
        print("连接失败，退出程序")

    def show_waiting_for_data(self) -> None:
        """显示等待数据加载消息"""
        print("等待物体数据加载（最多30秒）...")

    def show_waiting_progress(self, seconds: int) -> None:
        """显示等待进度"""
        print(f"已等待 {seconds} 秒...")

    def show_no_data_error(self) -> None:
        """显示无数据错误"""
        print("未能获取到物体数据，程序将退出")

    def show_object_summary(self, total: int, object_ids: List[int]) -> None:
        """显示物体汇总信息"""
        print(f"共发现 {total} 个物体：")
        print(f"可用物体ID: {', '.join(map(str, object_ids[:10]))}{'...' if len(object_ids) > 10 else ''}")

    def show_tracking_start(self, target_id: int) -> None:
        """显示跟踪开始消息"""
        print(f"\n开始跟踪物体ID={target_id}（按Ctrl+C停止跟踪）")

    def show_tracking_stop(self) -> None:
        """显示跟踪停止消息"""
        print("\n已停止跟踪")

    def show_tracking_error(self, target_id: int) -> None:
        """显示跟踪错误消息"""
        print(f"无法获取物体ID={target_id}的最新数据，将重试...")

    def show_tracking_exception(self, e: Exception) -> None:
        """显示跟踪异常消息"""
        print(f"跟踪过程中发生错误: {str(e)}")

    def show_invalid_input(self) -> None:
        """显示无效输入消息"""
        print("请输入有效的ID")

    def show_id_not_found(self, target_id: int, object_ids: List[int]) -> None:
        """显示ID未找到消息"""
        print(f"未找到ID={target_id}的物体，请重新输入")
        print(f"可用物体ID: {', '.join(map(str, object_ids[:10]))}{'...' if len(object_ids) > 10 else ''}")

    def show_invalid_number(self) -> None:
        """显示无效数字消息"""
        print("请输入有效的数字ID")

    def show_operation_error(self, e: Exception) -> None:
        """显示操作错误消息"""
        print(f"操作出错: {str(e)}")

    def show_user_interrupt(self) -> None:
        """显示用户中断消息"""
        print("\n用户中断操作")

    def show_program_exit(self) -> None:
        """显示程序退出消息"""
        print("程序已退出")

    # 辅助方法
    def _get_country_name(self, country_code: Any) -> str:
        """获取国家名称（带映射）"""
        if isinstance(country_code, int):
            return self.country_mapping.get(country_code, f"代码:{country_code}")
        return str(country_code) if country_code else "未知"

    def _get_coalition_name(self, coalition_info: Any, coalition_id: Any) -> str:
        """获取联盟名称（带映射）"""
        if coalition_info:
            return str(coalition_info)
        if isinstance(coalition_id, int):
            return self.coalition_mapping.get(coalition_id, f"ID:{coalition_id}")
        return "未知"
