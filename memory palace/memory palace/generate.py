from flask import Flask, render_template, request, send_from_directory
from openai import OpenAI
import os
from dotenv import load_dotenv
import uuid
import requests

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/generated'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def download_image(url, filename):
    response = requests.get(url)
    with open(filename, 'wb') as f:
        f.write(response.content)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        prompt = request.form['prompt']
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            image_url = response.data[0].url
            unique_id = str(uuid.uuid4())
            filename = f"{unique_id}.png"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            download_image(image_url, filepath)
            
            return render_template('result.html', 
                                image_file=filename,
                                prompt=prompt)
        except Exception as e:
            return render_template('error.html', error=str(e))
    return render_template('index.html')

@app.route('/static/generated/<filename>')
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)