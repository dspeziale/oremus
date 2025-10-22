from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS


app = Flask(__name__)
app.config['SECRET_KEY'] = 'oremus'
app.config['JSON_AS_ASCII'] = False
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=59000)