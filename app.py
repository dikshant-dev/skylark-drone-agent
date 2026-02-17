from flask import Flask, request, jsonify, render_template
from agent import DroneAgent
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
agent = DroneAgent()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    response = agent.handle_message(user_message)
    return jsonify(response)

@app.route('/dashboard', methods=['GET'])
def dashboard():
    summary = agent.get_dashboard_summary()
    return jsonify(summary)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
