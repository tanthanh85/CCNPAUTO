#!/usr/bin/env python3
"""Small stateless web service used to demonstrate Kubernetes fundamentals."""

import os
from flask import Flask, jsonify


app = Flask(__name__)


@app.get("/")
def index():
    return jsonify(
        {
            "application": "network-status",
            "message": os.getenv("APP_MESSAGE", "Network automation is ready"),
            "pod": os.getenv("POD_NAME", "local"),
            "namespace": os.getenv("POD_NAMESPACE", "local"),
        }
    )


@app.get("/health")
def health():
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
