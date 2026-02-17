# this one is a meme i did not make it.


from flask import Flask, request, render_template, jsonify
from pathlib import Path
import random
import json
import re
import pyttsx3


# --- Persona config ---
PERSONA = {
    "name": "Maya",
    "age_approx": "mid-20s",
    "traits": ["playful", "supportive", "curious"],
    "likes": ["coffee", "hiking", "sci-fi movies"],
    "dislikes": ["rudeness", "spam"],
    "greeting": "Hey — I'm Maya. How was your day?",
    "example_phrases": {
        "flirt": ["You're making me blush 😊", "Is that a challenge? I like a good challenge 😉"],
        "support": ["That sounds tough. Tell me more if you want to vent.", "I got you. What helps you relax?"],
        "smalltalk": ["I had the best latte today. What did you eat?", "If you could teleport, where would you go?"]
    }
}

# --- Simple memory ---
CONVERSATIONS_DIR = Path("convos")
CONVERSATIONS_DIR.mkdir(exist_ok=True)

def save_message(session_id, speaker, text):
    f = CONVERSATIONS_DIR / f"{session_id}.txt"
    with f.open("a", encoding="utf8") as fh:
        fh.write(f"{speaker}: {text}\n")

def load_history(session_id, n=20):
    f = CONVERSATIONS_DIR / f"{session_id}.txt"
    if not f.exists():
        return []
    lines = f.read_text(encoding="utf8").strip().splitlines()
    return lines[-n:]

# --- Response engine (heuristic + templates) ---
def detect_intent(text):
    t = text.lower()
    if any(w in t for w in ["love", "miss you", "i like you", "crush"]):
        return "flirt"
    if any(w in t for w in ["sad", "upset", "depressed", "angry", "tired"]):
        return "support"
    if any(w in t for w in ["hi", "hello", "hey", "yo"]):
        return "greet"
    if any(w in t for w in ["movie", "watch", "netflix", "film"]):
        return "movies"
    if re.search(r"\bhow\b.*\b(day|are you)\b", t):
        return "smalltalk"
    return "default"

def build_reply(user_text, history):
    intent = detect_intent(user_text)
    p = PERSONA
    if intent == "greet":
        return random.choice([
            f"{p['greeting']}",
            f"Hi — {p['name']} here. What's new with you?"
        ])
    if intent == "flirt":
        return random.choice(p["example_phrases"]["flirt"])
    if intent == "support":
        return random.choice(p["example_phrases"]["support"])
    if intent == "movies":
        likes = ", ".join(p["likes"])
        return f"I love movies. I like sci-fi and cozy comedies. My favorites are Dune and The Princess Bride. You into something specific?"
    if intent == "smalltalk":
        return random.choice(p["example_phrases"]["smalltalk"])
    # default: echo + personality twist
    short = user_text.strip()
    if len(short) == 0:
        return "Say something. I'm listening."
    # mirror + add emoji and a follow-up question
    followups = [
        "Tell me more.",
        "Why do you say that?",
        "How does that make you feel?",
        "That sounds interesting. Go on."
    ]
    emoji = random.choice(["🙂","😊","😉","🤔"])
    return f"{emoji} I hear you: \"{short}\". {random.choice(followups)}"

# Optional TTS
tts_engine = None
def speak_text(text):
    global tts_engine
    if tts_engine is None:
        try:
            tts_engine = pyttsx3.init()
        except Exception:
            tts_engine = None
            return False
    try:
        tts_engine.say(text)
        tts_engine.runAndWait()
        return True
    except Exception:
        return False

# --- Routes ---
def index():
    return render_template("chatbot.html", persona=PERSONA)

def chat():
    data = request.json
    session_id = data.get("session_id", "default")
    message = data.get("message", "")
    save_message(session_id, "user", message)
    history = load_history(session_id)
    reply = build_reply(message, history)
    save_message(session_id, PERSONA["name"], reply)
    tts = False
    if data.get("tts", False):
        tts = speak_text(reply)
    return jsonify({
        "reply": reply,
        "persona": PERSONA["name"],
        "tts_played": tts
    })

def register_chatbot_routes(app):
	app.add_url_rule('/chatbot', "chatbot_page", index, methods=['GET','POST'])
	app.add_url_rule('/chatbot/chat', "chatbot_chat", chat, methods=['GET','POST'])

