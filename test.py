import re
from typing import List, Dict, Any

class DCSDataParser:
    def __init__(self):
        self.patterns = {
            'id': re.compile(r'^(\d+):$'),
            'key_value': re.compile(r'^\t*([^:]+):\s*(.+)$'),
            'nested_start': re.compile(r'^\t*([^:]+):$'),
            'empty_line': re.compile(r'^\s*$')
        }
        
    def parse_data(self, data: str) -> List[Dict[str, Any]]:
        """解析包含多个对象的数据字符串"""
        objects = []
        lines = data.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # 检查是否是ID行（新对象的开始）
            id_match = self.patterns['id'].match(line)
            if id_match:
                obj_id = id_match.group(1)
                i += 1  # 移动到下一行
                
                # 解析对象数据
                obj_data, i = self._parse_object(lines, i, 0)
                obj_data['ID'] = obj_id
                objects.append(obj_data)
            else:
                i += 1  # 跳过不相关的行
                
        return objects
    
    def _parse_object(self, lines: List[str], start_index: int, indent_level: int) -> (Dict[str, Any], int):
        """解析单个对象的数据"""
        obj = {}
        i = start_index
        indent = '\t' * indent_level
        
        while i < len(lines):
            line = lines[i]
            
            # 检查是否为空行
            if self.patterns['empty_line'].match(line):
                i += 1
                continue
                
            # 检查是否是当前缩进级别的结束
            if not line.startswith(indent) and indent_level > 0:
                break
                
            # 移除当前缩进
            line_content = line[len(indent):] if line.startswith(indent) else line
            
            # 检查键值对
            kv_match = self.patterns['key_value'].match(line_content)
            if kv_match:
                key = kv_match.group(1).strip()
                value = self._parse_value(kv_match.group(2).strip())
                obj[key] = value
                i += 1
                continue
                
            # 检查嵌套对象开始
            nested_match = self.patterns['nested_start'].match(line_content)
            if nested_match:
                key = nested_match.group(1).strip()
                # 递归解析嵌套对象
                nested_obj, i = self._parse_object(lines, i + 1, indent_level + 1)
                obj[key] = nested_obj
                continue
                
            i += 1  # 移动到下一行
            
        return obj, i
    
    def _parse_value(self, value_str: str) -> Any:
        """解析值字符串，尝试转换为适当的数据类型"""
        # 尝试解析为浮点数
        try:
            return float(value_str)
        except ValueError:
            pass
            
        # 尝试解析为整数
        try:
            return int(value_str)
        except ValueError:
            pass
            
        # 检查是否是布尔值
        if value_str.lower() in ['true', 'false']:
            return value_str.lower() == 'true'
            
        # 保持为字符串
        return value_str

# 使用示例
if __name__ == "__main__":
    # 示例数据
    sample_data = """16788480:
	Pitch: 0.00065683852881193
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
			y: 0.99999976158142
			x: -0.00053096370538697
			z: 0.99999976158142
		x:
			y: 0.00065683847060427
			x: 0.89767146110535
			z: 0.00065683847060427
		p:
			y: 6511.6151754479
			x: -286574.64946849
			z: 6511.6151754479
		z:
			y: -0.00013312058581505
			x: 0.44066500663757
			z: -0.00013312058581505
	Coalition: Enemies
	Heading: 5.8268462121487
	Name: F-16C_50
	Position:
		y: 6511.6151754479
		x: -286574.64946849
		z: 690471.04183188
	UnitName: ?????????
	LatLongAlt:
		Long: 42.557971095422
		Lat: 42.156017338429
		Alt: 6511.6151754479
	CoalitionID: 2
	Bank: 0.00013312061491888
16788480:
	Pitch: 0.00065683852881193
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
			y: 0.99999976158142
			x: -0.00053096370538697
			z: 0.99999976158142
		x:
			y: 0.00065683847060427
			x: 0.89767146110535
			z: 0.00065683847060427
		p:
			y: 6511.6151754479
			x: -286574.64946849
			z: 6511.6151754479
		z:
			y: -0.00013312058581505
			x: 0.44066500663757
			z: -0.00013312058581505
	Coalition: Enemies
	Heading: 5.8268462121487
	Name: F-16C_50
	Position:
		y: 6511.6151754479
		x: -286574.64946849
		z: 690471.04183188
	UnitName: ?????????
	LatLongAlt:
		Long: 42.557971095422
		Lat: 42.156017338429
		Alt: 6511.6151754479
	CoalitionID: 2
	Bank: 0.00013312061491888"""
    
    parser = DCSDataParser()
    objects = parser.parse_data(sample_data)
    
    # 打印解析结果
    for i, obj in enumerate(objects):
        print(f"Object {i+1}:")
        print(f"  ID: {obj['ID']}")
        print(f"  Name: {obj.get('Name', 'N/A')}")
        print(f"  Position: {obj.get('Position', {})}")
        print()