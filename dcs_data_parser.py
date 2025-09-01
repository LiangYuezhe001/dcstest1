from typing import List, Dict, Any


def parse_single_object(lines: List[str]) -> Dict[str, Any]:
    """解析单个物体的数据，返回包含ID和属性的字典"""
    if not lines:
        return {}
    
    # 提取根ID
    root_line = lines[0]
    root_id = root_line.split(':', 1)[0].strip()
    result = {"id": root_id}  # 用"id"字段存储物体ID
    current_dict = result  # 当前操作的字典（从根属性开始）
    
    # 处理剩余行
    stack = [(current_dict, 0)]  # (当前字典, 当前缩进级别)
    
    for line in lines[1:]:
        indent = len(line) - len(line.lstrip(' \t'))
        current_line = line.lstrip(' \t')
        
        if ': ' in current_line:
            key, value = current_line.split(': ', 1)
            key = key.strip()
            
            if not value.strip():
                # 嵌套节点，创建新字典
                new_dict = {}
                while stack and stack[-1][1] >= indent:
                    stack.pop()
                parent_dict, _ = stack[-1]
                parent_dict[key] = new_dict
                stack.append((new_dict, indent))
                current_dict = new_dict
            else:
                # 普通值，转换类型
                parsed_value = value.strip()
                if parsed_value.replace('.', '', 1).replace('-', '', 1).isdigit():
                    if '.' in parsed_value:
                        parsed_value = float(parsed_value)
                    else:
                        parsed_value = int(parsed_value)
                # 找到父节点
                while stack and stack[-1][1] >= indent:
                    stack.pop()
                parent_dict, _ = stack[-1]
                parent_dict[key] = parsed_value
    
    return result


def parse_dcs_data(raw_data: str) -> List[Dict[str, Any]]:
    """解析DCS数据为数组（列表），每个元素是包含id和属性的字典"""
    lines = [line.rstrip() for line in raw_data.strip().split('\n') if line.strip()]
    if not lines:
        return []
    
    all_objects = []  # 用列表存储所有物体
    current_object_lines = []
    
    for line in lines:
        # 判断是否是新物体的开始（以数字ID开头）
        if line.strip().endswith(':') and line.strip().split(':')[0].isdigit():
            if current_object_lines:
                # 解析并添加当前物体
                obj_data = parse_single_object(current_object_lines)
                all_objects.append(obj_data)
                current_object_lines = []
            current_object_lines.append(line)
        else:
            current_object_lines.append(line)
    
    # 添加最后一个物体
    if current_object_lines:
        obj_data = parse_single_object(current_object_lines)
        all_objects.append(obj_data)
    
    return all_objects  # 返回列表而非字典


class DCSDataParser:
    """DCS数据解析器，返回数组格式结果"""
    
    def parse_data(self, data: str) -> List[Dict[str, Any]]:
        return parse_dcs_data(data)
