# -*- coding: utf-8 -*-
# Initialize MongoDBHandler instance
from Mongo_Connect import MongoDBHandler

mongodb_handler = MongoDBHandler("localhost", 27017, "ipc")
# 获取设备信息，包括设备详情、规则信息、参数信息和定时任务设置
def get_device_info():
    # 从 MongoDB 获取设备信息
    device_info, rule_info, param_info, cron_ = mongodb_handler.get_device_info()
    # 将设备信息以字典的形式返回
    return {
        "device_info": device_info,  # 设备详情
        "rule_info": rule_info,      # 规则信息
        "param_info": param_info,    # 参数信息
        "cron_": cron_               # 定时任务设置
    }

# 获取最近的DO设备的实时数据
def get_rtd_data_DO():
    device_name_contains = "DO"  # 设备名称中包含"DO"的设备
    extra_fields = ["DO"]        # 需要额外获取的字段
    num_to_display = 5           # 显示的记录条数
    # 从 MongoDB 获取最近的实时数据
    output_str = mongodb_handler.get_last_rtd_data_DO(device_name_contains, extra_fields=extra_fields,
                                                   num_to_display=num_to_display)
    # 将实时数据以字典的形式返回
    return {"rtd_data": output_str}

# 获取最近的风机设备的实时数据
def get_rtd_data_FengJi(num_to_display):
    device_name_contains = "风机"  # 设备名称中包含"风机"的设备
    extra_fields = ["40015", "40026"]  # 需要额外获取的字段
    # 从 MongoDB 获取最近的实时数据
    output_str = mongodb_handler.get_last_rtd_data_FengJi(device_name_contains, extra_fields=extra_fields,
                                                   num_to_display=num_to_display)
    # 将实时数据以字典的形式返回
    return {"rtd_data": output_str}

# 获取指定DO设备的规则信息
def get_rule_info(device_info, device_id):
    # 遍历设备信息中的规则信息，找到匹配的设备ID的规则
    rule = next((item for item in device_info['rule_info'] if item.get('deviceId') == device_id), {})
    # 返回该设备的 LCL (下限控制界限)、LSL (下限设定值)、UCL (上限控制界限) 和 USL (上限设定值)
    return rule.get('LCL'), rule.get('LSL'), rule.get('UCL'), rule.get('USL')

# 获取指定DO设备的实时数值
def get_do_values(rtd_data_DO, device_id):
    # 过滤实时数据中指定设备ID的数据，并获取其中的DO数值，限制为最近的5个数值
    return [entry['DO'] for entry in rtd_data_DO['rtd_data'] if entry.get('Device ID') == device_id][:5]

# 将字符串数值转换为浮点型，并过滤掉无效值
def convert_and_filter(values):
    # 将所有值转换为 float 类型，并去除 None 和空字符串等无效值
    return [float(value) for value in values if
            value is not None and isinstance(value, (int, float, str)) and value != '']