def parse_dcs_data(raw_data: str) -> dict:
    """解析DCS格式的缩进数据为嵌套字典"""
    # 预处理：去除空行和首尾空格
    lines = [line.rstrip() for line in raw_data.strip().split('\n') if line.strip()]
    if not lines:
        return {}
    
    # 提取根ID
    root_line = lines[0]
    root_id = root_line.split(':', 1)[0].strip()
    result = {root_id: {}}
    
    # 处理剩余行（从根节点的子节点开始）
    current_level = 0
    stack = [(result[root_id], current_level)]  # 栈元素: (当前字典, 当前缩进级别)
    
    for line in lines[1:]:
        # 计算当前行的缩进级别（只计算开头的空格和制表符）
        indent = len(line) - len(line.lstrip(' \t'))
        current_line = line.lstrip(' \t')
        
        # 分割键和值（处理"键: 值"格式）
        if ': ' in current_line:
            key, value = current_line.split(': ', 1)
            key = key.strip()
            
            # 判断值是否为空（为空则可能是嵌套节点）
            if not value.strip():
                # 是嵌套节点，创建新字典
                new_dict = {}
                # 找到当前层级的父节点
                while stack and stack[-1][1] >= indent:
                    stack.pop()
                parent_dict, parent_level = stack[-1]
                parent_dict[key] = new_dict
                stack.append((new_dict, indent))
            else:
                # 是普通值，转换类型
                parsed_value = value.strip()
                # 尝试转换为数字
                if parsed_value.replace('.', '', 1).replace('-', '', 1).isdigit():
                    if '.' in parsed_value:
                        parsed_value = float(parsed_value)
                    else:
                        parsed_value = int(parsed_value)
                # 找到当前层级的父节点
                while stack and stack[-1][1] >= indent:
                    stack.pop()
                parent_dict, _ = stack[-1]
                parent_dict[key] = parsed_value
    
    return result


# 待解析的原始数据
raw_data = """16785664:
	Pitch: 0.10128597915173
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
			y: 0.99487429857254
			x: -0.06228144094348
			z: 0.99487429857254
		x:
			y: 0.10112025588751
			x: 0.61243462562561
			z: 0.10112025588751
		p:
			y: 9448.8081648943
			x: -324252.80122934
			z: 9448.8081648943
		z:
			y: -4.1414052248001e-05
			x: -0.78806400299072
			z: -4.1414052248001e-05
	Coalition: Enemies
	Heading: 0.90765762329102
	Name: C-17A
	Position:
		y: 9448.8081648943
		x: -324252.80122934
		z: 569010.54678577
	UnitName: Pilot #006
	LatLongAlt:
		Long: 41.060995231004
		Lat: 41.932888897004
		Alt: 9448.8081648943
	CoalitionID: 2
	Bank: 4.1403265640838e-05
16785920:
	Pitch: 0.10128603130579
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
			y: 0.99487429857254
			x: -0.097415626049042
			z: 0.99487429857254
		x:
			y: 0.10112032294273
			x: 0.95846480131149
			z: 0.10112032294273
		p:
			y: 9448.8081998392
			x: -294348.80609856
			z: 9448.8081998392
		z:
			y: -1.4906749129295e-05
			x: 0.26805859804153
			z: -1.4906749129295e-05
	Coalition: Enemies
	Heading: 6.0118082165718
	Name: C-17A
	Position:
		y: 9448.8081998392
		x: -294348.80609856
		z: 913664.77003354
	UnitName: Pilot #007
	LatLongAlt:
		Long: 45.192363792829
		Lat: 41.833454148847
		Alt: 9448.8081998392
	CoalitionID: 2
	Bank: 1.485484517616e-05
16778496:
	Pitch: 0.058255858719349
	Type:
		level3: 6
		level1: 1
		level4: 283
		level2: 1
	Country: 16
	Flags:
	GroupName: Kutaisi #003
	PositionAsMatrix:
		y:
			y: 0.99830347299576
			x: -0.048772864043713
			z: 0.99830347299576
		x:
			y: 0.058227173984051
			x: 0.83692288398743
			z: 0.058227173984051
		p:
			y: 914.40844992718
			x: -285251.66280719
			z: 914.40844992718
		z:
			y: -7.619708776474e-05
			x: 0.54514360427856
			z: -7.619708776474e-05
	Coalition: Enemies
	Heading: 5.7066251039505
	Name: L-39C
	Position:
		y: 914.40844992718
		x: -285251.66280719
		z: 686755.2483111
	UnitName: Pilot #066
	LatLongAlt:
		Long: 42.51539253616
		Lat: 42.171489625429
		Alt: 914.40844992718
	CoalitionID: 2
	Bank: 7.6330652518664e-05
16778752:
	Pitch: 0.23316149413586
	Type:
		level3: 6
		level1: 1
		level4: 283
		level2: 1
	Country: 16
	Flags:
	GroupName: Kutaisi #001
	PositionAsMatrix:
		y:
			y: 0.97292983531952
			x: 0.066541619598866
			z: 0.97292983531952
		x:
			y: 0.23106043040752
			x: -0.26225820183754
			z: 0.23106043040752
		p:
			y: 213.98648137128
			x: -285208.82552524
			z: 213.98648137128
		z:
			y: -0.004303365945816
			x: 0.96270084381104
			z: -0.004303365945816
	Coalition: Enemies
	Heading: 4.438903927803
	Name: L-39C
	Position:
		y: 213.98648137128
		x: -285208.82552524
		z: 682786.73176767
	UnitName: Pilot #072
	LatLongAlt:
		Long: 42.468059506824
		Lat: 42.175827397508
		Alt: 213.98648137128
	CoalitionID: 2
	Bank: 0.0046975100412965
16779008:
	Pitch: 0.23312826454639
	Type:
		level3: 6
		level1: 1
		level4: 283
		level2: 1
	Country: 16
	Flags:
	GroupName: Kutaisi #001
	PositionAsMatrix:
		y:
			y: 0.97294366359711
			x: 0.064729958772659
			z: 0.97294366359711
		x:
			y: 0.23103246092796
			x: -0.26355981826782
			z: 0.23103246092796
		p:
			y: 202.76801821256
			x: -285156.61573589
			z: 202.76801821256
		z:
			y: -0.0021691359579563
			x: 0.96246892213821
			z: -0.0021691359579563
	Coalition: Enemies
	Heading: 4.437805056572
	Name: L-39C
	Position:
		y: 202.76801821256
		x: -285156.61573589
		z: 682888.8776059
	UnitName: Pilot #073
	LatLongAlt:
		Long: 42.46934924551
		Lat: 42.176189584091
		Alt: 202.76801821256
	CoalitionID: 2
	Bank: 0.0021990563254803
16779264:
	Pitch: -0.0078540937975049
	Type:
		level3: 5
		level1: 1
		level4: 39
		level2: 1
	Country: 16
	Flags:
	GroupName: Kutaisi #002
	PositionAsMatrix:
		y:
			y: 0.99996852874756
			x: -0.0052353036589921
			z: 0.99996852874756
		x:
			y: -0.007931187748909
			x: -0.66451162099838
			z: -0.007931187748909
		p:
			y: 47.685340881348
			x: -284170.37512449
			z: 47.685340881348
		z:
			y: -4.7141220420599e-05
			x: 0.74725961685181
			z: -4.7141220420599e-05
	Coalition: Enemies
	Heading: 3.9914650917053
	Name: An-26B
	Position:
		y: 47.685340881348
		x: -284170.37512449
		z: 684938.42160339
	UnitName: Pilot #074
	LatLongAlt:
		Long: 42.495148088269
		Lat: 42.182908502042
		Alt: 47.685340881348
	CoalitionID: 2
	Bank: -0"""

# 执行解析
parsed_dict = parse_dcs_data(raw_data)

# 打印解析结果（完整字典）
import pprint
print("解析后的完整字典：")
pprint.pprint(parsed_dict, indent=2)
