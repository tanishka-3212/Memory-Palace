
from flask import Flask, render_template, request, session, redirect, url_for, send_file
import requests
import os
import io
from gtts import gTTS

os.makedirs("static", exist_ok=True)

app = Flask(__name__)
app.secret_key = os.urandom(24)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = "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"

def chat_with_groq(message, history=None):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = history if history else []
    messages.append({"role": "user", "content": message})

    data = {
        "model": "gemma2-9b-it",
        "messages": messages,
        "temperature": 0.7
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=data)
        print("Status Code:", response.status_code)
        print("Response Body:", response.text)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print("HTTP Error:", e)
        return "Sorry, there was a problem contacting the chatbot.", messages
    except Exception as e:
        print("Unexpected Error:", e)
        return "Unexpected error occurred.", messages

    try:
        reply = response.json()["choices"][0]["message"]["content"]
        messages.append({"role": "assistant", "content": reply})
        tts = gTTS(reply)
        tts.save("static/reply.mp3")
        return reply, messages
    except Exception as e:
        print("Error parsing response:", e)
        return "Could not understand the chatbot response.", messages



@app.route("/", methods=["GET", "POST"])
def index():
    if "username" in session:
        return redirect(url_for("chat"))

    if request.method == "POST":
        session["username"] = request.form["username"]
        session["history"] = []
        return redirect(url_for("chat"))

    return render_template("login.html")

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "username" not in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        history = session.get("history", [])
        file = request.files.get("file")
        user_message = request.form.get("message", "").strip()

        # 📁 Handle file upload
        if file and file.filename:
            filename = file.filename
            file.save(os.path.join("uploads", filename))  # Ensure "uploads" folder exists

            # 🧠 Trigger bot response about file
            user_message = f"I uploaded a file named {filename}."

        if user_message:
            bot_reply, updated_history = chat_with_groq(user_message, history)
            session["history"] = updated_history

    return render_template("chat.html", messages=session.get("history", []), username=session["username"])


@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("index"))

@app.route("/download")
def download_chat():
    chat_log = session.get("history", [])
    content = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in chat_log])
    return send_file(
        io.BytesIO(content.encode()),
        mimetype="text/plain",
        as_attachment=True,
        download_name="chat_log.txt"
    )

if __name__ == "__main__":
    app.run(debug=True)