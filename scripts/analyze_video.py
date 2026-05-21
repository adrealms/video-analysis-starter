#!/usr/bin/env python3
"""Analyze a video creative with Gemini.

Usage:
  python3 analyze_video.py <video_path> <model> <output_path>

Models: gemini-2.5-flash, gemini-2.5-pro
"""
import sys
import time
from pathlib import Path
from google import genai

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".env"


PROMPT = """You are a video analyst producing raw transcription data for a downstream strategic analysis. A separate model will interpret your output, so your only job is to extract factual data with maximum precision. Do NOT interpret, rate, or recommend. Do NOT add hook strength scores, audience guesses, or strategic notes.

Output a markdown document with exactly THREE independent timeline tracks.

## Track 1: VISUAL

List discrete visual scenes. A scene = one coherent visual unit (one camera setup OR one continuous action). NOT individual frames, NOT arbitrary time slices.

Format each entry as:
- **[start_time → end_time]** Description: subject + action + environment + camera movement + relevant visual details (props, colors, framing).

Example:
- **[0.0s → 2.0s]** Man in white t-shirt at outdoor cafe table, smiling at camera, holding black laptop case with both hands. Static eye-level medium shot, blurred greenery in background.
- **[2.0s → 3.5s]** Hard cut to airport floor: woman accidentally spills coffee from cup near a blue backpack on the ground. Handheld, low-angle.
- **[15.0s → 22.0s]** Static talking-head: same man at desk, gesturing while speaking. No camera movement.

Rules:
- A scene typically lasts 1-8 seconds, but can be longer if static. If a talking-head shot continues for 15 seconds without cuts, that's ONE scene, not multiple.
- A new scene begins when: camera cuts, subject changes, environment changes, or major action shift occurs.
- Be specific: "man pours water onto case" not "demo of feature".
- Don't list every micro-movement; group by semantic action.

## Track 2: ON-SCREEN TEXT

List every appearance of overlay text (animated captions, hook copy, kinetic typography, lower-thirds, end-card text, price stamps, brand IDs, button labels).

Format:
- **[start_time → end_time]** "EXACT TEXT AS DISPLAYED"

Example:
- **[0.0s → 0.4s]** "THINK"
- **[0.4s → 1.0s]** "LAPTOP"
- **[1.0s → 1.5s]** "AT AIRPORT"
- **[36.0s → end]** "ATLAS CASE / 360° Shockproof protection / SHOP NOW"

Rules:
- Include EVERY text element, even if it lasts under 0.5 seconds.
- Preserve original casing, spelling, and punctuation.
- If multiple texts share screen simultaneously and are part of the same animated unit, combine with " / ". If they're independent elements, list separately.
- If the video has no on-screen text at all, write only: `_No on-screen text in this video._`

## Track 3: AUDIO

Three subsections.

### Voiceover / Spoken

Verbatim transcription of every spoken phrase, with start-end timestamps per utterance.

- **[0.5s → 2.8s]** "I didn't think I needed a proper laptop sleeve until my bag got soaked at the airport."
- **[3.5s → 5.0s]** "Until I tested this one."

If no spoken audio: `_No voiceover._`

### Music

Describe the music track: genre, mood, tempo, instrumentation. Note where it starts, changes, drops, or stops.

- **[0.0s → end]** Upbeat acoustic pop, mid-tempo, light percussion, no major dynamic changes.

If no music: `_No music._`

### SFX

Sound effects with timestamps.

- **[1.5s]** Water splash
- **[3.5s]** Water pour sound
- **[8.0s]** Zipper sound

If no SFX: `_No notable SFX._`

---

CRITICAL RULES:
- Do NOT add a "strategic analysis", "hook rating", "target audience", "creative meta", or "recommendations" section. A separate model handles all of that.
- Do NOT use marketing adjectives like "engaging", "effective", "compelling", "captivating", "strong hook". Just describe what's there.
- Be CONCISE. Each scene/text/audio entry should be one line or short paragraph.
- Use exact timestamps to within ~0.2 seconds where possible. Approximate ranges for music are fine.
"""


def load_key():
    for line in open(ENV):
        line = line.strip()
        if line.startswith("GEMINI_API_KEY="):
            k = line.split("=", 1)[1].strip()
            if k and k != "PASTE_YOUR_KEY_HERE":
                return k
    raise SystemExit("No valid GEMINI_API_KEY in .env")


def wait_for_active(client, file, timeout=180):
    """Wait for uploaded file to become ACTIVE state."""
    start = time.time()
    while True:
        state = file.state.name if hasattr(file.state, "name") else str(file.state)
        if state == "ACTIVE":
            return file
        if state == "FAILED":
            raise RuntimeError(f"File processing failed: {file.name}")
        if time.time() - start > timeout:
            raise TimeoutError(f"File didn't become ACTIVE within {timeout}s")
        time.sleep(2)
        file = client.files.get(name=file.name)


def analyze(video_path: Path, model: str, out_path: Path):
    client = genai.Client(api_key=load_key())

    print(f"[{model}] uploading {video_path.name} ({video_path.stat().st_size / 1e6:.1f} MB)...")
    t0 = time.time()
    file = client.files.upload(file=str(video_path))
    upload_dur = time.time() - t0
    print(f"[{model}]   uploaded in {upload_dur:.1f}s, waiting for processing...")

    t1 = time.time()
    file = wait_for_active(client, file)
    process_dur = time.time() - t1
    print(f"[{model}]   active in {process_dur:.1f}s")

    print(f"[{model}] running analysis...")
    t2 = time.time()
    response = client.models.generate_content(
        model=model,
        contents=[file, PROMPT],
    )
    analyze_dur = time.time() - t2

    out_path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        f"# {video_path.stem} — analyzed with {model}\n\n"
        f"_Upload: {upload_dur:.1f}s · Processing: {process_dur:.1f}s · Analysis: {analyze_dur:.1f}s_\n\n"
        f"---\n\n"
    )
    out_path.write_text(header + response.text, encoding="utf-8")
    print(f"[{model}]   ✓ wrote {out_path.name} ({analyze_dur:.1f}s analysis)")

    # Cleanup uploaded file from Gemini (optional, files auto-expire in 48h)
    try:
        client.files.delete(name=file.name)
    except Exception:
        pass

    return out_path


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    analyze(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]))
