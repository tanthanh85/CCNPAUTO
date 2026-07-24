from __future__ import annotations

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template

from src.restconf_monitor import RestconfMonitorError, get_monitoring_snapshot


load_dotenv()

app = Flask(__name__, template_folder="templates_flask")


@app.get("/")
def index():
    return render_template("portal.html")


@app.get("/api/metrics")
def metrics():
    try:
        return jsonify({"ok": True, "data": get_monitoring_snapshot()})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 502


if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", "5060")),
    )

