from flask import Flask, render_template, request
from openai import OpenAI
import os

app = Flask(__name__)

# Your OpenAI API key
client = OpenAI(api_key="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")

@app.route("/", methods=["GET", "POST"])
def index():
    image_url = None
    error = None

    if request.method == "POST":
        prompt = request.form.get("prompt")
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url
        except Exception as e:
            error = f"Error: {str(e)}"

    return render_template("index.html", image_url=image_url, error=error)

if __name__ == "__main__":
    app.run(debug=True)
