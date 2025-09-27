import subprocess
import os
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Global variable to store the Jarvis process
jarvis_process = None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start_jarvis():
    global jarvis_process
    try:
        if jarvis_process is None or jarvis_process.poll() is not None:
            run_path = os.path.join(os.getcwd(), "run.py")

            # Start Jarvis in background (cross-platform)
            jarvis_process = subprocess.Popen(
                ["python", run_path],
                cwd=os.path.dirname(run_path)
            )
            return jsonify({"status": "success", "message": "Jarvis started!"})
        else:
            return jsonify({"status": "info", "message": "Jarvis is already running!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/stop", methods=["POST"])
def stop_jarvis():
    global jarvis_process
    try:
        if jarvis_process is not None and jarvis_process.poll() is None:
            jarvis_process.terminate()
            jarvis_process = None
            return jsonify({"status": "success", "message": "Jarvis stopped!"})
        else:
            return jsonify({"status": "info", "message": "Jarvis is not running."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
