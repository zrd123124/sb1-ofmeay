# -*- coding: utf-8 -*-
from flask import Flask, jsonify, send_from_directory, render_template, request
import logging
from logging.handlers import RotatingFileHandler
from Fengji_divide import *
from DO_OTE import *
from Get_imfort import *
import json

app = Flask(__name__)

# 配置文件路径
CONFIG_FILE = 'config.json'

# 读取配置文件
def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "DO1_id": "18cd8ac0-70e5-11ef-b8c6-4982de071b27",
            "DO2_id": "1cde3100-70e5-11ef-b8c6-4982de071b27"
        }

# 保存配置文件
def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

# 配置日志文件，使用 RotatingFileHandler
handler = RotatingFileHandler('error.log', maxBytes=10 * 1024 * 1024, backupCount=1)  # 10 MB大小限制，保留1个备份
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(logging.ERROR)
logger.addHandler(handler)

# 在出错时记录日志
@app.errorhandler(Exception)
def log_error(error):
    logging.error(f'Error occurred: {str(error)}')
    # 读取并保留最新的500条日志记录
    with open('error.log', 'r') as f:
        lines = f.readlines()
    with open('error.log', 'w') as f:
        f.writelines(lines[-500:])
    return 'Internal Server Error', 500

@app.route('/', methods=['GET', 'POST'])
def config_page():
    config = load_config()
    if request.method == 'POST':
        config['DO1_id'] = request.form.get('DO1_id', config['DO1_id'])
        config['DO2_id'] = request.form.get('DO2_id', config['DO2_id'])
        save_config(config)
        return render_template('config.html', DO1_id=config['DO1_id'], DO2_id=config['DO2_id'], message="Configuration updated successfully!")
    return render_template('config.html', DO1_id=config['DO1_id'], DO2_id=config['DO2_id'])

@app.route('/api/receive_params', methods=['GET'])
def receive_params():
    # 读取配置文件
    config = load_config()
    DO1_id = config['DO1_id']
    DO2_id = config['DO2_id']

    # 获取设备信息和最近的实时数据
    device_info = get_device_info()
    rtd_data_DO = get_rtd_data_DO()  # 获取最近的 DO 数据
    rtd_data_风机 = get_rtd_data_FengJi(1)  # 获取最近的风机数据
    # 定义控制算法和调度周期
    control_ = "智控算法"
    cron_ = int(device_info['cron_'])

    # 获取设备的 JSON 数据
    json_data = device_info["device_info"]

    # 提取风机1、风机2 和 风机3的 ID、最小值和最大值
    (风机1_id, 风机2_id, 风机3_id), (风机1_min, 风机2_min, 风机3_min), (风机1_max, 风机2_max, 风机3_max) = (
        [json_data[i][key] for i in range(3)] for key in ["id", "min", "max"]
    )
    # 获取风机1、风机2 和 风机3的当前百分比和功率
    风机1_percent, 风机1_power = get_power(rtd_data_风机, 风机1_id)
    风机2_percent, 风机2_power = get_power(rtd_data_风机, 风机2_id)
    风机3_percent, 风机3_power = get_power(rtd_data_风机, 风机3_id)
    # 将风机的最小值、最大值、百分比和功率转换为整数
    风机1_min, 风机2_min, 风机3_min, 风机1_max, 风机2_max, 风机3_max = map(int, [风机1_min, 风机2_min, 风机3_min, 风机1_max, 风机2_max, 风机3_max])
    风机1_percent, 风机2_percent, 风机3_percent, 风机1_power, 风机2_power, 风机3_power = map(int, [
        风机1_percent, 风机2_percent, 风机3_percent, 风机1_power, 风机2_power, 风机3_power
    ])
    # 获取 DO1 和 DO2 的控制限值（LCL、LSL、UCL、USL）和实测值
    (DO1_LCL, DO1_LSL, DO1_UCL, DO1_USL), (DO2_LCL, DO2_LSL, DO2_UCL, DO2_USL) = (
        convert_and_filter(get_rule_info(device_info, DO_id)) for DO_id in [DO1_id, DO2_id]
    )
    DO1_values, DO2_values = (convert_and_filter(get_do_values(rtd_data_DO, DO_id)) for DO_id in [DO1_id, DO2_id])
    # 获取优化轮数和增减量优化参数
    优化轮数, 增量优化, 减量优化 = (
        int(next((item for item in device_info['param_info'] if item.get('name') == name), {}).get('val'))
        for name in ['OTE优化', '增量优化', '减量优化']
    )

    容忍度 = float(next((item for item in device_info['param_info'] if item.get('name') == '容忍度'), {}).get('val'))

    # 检查优化状态，确定 OTE 优化参数
    OTE优化 = int(check_device_status(get_rtd_data_FengJi(优化轮数 * cron_ - 1)))
    # 判断主控制区间并记录日志
    huan_xun_value, number_value = mongodb_handler.ControlLog()  # 记录日志

    # 计算 DO1 和 DO2 的实测值
    DO1_实测 = sum(DO1_values) / len(DO1_values)
    DO2_实测 = sum(DO2_values) / len(DO2_values)
    # 确定风量调整百分比和控制策略
    increase_percent, control_ = determine_adjustment_Dochange(DO1_LCL, DO1_LSL, DO1_UCL, DO1_USL, DO2_LCL,
                                                               DO2_LSL, DO2_UCL, DO2_USL, DO1_实测,
                                                               DO2_实测, OTE优化, control_, huan_xun_value, 容忍度)
    # 检查每台风机是否在线（percent和power都为-1表示不在线）
    风机1在线 = not (风机1_percent == -1 and 风机1_power == -1)
    风机2在线 = not (风机2_percent == -1 and 风机2_power == -1)
    风机3在线 = not (风机3_percent == -1 and 风机3_power == -1)
    logs = []

    # 判断在线风机数量
    在线风机数量 = sum([风机1在线, 风机2在线, 风机3在线])
    print(在线风机数量)

    # 如果有2台风机在线，调用对应的2台风机调控函数，优先顺序：3 > 2 > 1
    if 在线风机数量 >= 2:
        if 风机3在线 and 风机2在线:
            新风机3_百分比, 新风机2_百分比, 风机3_op, 风机2_op, number = adjust_wind_volume_two(
                风机3_min, 风机2_min, 风机3_max, 风机2_max,
                风机3_percent, 风机2_percent,
                风机3_power, 风机2_power,
                increase_percent, int(number_value), control_)
            if 风机3_op != -1:
                logs.append({"deviceId": 风机3_id, "op": 风机3_op, "fl": 新风机3_百分比})
            if 风机2_op != -1:
                logs.append({"deviceId": 风机2_id, "op": 风机2_op, "fl": 新风机2_百分比})
        elif 风机3在线 and 风机1在线:
            新风机3_百分比, 新风机1_百分比, 风机3_op, 风机1_op, number = adjust_wind_volume_two(
                风机3_min, 风机1_min, 风机3_max, 风机1_max,
                风机3_percent, 风机1_percent,
                风机3_power, 风机1_power,
                increase_percent, int(number_value), control_)
            if 风机3_op != -1:
                logs.append({"deviceId": 风机3_id, "op": 风机3_op, "fl": 新风机3_百分比})
            if 风机1_op != -1:
                logs.append({"deviceId": 风机1_id, "op": 风机1_op, "fl": 新风机1_百分比})
        elif 风机2在线 and 风机1在线:
            新风机2_百分比, 新风机1_百分比, 风机2_op, 风机1_op, number = adjust_wind_volume_two(
                风机2_min, 风机1_min, 风机2_max, 风机1_max,
                风机2_percent, 风机1_percent,
                风机2_power, 风机1_power,
                increase_percent, int(number_value), control_)
            if 风机2_op != -1:
                logs.append({"deviceId": 风机2_id, "op": 风机2_op, "fl": 新风机2_百分比})
            if 风机1_op != -1:
                logs.append({"deviceId": 风机1_id, "op": 风机1_op, "fl": 新风机1_百分比})

    # 如果有1台风机在线，调用对应的1台风机调控函数，优先顺序：3 > 2 > 1
    elif 在线风机数量 == 1:
        if 风机3在线:
            新风机3_百分比, 风机3_op, number = adjust_wind_volume_one(
                风机3_min, 风机3_max, 风机3_percent, 风机3_power,
                increase_percent, int(number_value), control_)
            if 风机3_op != -1:
                logs.append({"deviceId": 风机3_id, "op": 风机3_op, "fl": 新风机3_百分比})
        elif 风机2在线:
            新风机2_百分比, 风机2_op, number = adjust_wind_volume_one(
                风机2_min, 风机2_max, 风机2_percent, 风机2_power,
                increase_percent, int(number_value), control_)
            if 风机2_op != -1:
                logs.append({"deviceId": 风机2_id, "op": 风机2_op, "fl": 新风机2_百分比})
        elif 风机1在线:
            新风机1_百分比, 风机1_op, number = adjust_wind_volume_one(
                风机1_min, 风机1_max, 风机1_percent, 风机1_power,
                increase_percent, int(number_value), control_)
            if 风机1_op != -1:
                logs.append({"deviceId": 风机1_id, "op": 风机1_op, "fl": 新风机1_百分比})
    # 构建返回的数据字典
    data = {
        "logs": logs,
        "rtdData": {
            "DO中": f"{round(DO1_实测, 2):.2f}",  # 返回 DO1 实测值，保留两位小数
            "DO末": f"{round(DO2_实测, 2):.2f}",  # 返回 DO2 实测值，保留两位小数
            "环浔": str(control_),  # 返回控制策略
            "number": str(number)  # 返回调整后的 number 值
        }
    }
    print(data)
    return data  # 返回数据

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False, use_debugger=False)