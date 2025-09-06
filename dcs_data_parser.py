from typing import List, Dict, Any, Callable, Optional, Tuple
import json
import re
import logging
from functools import lru_cache

# 配置日志
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())  # 默认不输出日志，由用户配置

class DCSDataParser:
    """
    DCS数据解析器，将DCS系统输出的结构化文本数据转换为键名无冒号的Python字典列表。
    
    支持解析具有层级结构的文本数据，自动识别数据类型，并提供完善的错误处理机制。
    """
    
    def __init__(self, error_handler: Optional[Callable[[str], None]] = None):
        """
        初始化解析器
        
        参数:
            error_handler: 自定义错误处理函数，默认为使用日志记录错误
        """
        self.error_handler = error_handler or self._default_error_handler
        self.indent_cache = {}  # 缓存行缩进计算结果，提高性能

    @staticmethod
    def _default_error_handler(message: str) -> None:
        """默认错误处理函数，使用日志记录错误"""
        logger.warning(message)

    @staticmethod
    def _calculate_indent(line: str, tab_width: int = 4) -> Tuple[int, str]:
        """
        计算行缩进级别，统一处理空格和制表符
        
        参数:
            line: 输入行
            tab_width: 制表符对应的空格数
        
        返回:
            缩进级别和处理后的行（制表符转换为空格）
        """
        # 计算缩进中的制表符和空格
        indent_chars = []
        for c in line:
            if c in (' ', '\t'):
                indent_chars.append(c)
            else:
                break
        
        # 转换为统一的空格计数
        indent_str = ''.join(indent_chars)
        normalized_indent = indent_str.replace('\t', ' ' * tab_width)
        indent_level = len(normalized_indent) // 2  # 每2个空格为一个缩进级别
        
        # 返回处理后的行（仅替换缩进部分的制表符）
        content = line[len(indent_chars):]
        processed_line = normalized_indent + content
        return indent_level, processed_line

    @lru_cache(maxsize=1024)
    def _parse_value(self, value_str: str, line_num: int) -> Any:
        """
        解析值并转换为合适的Python类型，使用缓存提高重复值的解析效率
        
        参数:
            value_str: 原始值字符串
            line_num: 行号，用于错误提示
        
        返回:
            转换后的Python对象
        """
        # 处理空值
        if not value_str.strip():
            return None
            
        # 处理布尔值
        lower_val = value_str.lower()
        if lower_val == 'true':
            return True
        if lower_val == 'false':
            return False
        if lower_val == 'none':
            return None
        
        # 处理数字（包括整数、浮点数和科学计数法）
        num_pattern = re.compile(r'^[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?$')
        if num_pattern.match(value_str):
            try:
                # 优先尝试整数转换
                return int(value_str)
            except ValueError:
                # 尝试浮点数转换
                try:
                    return float(value_str)
                except ValueError:
                    pass  # 保留原始字符串
        
        # 处理JSON数组
        if value_str.startswith('[') and value_str.endswith(']'):
            try:
                return json.loads(value_str)
            except json.JSONDecodeError as e:
                self.error_handler(f"第{line_num}行数组解析失败: {str(e)}，值: '{value_str}'")
        
        # 处理JSON对象
        if value_str.startswith('{') and value_str.endswith('}'):
            try:
                return json.loads(value_str)
            except json.JSONDecodeError as e:
                self.error_handler(f"第{line_num}行对象解析失败: {str(e)}，值: '{value_str}'")
        
        # 保留原始字符串
        return value_str

    def _parse_single_object(self, lines: List[str]) -> Dict[str, Any]:
        """
        解析单个物体的数据
        
        参数:
            lines: 组成单个物体的行列表
        
        返回:
            解析后的物体字典
        """
        if not lines:
            return {}
        
        result: Dict[str, Any] = {}
        stack = [(result, 0)]  # (当前字典, 当前缩进级别)
        first_line = lines[0].strip()

        # 检查首行是否为ID行（如 "16785664:"）
        if first_line.endswith(':'):
            id_part = first_line.rsplit(':', 1)[0].strip()
            if id_part.isdigit():
                # 提取根ID
                result["id"] = int(id_part)
                start_idx = 1  # 从第二行开始解析属性
            else:
                start_idx = 0  # 首行不是有效的ID行
        else:
            start_idx = 0  # 无开头ID行

        # 处理物体属性行
        for line_num, line in enumerate(lines[start_idx:], start=start_idx + 1):
            # 计算缩进和处理行
            indent_level, processed_line = self._calculate_indent(line)
            current_line = processed_line.strip()
            
            if not current_line:
                continue  # 跳过空行
            
            # 查找键值分隔符
            colon_pos = current_line.find(':')
            if colon_pos == -1:
                self.error_handler(f"第{line_num}行缺少键值分隔符: '{current_line}'")
                continue
            
            # 提取键名和值部分
            key = current_line[:colon_pos].strip()
            value_part = current_line[colon_pos + 1:].lstrip()
            
            # 找到正确的父节点
            while stack and stack[-1][1] >= indent_level:
                stack.pop()
            if not stack:
                stack.append((result, 0))  # 回退到根节点
            parent_dict, _ = stack[-1]
            
            if not value_part:
                # 嵌套节点，创建新字典
                new_dict = {}
                parent_dict[key] = new_dict
                stack.append((new_dict, indent_level))
            else:
                # 解析值并添加到父节点
                parsed_value = self._parse_value(value_part, line_num)
                parent_dict[key] = parsed_value
        
        return result

    def parse_data(self, raw_data: str) -> List[Dict[str, Any]]:
        """
        解析DCS原始数据为物体字典列表
        
        参数:
            raw_data: 原始DCS数据字符串
        
        返回:
            解析后的物体字典列表
        """
        if not raw_data:
            return []
            
        # 预处理数据：分割行并过滤空行
        lines = [line.rstrip() for line in raw_data.split('\n') if line.strip()]
        if not lines:
            return []
        
        all_objects = []
        current_object_lines: List[str] = []
        
        # 分割并解析每个物体
        for line in lines:
            stripped_line = line.strip()
            # 判断是否为新物体的开头（ID行格式：数字+冒号）
            if stripped_line.endswith(':'):
                id_part = stripped_line.rsplit(':', 1)[0].strip()
                if id_part.isdigit():
                    if current_object_lines:
                        # 解析上一个物体
                        obj_data = self._parse_single_object(current_object_lines)
                        all_objects.append(obj_data)
                        current_object_lines = []
            current_object_lines.append(line)
        
        # 处理最后一个物体
        if current_object_lines:
            obj_data = self._parse_single_object(current_object_lines)
            all_objects.append(obj_data)
        
        return all_objects


# 调试和示例用法
def main():
    # 配置日志输出
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试数据
    test_data = """
16785664:
	Pitch: 0.10096984356642
	Type:
		level3: 5
		level1: 1
		level4: 47
		level2: 1
	Country: 2
	Flags:
	GroupName: C-17 #002
	PositionAsMatrix:
		y:
			y: 0.99490612745285
			x: -0.062088575214148
			z: 0.99490612745285
		x:
			y: 0.10080575942993
			x: 0.61245423555374
			z: 0.10080575942993
		p:
			y: 9448.8081045219
			x: -307499.22200024
			z: 9448.8081045219
		z:
			y: -4.2356550693512e-05
			x: -0.78806394338608
			z: -4.2356550693512e-05
	Coalition: Enemies
	Heading: 0.90765762329102
	Name: C-17A
	Position:
		y: 9448.8081045219
		x: -307499.22200024
		z: 591204.79534245
	UnitName: Pilot #006
	LatLongAlt:
		Long: 41.345542272884
		Lat: 42.063150924973
		Alt: 9448.8081045219
	CoalitionID: 2
	Bank: 4.2366038542241e-05
16785920:
	Pitch: 0.10506981611252
	Type:
		level3: 5
		level1: 1
		level4: 47
		level2: 1
	Country: 2
	Flags:
	GroupName: C-17 #003
	PositionAsMatrix:
		y:
			y: 0.99446725845337
			x: -0.10215710103512
			z: 0.99446725845337
		x:
			y: 0.10488250106573
			x: 0.95260643959045
			z: 0.10488250106573
		p:
			y: 9448.7873458663
			x: -268197.37937391
			z: 9448.7873458663
		z:
			y: 0.0058636013418436
			x: 0.28653931617737
			z: 0.0058636013418436
	Coalition: Enemies
	Heading: 5.9925644397736
	Name: C-17A
	Position:
		y: 9448.7873458663
		x: -268197.37937391
		z: 906742.53550017
	UnitName: Pilot #007
	LatLongAlt:
		Long: 45.155208652132
		Lat: 42.072475575128
		Alt: 9448.7873458663
	CoalitionID: 2
	Bank: -0.0058585093356669
    """
    
    # 创建解析器实例
    parser = DCSDataParser()
    
    # 解析数据
    result = parser.parse_data(test_data)
    
    # 输出解析结果
    print(f"===== 解析结果 =====")
    print(f"成功解析 {len(result)} 个物体")
    print(json.dumps(result, indent=4, ensure_ascii=False))
    
    # 验证解析结果
    if result:
        first_object = result[1]
        print("\n===== 解析验证 =====")
        print(f"第一个物体ID: {first_object.get('id')}")
        print(f"第一个物体名称: {first_object.get('Name')}")
        print(f"第一个物体纬度: {first_object.get('LatLongAlt', {}).get('Lat')}")
        print(f"第一个物体类型level3: {first_object.get('Type', {}).get('level3')}")


if __name__ == "__main__":
    main()
