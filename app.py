import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, render_template, request
from fan_control import *
from do_ote import *
from data_retrieval import *
import json
import threading
import time

app = Flask(__name__)

# Configuration file path
CONFIG_FILE = 'config.json'

# Load configuration
def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "DO1_id": "18cd8ac0-70e5-11ef-b8c6-4982de071b27",
            "DO2_id": "1cde3100-70e5-11ef-b8c6-4982de071b27",
            "algorithm_running": False
        }

# Save configuration
def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

# Configure logging
handler = RotatingFileHandler('error.log', maxBytes=10 * 1024 * 1024, backupCount=1)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(logging.ERROR)
logger.addHandler(handler)

@app.errorhandler(Exception)
def log_error(error):
    logging.error(f'Error occurred: {str(error)}')
    with open('error.log', 'r') as f:
        lines = f.readlines()
    with open('error.log', 'w') as f:
        f.writelines(lines[-500:])
    return 'Internal Server Error', 500

def run_algorithm():
    while True:
        config = load_config()
        if config['algorithm_running']:
            receive_params()
        time.sleep(60)  # Run every minute

@app.route('/api/receive_params', methods=['GET'])
def receive_params():
    config = load_config()
    DO1_id = config['DO1_id']
    DO2_id = config['DO2_id']

    device_info = get_device_info()
    rtd_data_DO = get_rtd_data_DO()
    rtd_data_fan = get_rtd_data_fan(1)
    control_ = "智控算法"
    cron_ = int(device_info['cron_'])

    json_data = device_info["device_info"]

    (fan1_id, fan2_id, fan3_id), (fan1_min, fan2_min, fan3_min), (fan1_max, fan2_max, fan3_max) = (
        [json_data[i][key] for i in range(3)] for key in ["id", "min", "max"]
    )
    fan1_percent, fan1_power = get_power(rtd_data_fan, fan1_id)
    fan2_percent, fan2_power = get_power(rtd_data_fan, fan2_id)
    fan3_percent, fan3_power = get_power(rtd_data_fan, fan3_id)
    fan1_min, fan2_min, fan3_min, fan1_max, fan2_max, fan3_max = map(int, [fan1_min, fan2_min, fan3_min, fan1_max, fan2_max, fan3_max])
    fan1_percent, fan2_percent, fan3_percent, fan1_power, fan2_power, fan3_power = map(int, [
        fan1_percent, fan2_percent, fan3_percent, fan1_power, fan2_power, fan3_power
    ])
    (DO1_LCL, DO1_LSL, DO1_UCL, DO1_USL), (DO2_LCL, DO2_LSL, DO2_UCL, DO2_USL) = (
        convert_and_filter(get_rule_info(device_info, DO_id)) for DO_id in [DO1_id, DO2_id]
    )
    DO1_values, DO2_values = (convert_and_filter(get_do_values(rtd_data_DO, DO_id)) for DO_id in [DO1_id, DO2_id])
    optimization_rounds, increase_optimization, decrease_optimization = (
        int(next((item for item in device_info['param_info'] if item.get('name') == name), {}).get('val'))
        for name in ['OTE优化', '增量优化', '减量优化']
    )

    tolerance = float(next((item for item in device_info['param_info'] if item.get('name') == '容忍度'), {}).get('val'))

    OTE_optimization = int(check_device_status(get_rtd_data_fan(optimization_rounds * cron_ - 1)))
    huan_xun_value, number_value = mongodb_handler.ControlLog()

    DO1_actual = sum(DO1_values) / len(DO1_values)
    DO2_actual = sum(DO2_values) / len(DO2_values)
    increase_percent, control_ = determine_adjustment_Dochange(DO1_LCL, DO1_LSL, DO1_UCL, DO1_USL, DO2_LCL,
                                                               DO2_LSL, DO2_UCL, DO2_USL, DO1_actual,
                                                               DO2_actual, OTE_optimization, control_, huan_xun_value, tolerance)
    fan1_online = not (fan1_percent == -1 and fan1_power == -1)
    fan2_online = not (fan2_percent == -1 and fan2_power == -1)
    fan3_online = not (fan3_percent == -1 and fan3_power == -1)
    logs = []

    online_fans = sum([fan1_online, fan2_online, fan3_online])
    print(online_fans)

    if online_fans >= 2:
        if fan3_online and fan2_online:
            new_fan3_percent, new_fan2_percent, fan3_op, fan2_op, number = adjust_wind_volume_two(
                fan3_min, fan2_min, fan3_max, fan2_max,
                fan3_percent, fan2_percent,
                fan3_power, fan2_power,
                increase_percent, int(number_value), control_)
            if fan3_op != -1:
                logs.append({"deviceId": fan3_id, "op": fan3_op, "fl": new_fan3_percent})
            if fan2_op != -1:
                logs.append({"deviceId": fan2_id, "op": fan2_op, "fl": new_fan2_percent})
        elif fan3_online and fan1_online:
            new_fan3_percent, new_fan1_percent, fan3_op, fan1_op, number = adjust_wind_volume_two(
                fan3_min, fan1_min, fan3_max, fan1_max,
                fan3_percent, fan1_percent,
                fan3_power, fan1_power,
                increase_percent, int(number_value), control_)
            if fan3_op != -1:
                logs.append({"deviceId": fan3_id, "op": fan3_op, "fl": new_fan3_percent})
            if fan1_op != -1:
                logs.append({"deviceId": fan1_id, "op": fan1_op, "fl": new_fan1_percent})
        elif fan2_online and fan1_online:
            new_fan2_percent, new_fan1_percent, fan2_op, fan1_op, number = adjust_wind_volume_two(
                fan2_min, fan1_min, fan2_max, fan1_max,
                fan2_percent, fan1_percent,
                fan2_power, fan1_power,
                increase_percent, int(number_value), control_)
            if fan2_op != -1:
                logs.append({"deviceId": fan2_id, "op": fan2_op, "fl": new_fan2_percent})
            if fan1_op != -1:
                logs.append({"deviceId": fan1_id, "op": fan1_op, "fl": new_fan1_percent})

    elif online_fans == 1:
        if fan3_online:
            new_fan3_percent, fan3_op, number = adjust_wind_volume_one(
                fan3_min, fan3_max, fan3_percent, fan3_power,
                increase_percent, int(number_value), control_)
            if fan3_op != -1:
                logs.append({"deviceId": fan3_id, "op": fan3_op, "fl": new_fan3_percent})
        elif fan2_online:
            new_fan2_percent, fan2_op, number = adjust_wind_volume_one(
                fan2_min, fan2_max, fan2_percent, fan2_power,
                increase_percent, int(number_value), control_)
            if fan2_op != -1:
                logs.append({"deviceId": fan2_id, "op": fan2_op, "fl": new_fan2_percent})
        elif fan1_online:
            new_fan1_percent, fan1_op, number = adjust_wind_volume_one(
                fan1_min, fan1_max, fan1_percent, fan1_power,
                increase_percent, int(number_value), control_)
            if fan1_op != -1:
                logs.append({"deviceId": fan1_id, "op": fan1_op, "fl": new_fan1_percent})
    data = {
        "logs": logs,
        "rtdData": {
            "DO中": f"{round(DO1_actual, 2):.2f}",
            "DO末": f"{round(DO2_actual, 2):.2f}",
            "环浔": str(control_),
            "number": str(number)
        }
    }
    print(data)
    return data

@app.route('/', methods=['GET', 'POST'])
def config_page():
    config = load_config()
    if request.method == 'POST':
        config['DO1_id'] = request.form.get('DO1_id', config['DO1_id'])
        config['DO2_id'] = request.form.get('DO2_id', config['DO2_id'])
        save_config(config)
        return render_template('config.html', DO1_id=config['DO1_id'], DO2_id=config['DO2_id'], algorithm_running=config['algorithm_running'], message="Configuration updated successfully!")
    return render_template('config.html', DO1_id=config['DO1_id'], DO2_id=config['DO2_id'], algorithm_running=config['algorithm_running'])

@app.route('/toggle_algorithm', methods=['POST'])
def toggle_algorithm():
    config = load_config()
    config['algorithm_running'] = not config['algorithm_running']
    save_config(config)
    return jsonify({"status": "success", "running": config['algorithm_running']})

if __name__ == '__main__':
    algorithm_thread = threading.Thread(target=run_algorithm)
    algorithm_thread.start()
    app.run(debug=True, port=5000, use_reloader=False, use_debugger=False)