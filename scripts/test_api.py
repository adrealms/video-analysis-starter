#!/usr/bin/env python3
"""Quick sanity check: API key works, list available models."""
from pathlib import Path
from google import genai

ENV = Path(__file__).resolve().parent.parent / ".env"
api_key = None
for line in open(ENV):
    line = line.strip()
    if line.startswith("GEMINI_API_KEY="):
        api_key = line.split("=", 1)[1].strip()
        break
if not api_key or api_key == "PASTE_YOUR_KEY_HERE":
    raise SystemExit("No API key in .env")

client = genai.Client(api_key=api_key)

print("Connecting to Gemini API...")
models = list(client.models.list())
print(f"  ✓ {len(models)} models available\n")

video_capable = []
for m in models:
    name = m.name.replace("models/", "")
    if any(k in name.lower() for k in ["gemini-2", "gemini-1.5"]):
        actions = m.supported_actions or []
        if "generateContent" in actions:
            video_capable.append(name)

print("Models suitable for video analysis (Gemini 2.x / 1.5):")
for n in sorted(video_capable):
    print(f"  - {n}")
