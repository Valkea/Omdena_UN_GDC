#! /usr/bin/env python3
# coding: utf-8

import os
from flask import Flask, request, redirect, jsonify, url_for, session, abort
from flask_cors import CORS

# ########## INIT APP ##########

# --- API Flask app ---
app = Flask(__name__)
app.secret_key = "super secret key"
# app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 200

CORS(app)

# ########## API ENTRY POINTS (BACKEND) ##########

@app.route("/")
# @app.doc(hide=True)
def index():
    """Define the content of the main fontend page of the API server"""

    return f"""
    <h1>Hello World</h1>
    """

@app.route("/option", methods=['GET'])
def option():

    query = request.form.get("query")

    print("\n", f"query: \"{query}\"", "\n")

    return f"""
    <h1>Option 1</h1>
    """

def shutdown_computer():
    if os.name == 'nt':
        # For Windows operating system
        os.system('shutdown /s /t 0')
    elif os.name == 'posix':
        # For Unix/Linux/Mac operating systems
        os.system('sudo shutdown now')
    else:
        print('Unsupported operating system.')


@app.route("/shutdown")
def shutdown():

    shutdown_computer()

    return f"""
    <h1>Shut down the instance</h1>
    """

# ########## START FLASK SERVER ##########

if __name__ == "__main__":

    current_port = int(os.environ.get("PORT") or 5000)
    app.run(debug=False, host="0.0.0.0", port=current_port, threaded=True)
