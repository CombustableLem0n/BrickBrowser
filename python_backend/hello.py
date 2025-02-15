from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def hello_world():
    return "Hello, World!"

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)

#  Run in terminal: python -m flask --app hello run
#  Must be ran while python_backend is in filepath
#  Example path: C:\Users\Developer\Project\python_backend