"""
DCS API 解析模块
负责API对象的创建、参数解析和序列化
"""
from enum import Enum
from typing import Dict, List, Optional, Any

class ParameterType(Enum):
    """参数类型枚举"""
    NUMBER = 0
    STRING = 1

class DCSAPI:
    """表示 DCS API 调用的类"""
    
    def __init__(self, 
                 id: int, 
                 returns_data: bool, 
                 api_syntax: str, 
                 parameter_count: int, 
                 parameter_defs: List[Dict],
                 error_thrown: bool = False,
                 error_message: Optional[str] = None,
                 result: Optional[str] = None,
                 result_type: Optional[str] = None):
        """初始化 DCSAPI 实例"""
        self.id = id
        self.returns_data = returns_data
        self.api_syntax = api_syntax
        self.parameter_count = parameter_count
        self.parameters = self._parse_parameters(parameter_defs)
        self.error_thrown = error_thrown
        self.error_message = error_message
        self.result = result
        self.result_type = result_type
    
    def _parse_parameters(self, parameter_defs: List[Dict]) -> List[Dict]:
        """解析参数定义"""
        params = []
        for param_def in parameter_defs:
            param = {
                'id': param_def.get('id', 0),
                'name': param_def.get('name', ''),
                'value': param_def.get('value', ''),
                'type': ParameterType(param_def.get('type', 0))
            }
            params.append(param)
        return params
    
    def to_dict(self) -> Dict:
        """将对象转换为字典，用于 JSON 序列化"""
        return {
            'id': self.id,
            'returns_data': self.returns_data,
            'api_syntax': self.api_syntax,
            'parameter_count': self.parameter_count,
            'parameter_defs': [{
                'id': p['id'],
                'name': p['name'],
                'value': p['value'],
                'type': p['type'].value
            } for p in self.parameters],
            'error_thrown': self.error_thrown,
            'error_message': self.error_message or "",
            'result': self.result or "",
            'result_type': self.result_type or "nil"
        }
    
    def set_parameter_value(self, param_name: str, value: Any):
        """设置参数值"""
        for param in self.parameters:
            if param['name'] == param_name:
                param['value'] = str(value)
                return
        raise ValueError(f"Parameter '{param_name}' not found in API {self.api_syntax}")
    
    def __str__(self) -> str:
        """返回对象的字符串表示"""
        return f"DCSAPI(id={self.id}, syntax='{self.api_syntax}', returns_data={self.returns_data})"

def create_api_from_dict(data: Dict) -> DCSAPI:
    """从字典创建DCSAPI对象"""
    return DCSAPI(
        id=data.get('id', 0),
        returns_data=data.get('returns_data', False),
        api_syntax=data.get('api_syntax', ''),
        parameter_count=data.get('parameter_count', 0),
        parameter_defs=data.get('parameter_defs', []),
        error_thrown=data.get('error_thrown', False),
        error_message=data.get('error_message', ''),
        result=data.get('result', ''),
        result_type=data.get('result_type', 'nil')
    )

def load_predefined_apis(predefined_apis: List[Dict]) -> List[DCSAPI]:
    """加载预定义的API列表"""
    api_list = []
    for api_def in predefined_apis:
        dcs_api = DCSAPI(
            id=api_def["id"],
            returns_data=api_def["returns_data"],
            api_syntax=api_def["api_syntax"],
            parameter_count=api_def["parameter_count"],
            parameter_defs=api_def["parameter_defs"],
            error_thrown=False,
            error_message="",
            result="",
            result_type=api_def.get("result_type", "nil")
        )
        api_list.append(dcs_api)
    return api_list
