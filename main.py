import time
import sys
from typing import List, Tuple

def main():
    # 尝试导入DCSObjectManager
    try:
        from dcs_object_manager import DCSObjectManager
    except ImportError:
        print("错误: 无法导入DCSObjectManager模块")
        return

    # 创建管理器实例
    print("初始化DCS物体管理器...")
    manager = DCSObjectManager(
        batch_update_interval=10.0,
        single_update_interval=1.0,
        self_update_interval=1.0,
        debug=False
    )
    
    # 存储用户选择的物体ID
    selected_object_id = None

    # 回调函数定义
    def on_single_object_updated(data: dict):
        """处理单个物体更新事件"""
        obj_id = data.get('id')
        obj_name = data.get('Name', '未知名称')
        
        print(f"\n[物体更新] ID: {obj_id} ({obj_name})")
        position = data.get('Position', {})
        print(f"  位置: X={position.get('x', 0):.2f}, Y={position.get('y', 0):.2f}, Z={position.get('z', 0):.2f}")
        
        # 可以添加更多需要显示的物体属性

    def on_self_data_updated(data: dict):
        """处理自身数据更新事件"""
        name = data.get('Name', '未知')
        print(f"\n[自身更新] {name}")
        
        lat_long = data.get('LatLongAlt', {})
        print(f"  经纬度: 纬度={lat_long.get('Lat', 0):.6f}, 经度={lat_long.get('Long', 0):.6f}")
        
        # 可以添加更多需要显示的自身属性

    def on_error(message: str):
        """处理错误事件"""
        print(f"\n[错误] {message}")

    # 设置回调
    manager.set_callback('single_object', on_single_object_updated)
    manager.set_callback('self_data', on_self_data_updated)
    manager.set_callback('error', on_error)
    
    # 连接到服务器
    print("尝试连接到DCS服务器...")
    if not manager.connect():
        print("无法连接到DCS服务器，程序退出")
        return
    
    try:
        # 1. 单次获取所有物体的ID和名称
        print("\n正在获取所有物体信息...")
        all_objects = manager.fetch_all_objects(timeout=15.0)
        
        if not all_objects:
            print("未能获取到物体信息，程序退出")
            return
        
        # 过滤出有ID的有效物体
        valid_objects: List[Tuple[int, str]] = []
        for obj in all_objects:
            obj_id = obj.get('id')
            obj_name = obj.get('Name', '未知名称')
            if isinstance(obj_id, int) and obj_id > 0:
                valid_objects.append((obj_id, obj_name))
        
        if not valid_objects:
            print("没有找到有效的物体，程序退出")
            return
        
        # 显示所有物体供用户选择
        print(f"\n共发现 {len(valid_objects)} 个物体:")
        print("-" * 50)
        for i, (obj_id, obj_name) in enumerate(valid_objects, 1):
            # 每5个物体显示一行，提高可读性
            print(f"ID: {obj_id:<6} 名称: {obj_name[:20]:<20}", end="  |  " if i % 5 != 0 else "\n")
        print("\n" + "-" * 50)
        
        # 2. 用户选择要跟踪的物体
        print("\n请选择要跟踪的物体:")
        while True:
            try:
                user_input = input("请输入物体ID (输入0退出): ").strip()
                selected_id = int(user_input)
                
                if selected_id == 0:
                    print("用户选择退出程序")
                    return
                
                # 检查输入的ID是否有效
                matched = [obj for obj in valid_objects if obj[0] == selected_id]
                if matched:
                    selected_object_id = selected_id
                    print(f"已选择跟踪: ID={selected_id}, 名称={matched[0][1]}")
                    break
                else:
                    print("无效的物体ID，请重新输入")
            except ValueError:
                print("请输入有效的数字")
            except KeyboardInterrupt:
                print("\n用户中断输入，程序退出")
                return
        
        # 3. 启动监控
        print("\n启动监控系统...")
        # 监控选定的物体
        manager.monitor_object(selected_object_id)
        # 启动自身数据监控
        manager.start_monitoring(monitor_type="self")
        
        print("\n监控已启动，正在接收数据...")
        print("(按Ctrl+C停止监控)")
        
        # 保持程序运行以接收更新
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n用户请求停止监控")
    
    finally:
        # 清理资源
        print("\n正在断开连接并清理资源...")
        manager.disconnect()
        print("程序已正常退出")

if __name__ == "__main__":
    main()
