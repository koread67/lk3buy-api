# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return 'LK_3_BUY API is running!'

@app.route('/analyze', methods=['POST'])
def analyze():
    return jsonify({"message": "ETF ë¶ì ìë£", "ë§¤ìì í¸": True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)