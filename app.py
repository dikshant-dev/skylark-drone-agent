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
    app.run(debug=True, port=5000)
