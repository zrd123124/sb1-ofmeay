from flask import Flask, render_template, request, jsonify
import json

app = Flask(__name__)

CONFIG_FILE = 'config.json'

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

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

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
    app.run(debug=True, port=5001, use_reloader=False, use_debugger=False)