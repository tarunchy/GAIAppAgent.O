from flask import Flask, jsonify, render_template
import random
import json

app = Flask(__name__)


# Load mock data
with open('data.json') as f:
    data = json.load(f)["Data"]

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/realtime', methods=['GET'])
def realtime_data():
    selected_data = random.choice(data)
    return jsonify(selected_data)

@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify(status="ok")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8898, debug=True, use_reloader=True)
