# -*- coding: utf-8 -*-

def get_power(rtd_data_fan, device_id):
    power_percentage = next(
        (item['40015'] for item in rtd_data_fan['rtd_data'] if item.get('Device ID') == device_id), None)
    current_power = next(
        (item['40026'] for item in rtd_data_fan['rtd_data'] if item.get('Device ID') == device_id), None)
    return power_percentage, current_power


def check_device_status(data2):
    device_status = {}
    for entry in data2['rtd_data']:
        device_id = entry.get('Device ID')
        percent_value = entry.get('40015')
        power_value = entry.get('40026')
        if device_id and percent_value is not None and power_value is not None:
            if device_id not in device_status:
                device_status[device_id] = {
                    "percent_values": set(),
                    "power_values": set(),
                    "has_power_switch": False
                }
            device_status[device_id]["percent_values"].add(percent_value)
            if power_value == 0:
                if any(p != 0 for p in device_status[device_id]["power_values"]):
                    device_status[device_id]["has_power_switch"] = True
            else:
                if 0 in device_status[device_id]["power_values"]:
                    device_status[device_id]["has_power_switch"] = True
            device_status[device_id]["power_values"].add(power_value)
    for device_id, status in device_status.items():
        percent_values = status["percent_values"]
        has_power_switch = status["has_power_switch"]
        if len(percent_values) > 1 or has_power_switch:
            return 1
    return 0


def adjust_wind_volume_two(fan1_min, fan2_min, fan1_max, fan2_max, fan1_percent,
                           fan2_percent, fan1_power, fan2_power, increase_percent, number_value, control_):
    fan2_op = -1
    fan1_op = -1

    if number_value > 0:
        fan2_percent, fan1_percent = fan2_percent, fan1_percent
        fan2_op = 2
        fan1_op = 2
        number = number_value - 1

    elif number_value < 0:
        fan2_percent, fan1_percent = fan2_percent, fan1_percent
        fan2_op = 2
        fan1_op = 2
        number = number_value + 1

    elif increase_percent > 0 and number_value == 0:
        if fan1_power > 0 and fan1_percent <= fan1_max - increase_percent:
            fan1_percent += increase_percent
            fan1_op = 2
            number = 0

        elif fan1_power > 0 and fan1_percent > fan1_max - increase_percent and fan1_percent < fan1_max:
            fan1_percent = fan1_max
            fan1_op = 2
            number = 0

        elif fan1_power > 0 and fan1_percent >= fan1_max and fan2_power > 0 and fan2_percent <= fan2_max - increase_percent:
            fan2_percent += increase_percent
            fan2_op = 2
            number = 0

        elif fan1_power > 0 and fan1_percent >= fan1_max and fan1_power > 0 and fan2_percent > fan2_max - increase_percent and fan2_percent < fan2_max:
            fan2_percent = fan2_max
            fan2_op = 2
            number = 0

        elif fan1_power > 0 and fan1_percent >= fan1_max and fan2_power > 0 and fan2_percent >= fan2_max:
            fan1_percent = fan1_max
            fan2_percent = fan2_max
            number = 0

    elif increase_percent < 0 and number_value == 0:
        if fan2_power > 0 and fan2_percent >= fan2_min - increase_percent:
            fan2_percent += increase_percent
            fan2_op = 2
            number = 0

        elif fan2_power > 0 and fan2_percent < fan2_min - increase_percent and fan2_percent > fan2_min:
            fan2_percent = fan2_min
            fan2_op = 2
            number = 0

        elif fan2_power > 0 and fan2_percent <= fan2_min and fan1_percent >= fan1_min - increase_percent:
            fan1_percent += increase_percent
            fan1_op = 2
            number = 0

        elif fan2_power > 0 and fan2_percent <= fan2_min and fan1_percent < fan1_min - increase_percent and fan1_percent > fan1_min:
            fan1_percent = fan1_min
            fan1_op = 2
            number = 0

        elif fan2_power > 0 and fan2_percent <= fan2_min and fan1_power > 0 and fan1_percent <= fan1_min and control_ == 'OTE优化':
            fan2_percent = fan2_min
            fan1_percent = fan1_min
            fan1_op = 2
            fan2_op = 2
            number = 0

    elif increase_percent == 0 and number_value == 0:
        fan1_percent, fan2_percent, fan1_op, fan2_op = fan1_percent, fan2_percent, fan1_op, fan2_op
        number = 0

    return fan1_percent, fan2_percent, fan1_op, fan2_op, number


def adjust_wind_volume_one(fan_min, fan_max, fan_percent, fan_power, increase_percent, number_value, control_):
    fan_op = -1

    if number_value > 0:
        fan_percent = fan_percent
        fan_op = 2
        number = number_value - 1

    elif number_value < 0:
        fan_percent = fan_percent
        fan_op = 2
        number = number_value + 1

    elif increase_percent > 0 and number_value == 0:
        if fan_power > 0 and fan_percent <= fan_max - increase_percent:
            fan_percent += increase_percent
            fan_op = 2
            number = 0

        elif fan_power > 0 and fan_percent > fan_max - increase_percent and fan_percent < fan_max:
            fan_percent = fan_max
            fan_op = 2
            number = 0

    elif increase_percent < 0 and number_value == 0:
        if fan_power > 0 and fan_percent >= fan_min - increase_percent:
            fan_percent += increase_percent
            fan_op = 2
            number = 0

        elif fan_power > 0 and fan_percent < fan_min - increase_percent and fan_percent > fan_min:
            fan_percent = fan_min
            fan_op = 2
            number = 0

        elif fan_power > 0 and fan_percent <= fan_min and control_ == 'OTE优化':
            fan_percent = fan_min
            fan_op = 2
            number = 0

    elif increase_percent == 0 and number_value == 0:
        number = 0

    return fan_percent, fan_op, number