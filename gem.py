import os
import base64
import json
import httpx
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# Configure the Gemini API
GOOGLE_AI_API_KEY = ""
genai.configure(api_key=GOOGLE_AI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

def generate_text(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error in generate_text: {e}")
        return "Sorry, I encountered an error while generating the response."

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    print("hello in api")
    user_message = request.form.get("user_message")
    uploaded_file = request.files.get("file")
    messages = request.form.getlist("messages")

    try:
        messages = [json.loads(msg) for msg in messages]
    except (json.JSONDecodeError, TypeError):
        return jsonify({"error": "Invalid or missing message format in previous messages"}), 400

    if not user_message and not uploaded_file:
        return jsonify({"error": "No message or file provided"}), 400

    if uploaded_file:
        try:
            image_data = base64.b64encode(uploaded_file.read()).decode('utf-8')
            image_mime = uploaded_file.mimetype
            caption_prompt = "Caption this image."
            image_response = model.generate_content([
                {'mime_type': image_mime, 'data': image_data}, caption_prompt
            ])
            caption = image_response.text
            user_message = f"Image Caption: {caption}. {user_message}" if user_message else caption
        except Exception as e:
            print(f"Error processing image: {e}")
            return jsonify({"error": "Error processing image"}), 500

    messages.append({"sender": "user", "text": user_message})
    prompt = "\n".join([msg["text"] for msg in messages])

    try:
        reply = generate_text(prompt)
        messages.append({"sender": "gemini", "text": reply})
        return jsonify({"reply": reply, "messages": messages})
    except Exception as e:
        print(f"Error generating response: {e}")
        return jsonify({"error": "An error occurred while generating response"}), 500

if __name__ == "__main__":
    app.run(debug=True)
