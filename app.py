# -*- coding: utf-8 -*-
#
# KTMB Auto Ticket Bot - Web Management Panel
# Copyright (C) 2025 AnnChongS
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
from flask import Flask, render_template, request, jsonify
import json
import os
import subprocess
import sys

app = Flask(__name__)

CONFIG_FILE = "config.json"
LOG_FILE = "bot.log"
bot_process = None

if not os.path.exists(LOG_FILE):
    open(LOG_FILE, 'w', encoding='utf-8').close()

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    # 使用 utf-8-sig 吞掉看不见的 BOM 字符，绝不报错
    with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as f:
        try:
            return json.load(f)
        except:
            return {}

def save_config(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@app.route('/')
def index():
    config = load_config()
    return render_template('index.html', config=config)

@app.route('/api/save', methods=['POST'])
def api_save():
    data = request.json
    save_config(data)
    return jsonify({"status": "success", "message": "配置已保存！"})

@app.route('/api/start', methods=['POST'])
def api_start():
    global bot_process
    if bot_process and bot_process.poll() is None:
        return jsonify({"status": "error", "message": "机器人已经在运行中！"})
    
    # 【改动】去掉了火箭表情，纯文字写入，Windows 绝对不报错
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(">>> [系统] 正在启动抢票指挥官...\n")
    
    try:
        log_file = open(LOG_FILE, 'a', encoding='utf-8')
        
        # 强制设置子进程的环境变量为 utf-8，双重保险
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        bot_process = subprocess.Popen(
            [sys.executable, "-u", "ktmb_auto.py"], 
            stdout=log_file, 
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            env=env
        )
        return jsonify({"status": "success", "message": "机器人已启动！"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"启动失败: {str(e)}"})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    global bot_process
    if bot_process and bot_process.poll() is None:
        bot_process.terminate()
        bot_process = None
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write("\n>>> [系统] 机器人已被强制停止！\n")
        return jsonify({"status": "success", "message": "机器人已停止！"})
    return jsonify({"status": "error", "message": "机器人未运行"})

@app.route('/api/status', methods=['GET'])
def api_status():
    global bot_process
    is_running = bot_process is not None and bot_process.poll() is None
    return jsonify({"running": is_running})

@app.route('/api/logs', methods=['GET'])
def api_logs():
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return jsonify({"logs": "".join(lines[-100:])})
    except:
        return jsonify({"logs": "暂无日志..."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)