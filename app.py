import os
import requests
from flask import Flask, request as flask_request, render_template_string, redirect, url_for

app = Flask(__name__)
app.secret_key = 'super_secret_miniai_key'

history = []

TEMPLATE = """<!DOCTYPE html>
<html>
<head><title>MiniAI</title></head>
<body>
<h3>MiniAI</h3>
<form action="/chat" method="post">
<input type="text" name="q" size="20">
<input type="submit" value="Ask">
</form>
<br>
{% for msg in history %}
  {% if msg.role == 'user' %}
    <b>> {{ msg.content }}</b><br>
  {% elif msg.role == 'assistant' %}
    <i>{{ msg.content }}</i><br><hr>
  {% endif %}
{% endfor %}
{% if history %}<a href="/clear">Clear</a>{% endif %}
</body>
</html>"""

API_KEY = os.environ.get("GROQ_API_KEY", "")

@app.route("/")
def index():
    return render_template_string(TEMPLATE, history=reversed(history))

@app.route("/chat", methods=["POST"])
def chat():
    global history
    q = flask_request.form.get("q")
    if not q or not q.strip():
        return redirect(url_for("index"))
    
    system_prompt = (
        "You are MiniAI for an old Nokia phone. "
        "Reply in under 60 words. Extremely concise. No markdown."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    
    for h in history[-4:]:
        messages.append({"role": h["role"], "content": h["content"]})
        
    messages.append({"role": "user", "content": q})
    
    reply = ""
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.1-8b-instant",
            "messages": messages,
            "max_tokens": 100
        }
        resp = requests.post(url, headers=headers, json=data)
        resp_json = resp.json()
        if "choices" in resp_json:
            reply = resp_json["choices"][0]["message"]["content"]
        else:
            reply = f"API Error: {resp.text}"
    except Exception as e:
        reply = f"Error: {str(e)}"

    history.append({"role": "user", "content": q})
    history.append({"role": "assistant", "content": reply})
    
    return redirect(url_for("index"))

@app.route("/clear")
def clear():
    global history
    history = []
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
