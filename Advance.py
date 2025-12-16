import os
import datetime
import subprocess
import webbrowser
import pyttsx3
import speech_recognition as sr
import sounddevice as sd

from dotenv import load_dotenv
from typing import List, Literal
from pydantic import BaseModel, Field
from openai import OpenAI

# ---------------- ENV ----------------
load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

MODEL = "llama-3.1-8b-instant"

# ---------------- SCHEMAS ----------------
class Action(BaseModel):
    name: Literal["Open App", "Close App", "Open Website"]
    app_name: str = ""
    website_link: str = ""
    contact: str = ""
    message: str = ""

class Recipe(BaseModel):
    subAction: List[Action]
    replyMessage: str

# ---------------- VOICE ----------------
def speak(text: str):
    engine = pyttsx3.init()
    engine.setProperty("rate", 175)
    engine.say(text)
    engine.runAndWait()

def greeting():
    hour = datetime.datetime.now().hour
    if hour < 12:
        speak("Good morning")
    elif hour < 18:
        speak("Good afternoon")
    else:
        speak("Good evening")

    speak("I am Taarzan. How can I help you?")

def take_command() -> str:
    r = sr.Recognizer()
    fs = 44100
    duration = 4

    print("🎙 Listening...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype="int16")
    sd.wait()

    try:
        audio_data = sr.AudioData(audio.tobytes(), fs, 2)
        query = r.recognize_google(audio_data, language="en-IN")
        print("🗣 User:", query)
        return query
    except Exception:
        return ""

# ---------------- PROMPTS ----------------
PROMPT_INTENT = """
Classify the user's intent.

Return EXACTLY one word:
automation OR normal

automation = app, website, or system action
normal = greeting or general question
"""

PROMPT_AUTOMATION = """
You must return a JSON object that EXACTLY follows this schema.

IMPORTANT:
- The value of "name" MUST be ONE of these strings:
  "Open App"
  "Close App"
  "Open Website"

- NEVER combine them
- NEVER include | symbol
- Choose ONLY ONE based on user intent

Schema example (this is ONLY an example):

{
  "subAction": [
    {
      "name": "Open App",
      "app_name": "WhatsApp",
      "website_link": "",
      "contact": "",
      "message": ""
    }
  ],
  "replyMessage": "Opening WhatsApp."
}

Rules:
- All fields must always exist
- website_link must include https:// if used
- Output ONLY valid JSON
"""


PROMPT_CHAT = """
You are Taarzan, a polite and helpful desktop assistant.
Reply briefly and naturally.
"""

# ---------------- LLM CALLS ----------------
def classify_intent(text: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": PROMPT_INTENT},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content.strip()

def get_automation(text: str) -> Recipe:
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": PROMPT_AUTOMATION},
            {"role": "user", "content": text}
        ]
    )
    return Recipe.model_validate_json(
        response.choices[0].message.content
    )

def chat_normal(text: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": PROMPT_CHAT},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content

# ---------------- ACTION EXECUTION ----------------
def execute_action(recipe: Recipe):
    action = recipe.subAction[0]

    if action.name == "Open App":
        subprocess.run(["open", "-a", action.app_name])
        speak(recipe.replyMessage)

    elif action.name == "Close App":
        subprocess.run(["pkill", "-x", action.app_name])
        speak(recipe.replyMessage)

    elif action.name == "Open Website":
        webbrowser.open(action.website_link)
        speak(recipe.replyMessage)

# ---------------- MAIN LOOP ----------------
if __name__ == "__main__":
    greeting()

    while True:
        query = take_command()
        if not query:
            continue

        intent = classify_intent(query)
        print("🧠 Intent:", intent)

        if intent == "automation":
            recipe = get_automation(query)
            print("⚙ Action:", recipe)
            execute_action(recipe)
        else:
            reply = chat_normal(query)
            print("💬 Reply:", reply)
            speak(reply)
