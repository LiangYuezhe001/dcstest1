import time
import os
import threading
from typing import Any, Optional  # 从typing模块导入必要的类型提示
from dcs_object_manager import DCSObjectManager


def clear_screen():
    """跨平台清屏函数"""
   # os.system('cls' if os.name == 'nt' else 'clear')


def print_monitoring_data(manager: DCSObjectManager, target_id: int):
    """打印监控数据的函数"""
    try:
        while True:
            clear_screen()
            print("="*60)
            print(f"正在监控 - 物体ID: {target_id} | 按Ctrl+C停止监控")
            print("="*60)
            
            # 获取并显示选定物体信息
            print("\n【跟踪物体信息】")
            target_data = manager.get_monitored_object(target_id)
            if target_data:
                print(f"ID: {target_data.get('id', '未知')}")
                print(f"名称: {target_data.get('Name', '未知')}")
                print(f"类型: {target_data.get('Type', '未知')}")
                
                position = target_data.get('Position', {})
                print(f"坐标: X={position.get('x', 0):.2f}, Y={position.get('y', 0):.2f}, Z={position.get('z', 0):.2f}")
                
                latlong = target_data.get('LatLongAlt', {})
                print(f"经纬度: 纬度={latlong.get('Lat', 0):.6f}, 经度={latlong.get('Long', 0):.6f}")
                print(f"高度: {latlong.get('Alt', 0):.2f}米")
            else:
                print("等待物体数据加载...")
            
            # 获取并显示自身信息
            print("\n【自身信息】")
            self_data = manager.get_self_data()
            if self_data:
                print(f"ID: {self_data.get('id', '未知')}")
                print(f"名称: {self_data.get('Name', '未知')}")
                print(f"类型: {self_data.get('Type', '未知')}")
                
                position = self_data.get('Position', {})
                print(f"坐标: X={position.get('x', 0):.2f}, Y={position.get('y', 0):.2f}, Z={position.get('z', 0):.2f}")
                
                latlong = self_data.get('LatLongAlt', {})
                print(f"经纬度: 纬度={latlong.get('Lat', 0):.6f}, 经度={latlong.get('Long', 0):.6f}")
                print(f"高度: {latlong.get('Alt', 0):.2f}米")
            else:
                print("等待自身数据加载...")
            
            print("\n" + "="*60)
            print(f"数据更新时间: {time.strftime('%H:%M:%S')}")
            print("按Ctrl+C退出监控")
            
            time.sleep(1)  # 每秒刷新一次显示
    except KeyboardInterrupt:
        print("\n监控已停止")


def is_valid_object_id(obj_id: Any) -> bool:
    """验证物体ID是否为有效的正整数"""
    if obj_id is None:
        return False
    # 处理字符串形式的数字（如"123"）
    if isinstance(obj_id, str):
        return obj_id.isdigit()
    # 处理整数类型
    if isinstance(obj_id, int):
        return obj_id > 0
    # 其他类型（如float但实际是整数，如123.0）
    if isinstance(obj_id, float):
        return obj_id.is_integer() and obj_id > 0
    return False


def convert_to_int_id(obj_id: Any) -> Optional[int]:
    """将有效格式的ID转换为整数类型"""
    if not is_valid_object_id(obj_id):
        return None
    try:
        return int(obj_id)
    except (ValueError, TypeError):
        return None


def main():
    # 初始化管理器
    print("初始化DCS物体管理器...")
    manager = DCSObjectManager(
        batch_update_interval=5.0,
        single_update_interval=1.0,
        self_update_interval=1.0,
        debug=True
    )
    
    # 连接到服务器
    print("连接到DCS服务器...")
    if not manager.connect():
        print("无法连接到DCS服务器，程序将退出")
        return
    
    try:
        # 单次获取所有物体的ID和名称
        print("获取所有物体信息...")
        all_objects = manager.fetch_all_objects(timeout=15.0)
        
        if not all_objects or len(all_objects) == 0:
            print("未能获取到物体数据，程序将退出")
            return
        
        # 筛选并收集有效的物体ID（确保是正整数）
        valid_objects = []
        object_ids = []
        for obj in all_objects:
            obj_id = obj.get('id')
            # 严格验证ID格式
            if is_valid_object_id(obj_id):
                int_id = convert_to_int_id(obj_id)
                if int_id is not None:
                    valid_objects.append({
                        'id': int_id,
                        'Name': obj.get('Name', '未知名称')
                    })
                    object_ids.append(int_id)
        
        # 检查是否有有效物体
        if not valid_objects:
            print("未发现有效的物体ID，程序将退出")
            return
        
        # 显示所有有效物体的ID和名称
        clear_screen()
        print("="*60)
        print("找到的所有有效物体:")
        print("="*60)
        print(f"{'ID':<10} | 名称")
        print("-"*60)
        for obj in valid_objects:
            print(f"{str(obj['id']):<10} | {obj['Name']}")
        
        # 让用户选择要跟踪的物体ID（增强版验证）
        print("\n" + "="*60)
        target_id = None
        while target_id is None:
            try:
                user_input = input("请输入要跟踪的物体ID（正整数）: ")
                # 检查输入是否为空
                if not user_input.strip():
                    print("ID不能为空，请重新输入")
                    continue
                
                # 尝试转换为整数
                target_id = int(user_input.strip())
                
                # 检查是否为正整数
                if target_id <= 0:
                    print("ID必须是正整数，请重新输入")
                    target_id = None
                    continue
                
                # 检查是否在有效ID列表中
                if target_id not in object_ids:
                    print(f"无效的ID: {target_id}，请从上面的列表中选择一个ID")
                    print(f"ID列表： {object_ids},0")
                    target_id = None
            
            except ValueError:
                print("输入无效，请输入一个有效的正整数ID")
        
        # 启动监控
        print(f"\n开始监控物体ID: {target_id} 和自身信息...")
        manager.add_object_monitoring(int(target_id))
        manager.start_self_monitoring()
        
        # 等待初始数据加载
        print("等待初始数据加载...")
        time.sleep(2)
        
        # 启动监控显示线程
        monitoring_thread = threading.Thread(
            target=print_monitoring_data,
            args=(manager, target_id),
            daemon=True
        )
        monitoring_thread.start()
        
        # 等待用户中断
        monitoring_thread.join()
        
    except KeyboardInterrupt:
        print("\n用户中断操作")
    finally:
        print("正在清理资源...")
        manager.disconnect()
        print("程序已退出")


if __name__ == "__main__":
    main()
