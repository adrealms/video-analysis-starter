#!/usr/bin/env python3
"""Run Flash and Pro on the same set of videos in parallel for comparison."""
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_video import analyze

ROOT = Path(__file__).resolve().parent.parent
VIDEOS = ROOT / "videos"
OUT = ROOT / "analysis"

MODELS = ["gemini-2.5-flash", "gemini-2.5-pro"]


def run_job(video: Path, model: str):
    out_path = OUT / f"{video.stem}__{model.replace('gemini-', '')}.md"
    try:
        analyze(video, model, out_path)
        return (video.name, model, "ok", None)
    except Exception as e:
        return (video.name, model, "error", str(e))


def main():
    videos = sorted(VIDEOS.glob("*.mp4"))
    if not videos:
        print("No videos in videos/ folder.")
        return
    print(f"Found {len(videos)} videos × {len(MODELS)} models = {len(videos)*len(MODELS)} jobs\n")

    jobs = [(v, m) for v in videos for m in MODELS]

    # Parallelize: 4 concurrent (2 videos × 2 models)
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = [ex.submit(run_job, v, m) for v, m in jobs]
        results = [f.result() for f in as_completed(futures)]

    print("\n=== SUMMARY ===")
    for name, model, status, err in results:
        if status == "ok":
            print(f"  ✓ {name} × {model}")
        else:
            print(f"  ✗ {name} × {model}: {err}")


if __name__ == "__main__":
    main()
