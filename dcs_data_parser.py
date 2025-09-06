from typing import List, Dict, Any, Callable
import pprint
import json
import re

def parse_single_object(
    lines: List[str], 
    error_handler: Callable[[str], None] = lambda msg: print(f"警告: {msg}")
) -> Dict[str, Any]:
    """
    解析单个物体的数据，生成键名无冒号的固定结构字典
    
    参数:
        lines: 组成单个物体的行列表
        error_handler: 处理解析错误的回调函数
    
    返回:
        解析后的物体字典，键名不含冒号
    """
    if not lines:
        return {}
    
    result = {}
    stack = [(result, 0)]  # (当前字典, 当前缩进级别)
    first_line = lines[0].strip()

    # 检查首行是否为ID行（如 "16785664:"）
    if first_line.endswith(':') and first_line.split(':')[0].isdigit():
        # 提取根ID（适用于LoGetWorldObjects格式）
        root_id = first_line.split(':', 1)[0].strip()
        result["id"] = root_id
        # 从第二行开始解析属性
        start_idx = 1 if len(lines) > 1 else 0
    else:
        # 无开头ID行（适用于LoGetObjectById格式）
        start_idx = 0

    # 处理物体属性行
    if start_idx >= len(lines):
        return result
    
    for line_num, line in enumerate(lines[start_idx:], start=start_idx+1):
        # 统一处理制表符为4个空格，便于缩进计算
        normalized_line = line.replace('\t', '    ')
        indent = len(normalized_line) - len(normalized_line.lstrip(' '))
        current_line = normalized_line.lstrip(' ')
        
        # 跳过空行
        if not current_line:
            continue
            
        # 检查是否包含键值分隔符，提取键名时移除冒号
        colon_index = current_line.find(':')
        if colon_index == -1:
            error_handler(f"第{line_num}行无法解析（缺少冒号）: '{current_line}'")
            continue
        
        # 提取键名（移除末尾的冒号）和值
        key = current_line[:colon_index].strip()  # 关键修改：不包含冒号
        value_part = current_line[colon_index + 1:].lstrip()
        
        if not value_part:
            # 嵌套节点，创建新字典
            new_dict = {}
            # 找到正确的父节点
            while stack and stack[-1][1] >= indent:
                stack.pop()
            if not stack:
                stack.append((result, 0))  # 回退到根字典
            parent_dict, _ = stack[-1]
            parent_dict[key] = new_dict
            stack.append((new_dict, indent))
        else:
            # 普通值，尝试转换类型
            parsed_value = parse_value(value_part, error_handler, line_num)
            
            # 找到正确的父节点
            while stack and stack[-1][1] >= indent:
                stack.pop()
            if not stack:
                stack.append((result, 0))  # 回退到根字典
            parent_dict, _ = stack[-1]
            parent_dict[key] = parsed_value
    
    return result


def parse_value(
    value: str, 
    error_handler: Callable[[str], None], 
    line_num: int
) -> Any:
    """解析值并尝试转换为合适的类型"""
    # 检查是否为布尔值
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    
    # 检查是否为None
    if value.lower() == 'none':
        return None
    
    # 检查是否为数字（包括科学计数法）
    number_pattern = re.compile(r'^[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?$')
    if number_pattern.match(value):
        try:
            # 尝试转换为整数
            return int(value)
        except ValueError:
            # 尝试转换为浮点数
            try:
                return float(value)
            except ValueError:
                pass  # 保留原始字符串
    
    # 检查是否为JSON格式的数组
    if value.startswith('[') and value.endswith(']'):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            error_handler(f"第{line_num}行的数组格式无效: '{value}'")
    
    # 保留原始字符串
    return value


def parse_dcs_data(
    raw_data: str, 
    error_handler: Callable[[str], None] = lambda msg: print(f"警告: {msg}")
) -> List[Dict[str, Any]]:
    """
    解析DCS数据为数组，生成键名无冒号的固定结构
    
    参数:
        raw_data: 原始DCS数据字符串
        error_handler: 处理解析错误的回调函数
    
    返回:
        解析后的物体字典列表，键名不含冒号
    """
    lines = [line.rstrip() for line in raw_data.strip().split('\n') if line.strip()]
    if not lines:
        return []
    
    all_objects = []
    current_object_lines = []
    
    for line_num, line in enumerate(lines, start=1):
        stripped_line = line.strip()
        # 判断是否为新物体的开头（ID行格式：数字+冒号）
        if stripped_line.endswith(':') and stripped_line.split(':')[0].isdigit():
            if current_object_lines:
                # 解析上一个物体
                obj_data = parse_single_object(current_object_lines, error_handler)
                all_objects.append(obj_data)
                current_object_lines = []
            current_object_lines.append(line)
        else:
            current_object_lines.append(line)
    
    # 处理最后一个物体
    if current_object_lines:
        obj_data = parse_single_object(current_object_lines, error_handler)
        all_objects.append(obj_data)
    
    return all_objects


class DCSDataParser:
    """DCS数据解析器，生成键名无冒号的固定结构结果"""
    
    def __init__(self, error_handler: Callable[[str], None] = None):
        """
        初始化解析器
        
        参数:
            error_handler: 自定义错误处理函数，默认为打印警告
        """
        self.error_handler = error_handler or (lambda msg: print(f"警告: {msg}"))
    
    def parse_data(self, data: str) -> List[Dict[str, Any]]:
        """
        解析DCS数据，返回键名无冒号的固定结构结果
        
        参数:
            data: 原始DCS数据字符串
        
        返回:
            解析后的物体字典列表，键名不含冒号
        """
        return parse_dcs_data(data, self.error_handler)


# 调试主函数：验证键名无冒号的固定结构解析效果
if __name__ == "__main__":
    # 测试数据：LoGetObjectById格式（无开头ID行）
    test_data = """
Pitch: 0.00074277498060837
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
        y: 0.99999970197678
        x: -0.00058460742002353
        z: 0.99999970197678
    x:
        y: 0.00074280321132392
        x: 0.89767533540726
        z: 0.00074280321132392
    p:
        y: 5106.030996279
        x: -244504.08167846
        z: 5106.030996279
    z:
        y: -0.0001865144004114
        x: 0.4406570494175
        z: -0.0001865144004114
Coalition: Enemies
Heading: 5.8268548250198
Name: F-16C_50
Position:
    y: 5106.030996279
    x: -244504.08167846
    z: 670183.18642734
UnitName: ?????????
LatLongAlt:
    Long: 42.371586124113
    Lat: 42.549983390301
    Alt: 5106.030996279
CoalitionID: 2
Bank: 0.00018662192451302
Velocity: [150.5, 0.0, -2.3]
Distance: 3.2e+5
    """
    
    # 使用解析器
    parser = DCSDataParser()
    result = parser.parse_data(test_data)
    
    print("===== 解析结果（键名无冒号） =====")
    print(f"解析出 {len(result)} 个物体：")
    # 输出格式化的JSON，确保中文正常显示
    print(json.dumps(result, indent=4, ensure_ascii=False))
    
    # 验证关键属性（键名无冒号）
    if result:
        parsed_object = result[0]
        print("\n===== 关键属性验证 =====")
        print(f"俯仰角 (Pitch): {parsed_object.get('Pitch')}")
        print(f"类型 (Type 级别3): {parsed_object.get('Type', {}).get('level3')}")
        print(f"国家代码 (Country): {parsed_object.get('Country')}")
        print(f"经纬度 (LatLongAlt 纬度): {parsed_object.get('LatLongAlt', {}).get('Lat')}")
        print(f"速度 (Velocity): {parsed_object.get('Velocity')}")
