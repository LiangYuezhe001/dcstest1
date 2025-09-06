from typing import List, Dict, Any
import pprint


def parse_single_object(lines: List[str]) -> Dict[str, Any]:
    """解析单个物体的数据，兼容有/无开头ID行的两种格式，增加边界检查"""
    if not lines:
        return {}
    
    result = {}
    current_dict = result
    stack = [(current_dict, 0)]  # (当前字典, 当前缩进级别)
    first_line = lines[0].strip()

    # 检查首行是否为ID行（如 "16785664:"）
    if first_line.endswith(':') and first_line.split(':')[0].isdigit():
        # 提取根ID（适用于LoGetWorldObjects格式）
        root_id = first_line.split(':', 1)[0].strip()
        result["id"] = root_id
        # 从第二行开始解析属性（增加边界检查）
        start_idx = 1 if len(lines) > 1 else 0
    else:
        # 无开头ID行（适用于LoGetObjectById格式），从第一行开始解析属性
        start_idx = 0

    # 处理物体属性行（增加边界检查）
    if start_idx >= len(lines):
        return result  # 避免索引越界
    
    for line in lines[start_idx:]:
        indent = len(line) - len(line.lstrip(' \t'))
        current_line = line.lstrip(' \t')
        
        # 跳过空行（防止异常数据）
        if not current_line:
            continue
            
        # 确保行包含键值分隔符，避免split错误
        if ': ' not in current_line:
            # 尝试用其他方式处理（如只有冒号的情况）
            if ':' in current_line:
                key, value = current_line.split(':', 1)
                key = key.strip()
                value = value.strip()
            else:
                # 无法解析的行，跳过并记录（调试用）
                print(f"警告：无法解析行 '{current_line}'")
                continue
        
        key, value = current_line.split(': ', 1) if ': ' in current_line else (current_line, '')
        key = key.strip()
        value = value.strip()
        
        if not value:
            # 嵌套节点，创建新字典
            new_dict = {}
            # 栈操作前检查栈是否为空（防止索引越界）
            while stack and stack[-1][1] >= indent:
                stack.pop()
            # 确保栈至少有一个元素
            if not stack:
                stack.append((result, 0))  # 回退到根字典
            parent_dict, _ = stack[-1]
            parent_dict[key] = new_dict
            stack.append((new_dict, indent))
            current_dict = new_dict
        else:
            # 普通值，转换类型
            parsed_value = value
            # 尝试转换为数字类型（增加格式检查）
            if parsed_value.replace('.', '', 1).replace('-', '', 1).isdigit():
                if '.' in parsed_value:
                    try:
                        parsed_value = float(parsed_value)
                    except ValueError:
                        pass  # 保留原始字符串
                else:
                    try:
                        parsed_value = int(parsed_value)
                    except ValueError:
                        pass  # 保留原始字符串
            # 找到父节点并赋值（检查栈是否为空）
            while stack and stack[-1][1] >= indent:
                stack.pop()
            # 确保栈至少有一个元素
            if not stack:
                stack.append((result, 0))  # 回退到根字典
            parent_dict, _ = stack[-1]
            parent_dict[key] = parsed_value
    
    return result


def parse_dcs_data(raw_data: str) -> List[Dict[str, Any]]:
    """解析DCS数据为数组，兼容多物体（带ID行）和单物体（可能无ID行）格式"""
    lines = [line.rstrip() for line in raw_data.strip().split('\n') if line.strip()]
    if not lines:
        return []
    
    all_objects = []
    current_object_lines = []
    
    for line in lines:
        stripped_line = line.strip()
        # 判断是否为新物体的开头（ID行格式：数字+冒号）
        if stripped_line.endswith(':') and stripped_line.split(':')[0].isdigit():
            if current_object_lines:
                # 解析上一个物体
                obj_data = parse_single_object(current_object_lines)
                all_objects.append(obj_data)
                current_object_lines = []
            current_object_lines.append(line)
        else:
            current_object_lines.append(line)
    
    # 处理最后一个物体（无论是否有ID行）
    if current_object_lines:
        obj_data = parse_single_object(current_object_lines)
        all_objects.append(obj_data)
    
    return all_objects


class DCSDataParser:
    """DCS数据解析器，兼容两种数据格式"""
    
    def parse_data(self, data: str) -> List[Dict[str, Any]]:
        return parse_dcs_data(data)


# 调试主函数：测试两种格式数据的解析效果
if __name__ == "__main__":
    # 测试1：LoGetWorldObjects格式（带开头ID行）
    test_data1 = """16785664:
        Pitch: 0.10101927816868
        Type:
            level3: 5
            level1: 1
            level4: 47
            level2: 1
        Country: 2
        Position:
            x: 1234.56
            y: 789.01
    16785665:
        Roll: -0.023456
        Type:
            level3: 3
            level1: 2
        Country: 1
    """
    
    # 测试2：LoGetObjectById格式（无开头ID行）
    test_data2 = """Pitch: 0.0089191347360611
Type:
        level3: 1
        level1: 1
        level4: 275
        level2: 1
Country: 2
Flags:
GroupName: Player
PositionAsMatrix:
        y:
                y: 0.99996024370193
                x: -0.0080521097406745
                z: 0.99996024370193
        x:
                y: 0.008918990381062
                x: 0.89762204885483
                z: 0.008918990381062
        p:
                y: 7198.9461371385
                x: -306136.37901418
                z: 7198.9461371385
        z:
                y: 0.00010417029261589
                x: 0.44069242477417
                z: 0.00010417029261589
Coalition: Enemies
Heading: 5.8268146514893
Name: F-16C_50
Position:
        y: 7198.9461371385
        x: -306136.37901418
        z: 699911.54117083
UnitName: 新呼号
LatLongAlt:
        Long: 42.644055309283
        Lat: 41.972804950209
        Alt: 7198.9461371385
CoalitionID: 2
Bank: -0.00010418758756714
    """
    
    # 测试3：异常数据（空行、不完整格式）
    test_data3 = """
    12345:
        Name: TestObject
        
        InvalidLine  # 无冒号的行
    """
    
    parser = DCSDataParser()
    
    print("===== 测试1：解析带ID行的多物体数据 =====")
    result1 = parser.parse_data(test_data1)
    print(f"解析出 {len(result1)} 个物体：")
    pprint.pprint(result1, indent=2)
    
    print("\n===== 测试2：解析无ID行的单物体数据 =====")
    result2 = parser.parse_data(test_data2)
    print(f"解析出 {len(result2)} 个物体：")
    pprint.pprint(result2, indent=2)
    
    print("\n===== 测试3：解析异常数据 =====")
    result3 = parser.parse_data(test_data3)
    print(f"解析出 {len(result3)} 个物体：")
    pprint.pprint(result3, indent=2)
