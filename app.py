from flask import Flask, render_template, jsonify
import os
import pandas as pd

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

REPLAY_PATH = os.path.join(
    BASE_DIR,
    "outputs",
    "raptor_replay.csv"
)


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/status")
def status():
    return jsonify({
        "system": "RAPTOR",
        "status": "online",
        "mode": "replay",
        "model": "LSTM"
    })


@app.route("/api/replay")
def replay():

    if not os.path.exists(REPLAY_PATH):
        return jsonify({
            "error": "Replay results not found"
        }), 404

    df = pd.read_csv(REPLAY_PATH)

    df["time_window"] = df["time_window"].astype(str)

    return jsonify({
        "count": len(df),
        "predictions": df.to_dict(orient="records")
    })


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )