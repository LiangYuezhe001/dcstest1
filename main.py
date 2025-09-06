import time
import threading
import os
from dcs_object_manager import DCSObjectManager
from typing import List, Dict, Any


def clear_screen() -> None:
    """跨平台清屏函数"""
    os.system('cls' if os.name == 'nt' else 'clear')


def format_type_info(type_dict: Any) -> str:
    """格式化显示Type信息（处理字典类型）"""
    if isinstance(type_dict, dict):
        # 提取关键级别信息
        levels = [f"level{i}:{type_dict.get(f'level{i}', '?')}" for i in range(1, 5) if f'level{i}' in type_dict]
        return ", ".join(levels) if levels else "未知类型"
    return str(type_dict)[:15]  # 限制长度


def print_object_list(objects: List[Dict[str, Any]]) -> None:
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
        country = obj.get('Country', '未知')
        obj_type = format_type_info(obj.get('Type', '未知'))
        position = obj.get('Position', {})
        pos_summary = f"X:{position.get('x', 0):.1f}, Y:{position.get('y', 0):.1f}"
        
        print(f"{obj_id:<12} | {name:<20} | {country:<10} | {obj_type:<25} | {pos_summary}")
    
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
                clear_screen()
                print(f"===== 物体跟踪 (ID={target_id}) =====")
                print(f"名称: {obj_data.get('Name', '未知')}")
                print(f"国家: {obj_data.get('Country', '未知')}")
                print(f"联盟: {obj_data.get('Coalition', '未知')}")
                print(f"类型: {format_type_info(obj_data.get('Type', '未知'))}")
                
                # 位置信息
                pos = obj_data.get('Position', {})
                print(f"坐标: X={pos.get('x', 0):.2f}, Y={pos.get('y', 0):.2f}, Z={pos.get('z', 0):.2f}")
                
                # 经纬度信息（匹配解析后的键名大写格式）
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
            else:
                print(f"无法获取物体ID={target_id}的最新数据，将重试...")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n已停止跟踪")
    except Exception as e:
        print(f"跟踪过程中发生错误: {str(e)}")


def get_object_ids(objects: List[Dict[str, Any]]) -> List[int]:
    """提取所有物体的ID列表"""
    ids = []
    for obj in objects:
        try:
            obj_id = obj.get('id')
            if obj_id and isinstance(obj_id, (int, str)):
                ids.append(int(obj_id))
        except (ValueError, TypeError):
            continue
    return ids


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
        all_objects = []
        while len(all_objects) == 0 and time.time() - start_time < 30:
            all_objects = manager.get_all_objects()
            if not all_objects:
                time.sleep(1)
                print(f"已等待 {int(time.time() - start_time)} 秒...")
        
        if not all_objects:
            print("未能获取到物体数据，程序将退出")
            return
        
        # 获取并显示所有物体
        print(f"共发现 {len(all_objects)} 个物体：")
        print_object_list(all_objects)
        object_ids = get_object_ids(all_objects)
        print(f"可用物体ID: {', '.join(map(str, object_ids[:10]))}{'...' if len(object_ids) > 10 else ''}")
        
        # 用户选择要跟踪的ID
        while True:
            try:
                num_input = input("请输入要跟踪的物体ID（输入0退出）: ")
                if not num_input.strip():
                    print("请输入有效的ID")
                    continue
                    
                target_id = int(num_input)
                
                if target_id == 0:
                    break
                
                # 验证ID是否存在
                if target_id in object_ids:
                    track_object(manager, target_id)
                    # 跟踪结束后重新显示物体列表
                    all_objects = manager.get_all_objects()
                    object_ids = get_object_ids(all_objects)
                    print(f"\n当前物体总数: {len(all_objects)}")
                    print_object_list(all_objects)
                    print(f"可用物体ID: {', '.join(map(str, object_ids[:10]))}{'...' if len(object_ids) > 10 else ''}")
                else:
                    print(f"未找到ID={target_id}的物体，请重新输入")
                    print(f"可用物体ID: {', '.join(map(str, object_ids[:10]))}{'...' if len(object_ids) > 10 else ''}")
            
            except ValueError:
                print("请输入有效的数字ID")
            except Exception as e:
                print(f"操作出错: {str(e)}")
    
    except KeyboardInterrupt:
        print("\n用户中断操作")
    finally:
        # 清理资源
        manager.stop_monitoring()
        manager.disconnect()
        print("程序已退出")


if __name__ == "__main__":
    main()
    