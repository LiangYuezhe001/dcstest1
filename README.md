# DCS 数据监控工具

该项目是一个用于监控DCS（数字战斗模拟）游戏内实体数据的客户端工具，通过连接DCS服务器、发送API命令获取实体信息，并进行解析和可视化展示。以下是各模块的详细说明：


## 核心模块说明

### 1. `dcs_api_definitions.py` - API定义模块
**用途**：存储所有已知的DCS API元数据，作为客户端与服务器通信的"协议字典"。

**核心内容**：
- `DCS_APIS`：列表类型，包含多个API定义字典，每个字典描述一个API的详细信息：
  - `id`：API唯一标识（整数）
  - `returns_data`：是否返回数据（布尔值）
  - `api_syntax`：API语法字符串（如`"LoGetSelfData()"`）
  - `parameter_count`：参数数量（整数）
  - `parameter_defs`：参数定义列表（包含参数ID、名称、类型）
  - `result_type`：返回值类型（默认`"nil"`）


### 2. `dcs_api_parser.py` - API解析模块
**用途**：负责API对象的创建、参数解析和序列化，将API定义转换为可操作的对象。

**核心类与函数**：
- `ParameterType`：枚举类，定义参数类型（`NUMBER=0`、`STRING=1`）
- `DCSAPI`：API对象类，封装API的属性和操作：
  - `__init__`：初始化API对象（接收ID、参数定义等）
  - `_parse_parameters`：解析参数定义为结构化字典
  - `to_dict`：转换为字典，用于JSON序列化
  - `set_parameter_value`：设置指定参数的值（按参数名）
- `create_api_from_dict`：从字典数据创建`DCSAPI`对象
- `load_predefined_apis`：加载`dcs_api_definitions.py`中的预定义API列表，转换为`DCSAPI`对象列表


### 3. `dcs_network.py` - 网络通信模块
**用途**：实现底层TCP Socket通信，负责与DCS服务器建立连接、发送数据和接收数据。

**核心类**：`DCSNetwork`
- 初始化参数：`host`（服务器地址，默认`"127.0.0.1"`）、`port`（端口，默认`7777`）
- 主要方法：
  - `connect()`：建立与服务器的TCP连接，返回连接结果（布尔值）
  - `disconnect()`：关闭连接，清理资源
  - `send_data(data: bytes)`：发送字节数据到服务器，返回发送结果（布尔值）
  - `start_listening(stop_event)`：在独立线程中监听服务器数据，通过`data_received_callback`传递接收的数据
  - `is_connected`：属性，返回当前连接状态（布尔值）


### 4. `dcs_command_processor.py` - 命令处理模块
**用途**：管理API命令队列，确保命令有序发送，并处理响应回调。

**核心类**：`DCSCommandProcessor`
- 主要方法：
  - `queue_command(api: DCSAPI, params: Dict)`：将API命令加入队列，设置参数（可选），返回入队结果（布尔值）
  - `send_next_command()`：发送队列中的下一个命令（通过`send_data_callback`发送序列化数据）
  - `mark_response_received()`：标记响应已接收，触发下一个命令发送


### 5. `dcs_event_handler.py` - 事件处理模块
**用途**：管理各类事件回调（连接状态、数据接收、错误），实现模块间解耦。

**核心类**：`DCSEventHandler`
- 主要回调属性：
  - `on_connection_changed`：连接状态变化回调（参数：`connected: bool`）
  - `on_api_data_received`：API数据接收回调（参数：`api: DCSAPI`）
  - `on_error_received`：错误接收回调（参数：`error_type: str`, `message: str`）
- 触发方法：
  - `trigger_connection_changed(connected)`：触发连接状态变化事件
  - `trigger_api_data_received(api)`：触发API数据接收事件
  - `trigger_error_received(error_type, message)`：触发错误事件


### 6. `dcs_client.py` - 客户端核心模块
**用途**：整合网络、命令处理、事件处理等子模块，提供高层API调用接口。

**核心类**：`DCSClient`
- 初始化参数：`host`、`port`、`log_level`（日志级别）
- 主要方法：
  - `connect()`：连接服务器，启动监听线程，返回连接结果（布尔值）
  - `disconnect()`：断开连接，停止监听线程
  - `send_command(api_id: int, params: Dict = None)`：发送指定ID的API命令（带参数），返回发送结果（布尔值）
  - `get_api(api_id: int = None, api_name: str = None)`：根据ID或语法查找API对象
  - `get_apis_matching(pattern: str)`：查找语法包含指定模式的API列表
  - `is_connected`：属性，返回当前连接状态


### 7. `dcs_data_parser.py` / `test.py` / `test3.py` - 数据解析模块
**用途**：解析服务器返回的原始数据字符串，转换为结构化字典（支持嵌套数据）。

**核心类**：`DCSDataParser`（`test.py`中实现）
- 主要方法：
  - `parse_data(data: str)`：将原始字符串数据解析为实体对象列表（每个对象为字典），支持缩进格式的嵌套数据解析


### 8. `dcs_display.py` - 显示格式化模块
**用途**：将解析后的实体数据以表格形式格式化展示，支持调试信息打印。

**核心类**：`DCSDisplayFormatter`
- 初始化参数：`debug`（是否开启调试模式，默认`False`）
- 主要方法：
  - `display_objects(objects: List[Dict], update_interval: float)`：以表格形式显示实体数据（包含ID、名称、国家、位置等）
  - `print_debug_info(raw_data: str, parsed_objects: List[Dict])`：在调试模式下打印原始数据和解析后的详细结构
  - 辅助方法：坐标格式化、文本截断、国家/联盟名称映射等


### 9. `main.py` / `test2.py` - 主程序入口
**用途**：整合客户端、数据解析和显示模块，实现完整的DCS实体监控流程。

**核心类**：`DCSObjectDisplay`
- 初始化参数：`host`、`port`、`update_interval`（数据更新间隔，默认5秒）、`debug`（调试模式）
- 主要方法：
  - `start()`：启动监控流程（连接服务器、定时发送API命令、处理数据并显示）
  - `stop()`：停止监控（断开连接、清理资源）
- 回调处理：通过`_on_connection_changed`、`_on_api_data_received`等方法处理连接状态和数据接收


## 使用流程
1. 实例化`DCSObjectDisplay`，指定服务器地址、端口和更新间隔
2. 调用`start()`方法启动监控
3. 工具自动连接DCS服务器，定时发送API命令（默认ID=52，获取实体数据）
4. 接收数据后解析并通过表格展示，支持Ctrl+C中断监控


## 依赖说明
- Python 3.x
- 标准库：`socket`、`select`、`threading`、`logging`、`json`、`enum`等（无需额外安装第三方库）