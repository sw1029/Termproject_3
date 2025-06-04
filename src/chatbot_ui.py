from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)
API_URL = "http://localhost:8000"

HTML = """
<!doctype html>
<title>Chatbot</title>
<h1>Chatbot Demo</h1>
<form method=post>
  <input name=question size=60 autofocus>
  <input type=submit value=Ask>
</form>
<pre>{{answer}}</pre>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    answer = ''
    if request.method == 'POST':
        q = request.form['question']
        resp = requests.post(f"{API_URL}/answer", json={'question': q}, timeout=10)
        if resp.ok:
            answer = resp.json().get('answer', '')
        else:
            answer = 'Error'
    return render_template_string(HTML, answer=answer)

if __name__ == '__main__':
    app.run(debug=True)
