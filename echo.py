import os
from flask import Flask, request
app = Flask(__name__)
 
@app.route("/")
def hello():
    return '<form action="/echo" method="GET"><input name="text"><input type="submit" value="Echo"></form>'
 
@app.route("/echo")
def echo(): 
    return "You said: " + request.args.get('text', '')
 
 
app.run(host="0.0.0.0", port=os.environ.get('PORT', 5000))