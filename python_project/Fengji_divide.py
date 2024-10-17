# -*- coding: utf-8 -*-

# 获取powerpercent和当前power
def get_power(rtd_data_fengji, device_id):
    power_percentage = next(
        (item['40015'] for item in rtd_data_fengji['rtd_data'] if item.get('Device ID') == device_id), None)
    current_power = next(
        (item['40026'] for item in rtd_data_fengji['rtd_data'] if item.get('Device ID') == device_id), None)
    return power_percentage, current_power


def check_device_status(data2):
    # 设备状态字典，记录每个设备的 `40015` 和 `40026` 的值
    device_status = {}
    # 遍历设备数据
    for entry in data2['rtd_data']:
        device_id = entry.get('Device ID')
        percent_value = entry.get('40015')
        power_value = entry.get('40026')
        # 检查记录中是否包含有效的 `Device ID`
        if device_id and percent_value is not None and power_value is not None:
            if device_id not in device_status:
                device_status[device_id] = {
                    "percent_values": set(),
                    "power_values": set(),
                    "has_power_switch": False
                }
            # 记录 `40015` 的数值
            device_status[device_id]["percent_values"].add(percent_value)
            # 检查 `40026` 是否从 0 到非 0 或从非 0 到 0 的变化
            if power_value == 0:
                if any(p != 0 for p in device_status[device_id]["power_values"]):
                    device_status[device_id]["has_power_switch"] = True
            else:
                if 0 in device_status[device_id]["power_values"]:
                    device_status[device_id]["has_power_switch"] = True
            # 记录 `40026` 的数值
            device_status[device_id]["power_values"].add(power_value)
    # 判断每个设备的状态
    for device_id, status in device_status.items():
        percent_values = status["percent_values"]
        has_power_switch = status["has_power_switch"]
        # 如果 `40015` 发生过变化或者 `40026` 有开关机变化
        if len(percent_values) > 1 or has_power_switch:
            return 1  # 如果任意一个设备发生变化，返回1
    return 0  # 如果所有设备的状态都没有变化，返回0


# 根据增减风量的需求执行操作
def adjust_wind_volume_two(风机1_min, 风机2_min, 风机1_max, 风机2_max, 风机1_percent,
                           风机2_percent, 风机1_power, 风机2_power, increase_percent, number_value, control_):
    风机2_op = -1  # 风机2操作状态初始化为-1，表示无操作
    风机1_op = -1  # 风机2操作状态初始化为-1，表示无操作

    # 情况1：number_value > 0，表示有特定的增量操作需求
    if number_value > 0:
        风机2_percent, 风机1_percent = 风机2_percent, 风机1_percent  # 风机2和风机2的百分比保持不变
        风机2_op = 2  # 设置风机2的操作状态为2，表示进行增量操作
        风机1_op = 2  # 设置风机2的操作状态为2，表示进行增量操作
        number = number_value - 1  # 将number_value减少1

    # 情况2：number_value < 0，表示有特定的减量操作需求
    elif number_value < 0:
        风机2_percent, 风机1_percent = 风机2_percent, 风机1_percent  # 风机2和风机2的百分比保持不变
        风机2_op = 2  # 设置风机2的操作状态为2，表示进行增量操作
        风机1_op = 2  # 设置风机2的操作状态为2，表示进行增量操作
        number = number_value + 1  # 将number_value增加1

    # 情况3：增加风量需求（increase_percent > 0 且 number_value == 0）
    elif increase_percent > 0 and number_value == 0:
        # 风机2在有电的情况下且当前百分比未达到最大值
        if 风机1_power > 0 and 风机1_percent <= 风机1_max - increase_percent:
            风机1_percent += increase_percent  # 增加风机1的百分比
            风机1_op = 2  # 设置风机2的操作状态为2
            number = 0  # number保持为0

        # 风机2在有电的情况下且当前百分比接近最大值
        elif 风机1_power > 0 and 风机1_percent > 风机1_max - increase_percent and 风机1_percent < 风机1_max:
            风机1_percent = 风机1_max  # 将风机2的百分比设置为最大值
            风机1_op = 2  # 设置风机2的操作状态为2
            number = 0  # number保持为0

        # 风机2和风机2都运行，且风机2可以增加风量
        elif 风机1_power > 0 and 风机1_percent >= 风机1_max and 风机2_power > 0 and 风机2_percent <= 风机2_max - increase_percent:
            风机2_percent += increase_percent  # 增加风机2的百分比
            风机2_op = 2  # 设置风机2的操作状态为2
            number = 0  # number保持为0

        # 风机2和风机2都运行，且风机2接近最大风量
        elif 风机1_power > 0 and 风机1_percent >= 风机1_max and 风机1_power > 0 and 风机2_percent > 风机2_max - increase_percent and 风机2_percent < 风机2_max:
            风机2_percent = 风机2_max  # 将风机2的百分比设置为最大值
            风机2_op = 2  # 设置风机2的操作状态为2
            number = 0  # number保持为0

        # 风机2和风机2都达到最大风量
        elif 风机1_power > 0 and 风机1_percent >= 风机1_max and 风机2_power > 0 and 风机2_percent >= 风机2_max:
            风机1_percent = 风机1_max  # 风机2保持在最大值
            风机2_percent = 风机2_max  # 风机2保持在最大值
            number = 0  # number保持为0

    # 情况4：减少风量需求（increase_percent < 0 且 number_value == 0）
    elif increase_percent < 0 and number_value == 0:
        # 风机2在有电的情况下且当前百分比高于最小值
        if 风机2_power > 0 and 风机2_percent >= 风机2_min - increase_percent:
            风机2_percent += increase_percent  # 减少风机2的百分比
            风机2_op = 2  # 设置风机2的操作状态为2
            number = 0  # number保持为0

        # 风机2在有电的情况下且当前百分比接近最小值
        elif 风机2_power > 0 and 风机2_percent < 风机2_min - increase_percent and 风机2_percent > 风机2_min:
            风机2_percent = 风机2_min  # 将风机2的百分比设置为最小值
            风机2_op = 2  # 设置风机2的操作状态为2
            number = 0  # number保持为0

        # 风机2已达最小值，风机2减少风量
        elif 风机2_power > 0 and 风机2_percent <= 风机2_min and 风机1_percent >= 风机1_min - increase_percent:
            风机1_percent += increase_percent  # 减少风机2的百分比
            风机1_op = 2  # 设置风机2的操作状态为2
            number = 0  # number保持为0

        # 风机2已达最小值，风机2接近最小风量
        elif 风机2_power > 0 and 风机2_percent <= 风机2_min and 风机1_percent < 风机1_min - increase_percent and 风机1_percent > 风机1_min:
            风机1_percent = 风机1_min  # 将风机2的百分比设置为最小值
            风机1_op = 2  # 设置风机2的操作状态为2
            number = 0  # number保持为0

        # 风机2已达最小值，且风机2操作满足OTE优化条件
        elif 风机2_power > 0 and 风机2_percent <= 风机2_min and 风机1_power > 0 and 风机1_percent <= 风机1_min and control_ == 'OTE优化':
            风机2_percent = 风机2_min  # 风机2保持最小值
            风机1_percent = 风机1_min  # 风机2保持最小值
            风机1_op = 2  # 设置风机2的操作状态为2
            风机2_op = 2  # 设置风机2的操作状态为2
            number = 0  # number保持为0

    # 情况6：没有增减风量需求（increase_percent == 0 且 number_value == 0）
    elif increase_percent == 0 and number_value == 0:
        # 保持当前风机2和风机2的风量和操作状态不变
        风机1_percent, 风机2_percent, 风机1_op, 风机2_op = 风机1_percent, 风机2_percent, 风机1_op, 风机2_op
        number = 0  # number保持为0，表示无任何操作需求

    return 风机1_percent, 风机2_percent, 风机1_op, 风机2_op, number


# 根据增减风量的需求执行操作
def adjust_wind_volume_one(风机_min, 风机_max, 风机_percent, 风机_power, increase_percent, number_value, control_):
    风机_op = -1  # 风机操作状态初始化为-1，表示无操作

    # 情况1：number_value > 0，表示有特定的增量操作需求
    if number_value > 0:
        风机_percent = 风机_percent
        风机_op = 2  # 设置风机的操作状态为2，表示进行增量操作
        number = number_value - 1  # 将number_value减少1

    # 情况2：number_value < 0，表示有特定的减量操作需求
    elif number_value < 0:
        风机_percent = 风机_percent
        风机_op = 2  # 设置风机的操作状态为2，表示进行减量操作
        number = number_value + 1  # 将number_value增加1

    # 情况3：增加风量需求（increase_percent > 0 且 number_value == 0）
    elif increase_percent > 0 and number_value == 0:
        if 风机_power > 0 and 风机_percent <= 风机_max - increase_percent:
            风机_percent += increase_percent  # 增加风机的百分比
            风机_op = 2  # 设置风机的操作状态为2
            number = 0  # number保持为0


        elif 风机_power > 0 and 风机_percent > 风机_max - increase_percent and 风机_percent < 风机_max:
            风机_percent = 风机_max  # 将风机的百分比设置为最大值
            风机_op = 2  # 设置风机的操作状态为2
            number = 0  # number保持为0

    # 情况4：减少风量需求（increase_percent < 0 且 number_value == 0）
    elif increase_percent < 0 and number_value == 0:
        if 风机_power > 0 and 风机_percent >= 风机_min - increase_percent:
            风机_percent += increase_percent  # 减少风机的百分比
            风机_op = 2  # 设置风机的操作状态为2
            number = 0  # number保持为0

        elif 风机_power > 0 and 风机_percent < 风机_min - increase_percent and 风机_percent > 风机_min:
            风机_percent = 风机_min  # 将风机的百分比设置为最小值
            风机_op = 2  # 设置风机的操作状态为2
            number = 0  # number保持为0

        # 风机2已达最小值，且风机2操作满足OTE优化条件
        elif 风机_power > 0 and 风机_percent <= 风机_min and control_ == 'OTE优化':
            风机_percent = 风机_min  # 风机2保持最小值
            风机_op = 2  # 设置风机2的操作状态为2
            number = 0  # number保持为0

    # 情况5：没有增减风量需求（increase_percent == 0 且 number_value == 0）
    elif increase_percent == 0 and number_value == 0:
        # 保持当前风机的风量和操作状态不变
        number = 0  # number保持为0，表示无任何操作需求

    return 风机_percent, 风机_op, number