# run app: flask --app main.py run

from flask import Flask

app = Flask(__name__)

@app.route('/') # specify directory/route
def hello_world():
    return '<p>Hello world!</p>' # return html code
