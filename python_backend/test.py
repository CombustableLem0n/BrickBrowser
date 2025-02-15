from flask import Flask
from flask import request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def hello_world():
    return "you called 'Hello, World!' dummy!"


@app.route("/image", methods = ['GET', 'POST'])
def image():
    if request.method == "GET":
        return "GET"

    if request.method == "POST":
        return "POST"

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)

#  Run in terminal: python -m flask --app test run
#  Must be ran while python_backend is in filepath
#  Example path: C:\Users\Developer\Project\python_backend