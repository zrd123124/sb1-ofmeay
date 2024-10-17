# -*- coding: utf-8 -*-
from db_handler import MongoDBHandler

mongodb_handler = MongoDBHandler("localhost", 27017, "ipc")

def get_device_info():
    device_info, rule_info, param_info, cron_ = mongodb_handler.get_device_info()
    return {
        "device_info": device_info,
        "rule_info": rule_info,
        "param_info": param_info,
        "cron_": cron_
    }

def get_rtd_data_DO():
    device_name_contains = "DO"
    extra_fields = ["DO"]
    num_to_display = 5
    output_str = mongodb_handler.get_last_rtd_data_DO(device_name_contains, extra_fields=extra_fields,
                                                   num_to_display=num_to_display)
    return {"rtd_data": output_str}

def get_rtd_data_fan(num_to_display):
    device_name_contains = "风机"
    extra_fields = ["40015", "40026"]
    output_str = mongodb_handler.get_last_rtd_data_fan(device_name_contains, extra_fields=extra_fields,
                                                   num_to_display=num_to_display)
    return {"rtd_data": output_str}

def get_rule_info(device_info, device_id):
    rule = next((item for item in device_info['rule_info'] if item.get('deviceId') == device_id), {})
    return rule.get('LCL'), rule.get('LSL'), rule.get('UCL'), rule.get('USL')

def get_do_values(rtd_data_DO, device_id):
    return [entry['DO'] for entry in rtd_data_DO['rtd_data'] if entry.get('Device ID') == device_id][:5]

def convert_and_filter(values):
    return [float(value) for value in values if
            value is not None and isinstance(value, (int, float, str)) and value != '']