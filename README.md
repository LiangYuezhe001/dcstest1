项目概述
DCS 数据监控工具是一款用于监控数字战斗模拟（DCS）游戏内实体数据的客户端工具。通过 TCP 连接 DCS 服务器，发送预定义的 API 命令获取实体信息，经解析后以表格形式可视化展示，支持实时更新与调试分析。
核心模块详解
1. dcs_api_definitions.py - API 定义模块
用途：存储所有 DCS API 的元数据，作为客户端与服务器通信的 "协议字典"，是整个工具的通信基础。

核心内容：

DCS_APIS：列表类型，包含多个 API 定义字典，每个字典描述一个 API 的详细信息：
id：API 唯一标识（整数，如 52 对应获取实体数据的命令）
returns_data：是否返回数据（布尔值，用于判断是否需要解析响应）
api_syntax：API 语法字符串（如 LoGetSelfData() 表示获取自身数据）
parameter_count：参数数量（整数，如 1 表示该 API 需要 1 个参数）
parameter_defs：参数定义列表（包含参数 id、name、type，type=0 为数字，type=1 为字符串）
result_type：返回值类型（默认 nil）
2. dcs_api_parser.py - API 解析模块
用途：将 dcs_api_definitions.py 中的原始 API 定义转换为可操作的对象，负责参数解析与序列化。

核心类与函数：

ParameterType：枚举类，定义参数类型（NUMBER=0、STRING=1）
DCSAPI：API 对象类，封装 API 的属性和操作：
__init__：初始化 API 对象（接收 id、returns_data 等参数）
_parse_parameters：将原始参数定义解析为结构化字典（包含 id、name、value、type）
to_dict：转换为字典，用于 JSON 序列化（网络传输时使用）
set_parameter_value：按参数名设置值（如为 LoGetObjectById 传入 object_id）
create_api_from_dict：从字典数据创建 DCSAPI 对象
load_predefined_apis：加载 DCS_APIS 列表并转换为 DCSAPI 对象列表
3. dcs_network.py - 网络通信模块
用途：实现底层 TCP Socket 通信，负责与 DCS 服务器建立连接、发送数据和接收数据。

核心类：DCSNetwork

初始化参数：host（服务器地址，默认 127.0.0.1）、port（端口，默认 7777）
主要方法：
connect()：建立 TCP 连接，返回连接结果（True/False）
disconnect()：关闭连接并清理资源
send_data(data: bytes)：发送字节数据到服务器，返回发送结果
start_listening(stop_event)：在独立线程中监听服务器响应，通过 data_received_callback 传递接收的数据
属性：is_connected：返回当前连接状态（布尔值）
4. dcs_command_processor.py - 命令处理模块
用途：管理 API 命令队列，确保命令有序发送（避免网络拥塞），并处理响应回调。

核心类：DCSCommandProcessor

主要方法：
queue_command(api: DCSAPI, params: Dict)：将 API 命令加入队列，设置参数（可选），返回入队结果
send_next_command()：发送队列中的下一个命令（通过 send_data_callback 调用网络模块发送）
mark_response_received()：标记上一个命令的响应已接收，触发下一个命令发送
5. dcs_event_handler.py - 事件处理模块
用途：管理各类事件回调（连接状态、数据接收、错误），实现模块间解耦（如网络模块与显示模块无需直接依赖）。

核心类：DCSEventHandler

回调属性：
on_connection_changed：连接状态变化回调（参数：connected: bool）
on_api_data_received：API 数据接收回调（参数：api: DCSAPI，包含解析后的响应）
on_error_received：错误事件回调（参数：error_type: str, message: str）
触发方法：
trigger_connection_changed(connected)：触发连接状态变化事件
trigger_api_data_received(api)：触发数据接收事件
trigger_error_received(error_type, message)：触发错误事件
6. dcs_client.py - 客户端核心模块
用途：整合网络、命令处理、事件处理等子模块，提供高层 API 调用接口，是工具与服务器交互的核心入口。

核心类：DCSClient

初始化参数：host、port、log_level（日志级别）
主要方法：
connect()：连接服务器，启动监听线程，返回连接结果
disconnect()：断开连接，停止监听线程
send_command(api_id: int, params: Dict = None)：发送指定 ID 的 API 命令（带参数），返回发送结果
get_api(api_id: int = None, api_name: str = None)：根据 ID 或语法查找 API 对象
get_apis_matching(pattern: str)：查找语法包含指定模式的 API 列表
属性：is_connected：返回当前连接状态
7. dcs_data_parser.py - 数据解析模块
用途：将服务器返回的原始数据字符串（如嵌套格式的实体信息）解析为结构化字典，供显示模块使用。

核心类：DCSDataParser

主要方法：
parse_data(data: str)：将原始字符串解析为实体对象列表（每个对象为字典，包含 id、Name、LatLongAlt 等字段）
支持嵌套数据解析（如坐标、类型等多层结构）
8. dcs_display.py - 显示格式化模块
用途：将解析后的实体数据以表格形式格式化展示，支持调试信息打印。

核心类：DCSDisplayFormatter

初始化参数：debug（是否开启调试模式，默认 False）
主要方法：
display_objects(objects: List[Dict], update_interval: float)：以表格形式显示实体数据（包含 ID、名称、国家、位置等）
print_debug_info(raw_data: str, parsed_objects: List[Dict])：调试模式下打印原始数据和解析后的详细结构
辅助方法：坐标格式化（保留小数点后两位）、文本截断（防止表格错位）、国家 / 联盟名称映射
9. main.py / test2.py - 主程序入口
用途：整合客户端、数据解析和显示模块，实现完整的 DCS 实体监控流程。

核心类：DCSObjectDisplay

初始化参数：host、port、update_interval（数据更新间隔，默认 5 秒）、debug（调试模式）
主要方法：
start()：启动监控流程（连接服务器 → 定时发送 API 命令 → 接收数据 → 解析 → 显示）
stop()：停止监控（断开连接、清理线程资源）
回调处理：通过 _on_connection_changed 处理连接状态变化，_on_api_data_received 处理数据接收并触发显示