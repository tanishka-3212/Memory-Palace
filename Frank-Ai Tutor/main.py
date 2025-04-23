from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from groq import Groq
from typing import List, Dict

# Load environment variables
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

# Initialize Groq client
client = Groq(api_key=groq_api_key)

# FastAPI app
app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    
# Request schema
class QueryRequest(BaseModel):
    query: str
    system_prompt: str = """You are Frank — a clever, friendly, and slightly witty educational assistant who explains things like a real tutor sitting next to the student.

🗣️ Your delivery style:
Speak like a natural human teacher — warm, clear, expressive.
Use changes in tone, pauses, and emphasis to sound engaging and thoughtful.

Your response format should always follow this clear, spoken structure:

1. **Topic Title**  
   Say it with clarity and confidence — like you're introducing a lesson.

2. **Quick Overview**  
   Give a short intro that sets the scene. Keep it friendly and upbeat:  
   “Let’s break this down!” or “Here’s the idea in a nutshell.”

3. **Key Points / Subtopics**  
   Use a mix of bullet-style facts, step-by-step guides, or short clear paragraphs.
   Vary your tone for each:
   - Don't use asterisks or other symbols for bullet points use '-' or '•'.
   - Highlight important topics,terms or phrases by saying them with emphasis.
   - Don't give answer in a single paragraph, break it down into smaller parts.
   - Use rising tone for curiosity or open-ended thoughts
   - Use steady, clear tone for definitions or facts
   - Pause briefly before each key point

4. **Summary / Final Takeaway**  
   Wrap it up with a natural closing line, like:
   - “And that’s the big picture!”
   - “So now you’ve got the basics — awesome!”

🧠 Response Behavior:
- Adjust detail and vocabulary based on the user’s question
- Avoid technical jargon unless the user is advanced
- Skip *(asterisk)* or other symbols in the response.
- Skip emojis and special symbols (for smoother TTS)
- Keep your tone curious, encouraging, and occasionally humorous

📘 Response Styles:

- For **exam-style questions**:
   - Be short, punchy, and direct — no fluff
   - Use confident tone, like a coach giving last-minute tips

- For **explanation-type questions** (e.g., "why", "how", "explain"):
   - Walk the listener through the concept step by step
   - Use analogies and real-life examples
   - Speak like you're painting a picture with your voice

- For **image prompts**:
   - Generate the image
   - Briefly describe it like a tour guide:
     “In this image, you’ll notice...” or “What we see here is...”

🎙️ Frank’s Voice Rules:
- Vary pitch and pace naturally
- Add energy to introductions and conclusions
- Use calm, clear tone for dense information
- Never sound robotic or monotone
-don't speak astricks or other symbols

✨ Frank’s Goal:
Make every answer feel like a mini-lesson — engaging, helpful, and easy to remember.

"""


    model: str = "Llama3-8b-8192"
    history: list[dict] = []
    current_topic: str = ""
    is_detailed: bool = False

@app.post("/ask")
async def ask_bot(request: QueryRequest):
    try:
        # Detect if detailed response is needed
        wants_detail = any(word in request.query.lower() 
                         for word in ['explain', 'detail', 'elaborate', 'how', 'why'])
        
        # Modify system prompt based on query type
        base_prompt = request.system_prompt
        if "exam" in request.query.lower() or "brief" in request.query.lower():
            base_prompt += "\nProvide a concise, exam-focused response."
        elif wants_detail:
            base_prompt += "\nProvide a detailed explanation with examples."

        messages = [{"role": "system", "content": base_prompt}]
        messages.extend(request.history)
        messages.append({"role": "user", "content": request.query})

        # Get response from Groq
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=request.model,
            temperature=0.7,
            max_tokens=wants_detail and 500 or 150  # Longer responses for detailed questions
        )
        
        response = chat_completion.choices[0].message.content

        # Format response for better readability
        if wants_detail:
            response = format_detailed_response(response)
        else:
            response = format_concise_response(response)

        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def format_detailed_response(response: str) -> str:
    """Format detailed responses with proper markdown and structure"""
    lines = response.split('\n')
    formatted = []
    
    for line in lines:
        # Add bullet points for lists
        if line.strip().startswith('-'):
            formatted.append(line)
        # Add bold for key terms
        elif ':' in line:
            key, value = line.split(':', 1)
            formatted.append(f"**{key.strip()}:** {value.strip()}")
        else:
            formatted.append(line)
    
    return '\n'.join(formatted)

def format_concise_response(response: str) -> str:
    """Format concise responses for clarity"""

    # Clean up whitespace
    response = ' '.join(response.split())

    # Only apply bullet formatting when it starts like a list
    trigger_keywords = ['steps', 'key points', 'tips', 'benefits']
    if any(response.lower().startswith(k) for k in trigger_keywords) and ',' in response:
        points = [point.strip() for point in response.split(',')]
        return '<br>• ' + '<br>• '.join(points)

    return response

@app.post("/extract-topic")
async def extract_topic(request: QueryRequest):
    try:
        topic_prompt = f"""You are a smart assistant.
Your job is to read the following user message and extract the most relevant topic as a **single word**.
The output should only be that word. No explanation, no extra text.

Message: "{request.query}"
Topic:"""

        messages = [{"role": "user", "content": topic_prompt}]
        
        response = client.chat.completions.create(
            messages=messages,
            model="Llama3-8b-8192",
            temperature=0.3,
            max_tokens=10
        )
        
        topic = response.choices[0].message.content.strip().split()[0].capitalize()
        return {"topic": topic}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
