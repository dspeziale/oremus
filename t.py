from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import calendar

app = Flask(__name__)
app.config['SECRET_KEY'] = 'liturgia-dashboard-atlantis-2.0'
app.config['JSON_AS_ASCII'] = False
CORS(app)

@app.route('/')
def index():
    """Gestione errore 404"""
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=59000)