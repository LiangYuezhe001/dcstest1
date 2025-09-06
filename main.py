import time
import threading
from dcs_object_manager import DCSObjectManager
from typing import List, Dict, Any


def print_object_list(objects: List[Dict[str, Any]]) -> None:
    """格式化显示物体列表（仅展示关键信息）"""
    if not objects:
        print("未获取到物体数据")
        return
    
    # 打印表头
    print("\n" + "="*80)
    print(f"{'ID':<12} | {'名称':<20} | {'国家':<10} | {'类型':<15} | 位置概要")
    print("-"*80)
    
    # 打印物体列表
    for obj in objects:
        obj_id = obj.get('id', '未知')
        name = obj.get('Name', '未知')[:18]  # 限制长度
        country = obj.get('Country', '未知')
        obj_type = obj.get('Type', '未知')[:13]
        position = obj.get('Position', {})
        pos_summary = f"X:{position.get('x', 0):.1f}, Y:{position.get('y', 0):.1f}"
        
        print(f"{obj_id:<12} | {name:<20} | {country:<10} | {obj_type:<15} | {pos_summary}")
    
    print("="*80 + "\n")


def track_object(manager: DCSObjectManager, target_id: int, interval: float = 2.0) -> None:
    """跟踪指定ID的物体，定期更新信息"""
    try:
        print(f"\n开始跟踪物体ID={target_id}（按Ctrl+C停止跟踪）")
        while True:
            # 获取最新数据
            obj_data = manager.fetch_object_by_id(target_id, timeout=5.0)
            
            if obj_data:
                # 清屏（跨平台兼容）
                print("\033c", end="")
                print(f"===== 物体跟踪 (ID={target_id}) =====")
                print(f"名称: {obj_data.get('Name', '未知')}")
                print(f"国家: {obj_data.get('Country', '未知')}")
                print(f"联盟: {obj_data.get('Coalition', '未知')}")
                print(f"类型: {obj_data.get('Type', '未知')}")
                
                # 位置信息
                pos = obj_data.get('Position', {})
                print(f"坐标: X={pos.get('x', 0):.2f}, Y={pos.get('y', 0):.2f}, Z={pos.get('z', 0):.2f}")
                
                # 经纬度信息
                latlong = obj_data.get('LatLongAlt', {})
                print(f"经纬度: 纬度={latlong.get('lat', 0):.6f}, 经度={latlong.get('long', 0):.6f}")
                print(f"高度: {latlong.get('alt', 0):.2f}米")
                
                print(f"\n上次更新: {time.strftime('%H:%M:%S')}")
                print("-------------------------------------")
            else:
                print(f"无法获取物体ID={target_id}的最新数据，将重试...")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n已停止跟踪")


def main():
    # 初始化管理器
    manager = DCSObjectManager(
        host="127.0.0.1",
        port=7790,
        update_interval=5.0,
        debug=False
    )
    
    # 启动批量监控（在后台线程运行）
    print("连接到DCS服务器并获取所有物体...")
    if not manager.start_monitoring():
        print("连接失败，退出程序")
        return
    
    try:
        # 等待第一批数据加载
        print("等待物体数据加载（最多30秒）...")
        start_time = time.time()
        while len(manager.get_all_objects()) == 0 and time.time() - start_time < 30:
            time.sleep(1)
        
        # 获取并显示所有物体
        all_objects = manager.get_all_objects()
        print(f"共发现 {len(all_objects)} 个物体：")
        print_object_list(all_objects)
        
        # 用户选择要跟踪的ID
        while True:
            try:
                target_id = input("请输入要跟踪的物体ID（输入0退出）: ")
                target_id = int(target_id)
                
                if target_id == 0:
                    break
                
                # 验证ID是否存在
                if any(obj.get('id') == target_id for obj in all_objects):
                    track_object(manager, target_id)
                    # 跟踪结束后重新显示物体列表
                    all_objects = manager.get_all_objects()
                    print(f"\n当前物体总数: {len(all_objects)}")
                    print_object_list(all_objects)
                else:
                    print(f"未找到ID={target_id}的物体，请重新输入")
            
            except ValueError:
                print("请输入有效的数字ID")
    
    except KeyboardInterrupt:
        print("\n用户中断操作")
    finally:
        # 清理资源
        manager.stop_monitoring()
        manager.disconnect()
        print("程序已退出")


if __name__ == "__main__":
    main()
    