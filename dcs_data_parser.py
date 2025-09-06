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
        self.indent_cache = {}  # 缓存行缩进计算结果，key:原始行，value:(indent_level, processed_line)
        self.id_line_pattern = re.compile(r'^\s*\d+:\s*$')  # 预编译ID行正则

    @staticmethod
    def _default_error_handler(message: str) -> None:
        """默认错误处理函数，使用日志记录错误"""
        logger.warning(message)

    def _calculate_indent(self, line: str, tab_width: int = 4) -> Tuple[int, str]:
        """
        计算行缩进级别，统一处理空格和制表符（带缓存）
        
        参数:
            line: 输入行
            tab_width: 制表符对应的空格数
        
        返回:
            缩进级别和处理后的行（制表符转换为空格）
        """
        if line in self.indent_cache:
            return self.indent_cache[line]
        
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
        self.indent_cache[line] = (indent_level, processed_line)  # 缓存结果
        return indent_level, processed_line

    @staticmethod
    def _is_number(value_str: str) -> bool:
        """判断字符串是否为数字（整数、浮点数或科学计数法）"""
        s = value_str.strip()
        if not s:
            return False
        
        # 处理科学计数法的e/E
        has_e = 'e' in s or 'E' in s
        parts = s.split('e', 1) if 'e' in s else s.split('E', 1) if 'E' in s else [s]
        if len(parts) > 2:
            return False  # 多个e/E，无效
        
        # 检查基数部分
        base = parts[0]
        if base.startswith(('+', '-')):
            base = base[1:]
        if not base:
            return False  # 仅符号，无效
        
        if '.' in base:
            base_parts = base.split('.', 1)
            if len(base_parts) != 2 or not (base_parts[0] or base_parts[1]):
                return False  # 多个小数点或空部分
            if base_parts[0] and not base_parts[0].isdigit():
                return False
            if base_parts[1] and not base_parts[1].isdigit():
                return False
        else:
            if not base.isdigit():
                return False  # 无小数点时必须为纯数字
        
        # 检查指数部分（若有）
        if has_e:
            exp = parts[1]
            if exp.startswith(('+', '-')):
                exp = exp[1:]
            if not exp.isdigit():
                return False
        
        return True

    @lru_cache(maxsize=4096)  # 扩大缓存容量
    def _parse_value(self, value_str: str, line_num: int) -> Any:
        """
        解析值并转换为合适的Python类型，使用缓存提高重复值的解析效率
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
        
        # 处理数字（替换正则匹配为字符串判断）
        if self._is_number(value_str):
            try:
                return int(value_str)
            except ValueError:
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
        """解析单个物体的数据"""
        if not lines:
            return {}
        
        result: Dict[str, Any] = {}
        stack = [(result, 0)]  # (当前字典, 当前缩进级别)
        first_line = lines[0].strip()

        # 检查首行是否为ID行（如 "16785664:"）
        if first_line.endswith(':'):
            id_part = first_line.rsplit(':', 1)[0].strip()
            if id_part.isdigit():
                result["id"] = int(id_part)
                start_idx = 1  # 从第二行开始解析属性
            else:
                start_idx = 0
        else:
            start_idx = 0

        # 处理物体属性行
        for line_num, line in enumerate(lines[start_idx:], start=start_idx + 1):
            indent_level, processed_line = self._calculate_indent(line)
            current_line = processed_line.strip()
            
            if not current_line:
                continue  # 跳过空行
            
            # 用partition分割键值（比find更高效）
            key_part, colon, value_part = current_line.partition(':')
            if not colon:
                self.error_handler(f"第{line_num}行缺少键值分隔符: '{current_line}'")
                continue
            
            key = key_part.strip()
            value_part = value_part.lstrip()
            
            # 找到正确的父节点
            while stack and stack[-1][1] >= indent_level:
                stack.pop()
            if not stack:
                stack.append((result, 0))
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
        """解析DCS原始数据为物体字典列表"""
        if not raw_data:
            return []
            
        # 用splitlines()替代split('\n')，更高效处理换行符
        lines = [line.rstrip() for line in raw_data.splitlines() if line.strip()]
        if not lines:
            return []
        
        all_objects = []
        current_object_lines: List[str] = []
        
        # 分割并解析每个物体（用预编译正则识别ID行）
        for line in lines:
            stripped_line = line.strip()
            if self.id_line_pattern.match(stripped_line):
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


# 调试和示例用法（保持不变）
def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试数据（同上）
    test_data = """..."""  # 省略测试数据
    
    parser = DCSDataParser()
    result = parser.parse_data(test_data)
    
    print(f"===== 解析结果 =====")
    print(f"成功解析 {len(result)} 个物体")
    print(json.dumps(result, indent=4, ensure_ascii=False))
    
    if result:
        first_object = result[1]
        print("\n===== 解析验证 =====")
        print(f"第一个物体ID: {first_object.get('id')}")
        print(f"第一个物体名称: {first_object.get('Name')}")
        print(f"第一个物体纬度: {first_object.get('LatLongAlt', {}).get('Lat')}")
        print(f"第一个物体类型level3: {first_object.get('Type', {}).get('level3')}")


if __name__ == "__main__":
    main()