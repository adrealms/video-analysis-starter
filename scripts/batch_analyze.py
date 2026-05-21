#!/usr/bin/env python3
"""Batch-analyze videos in a folder with Gemini.

Output .md files are written next to each video, with the same basename.
Already-analyzed videos are skipped (unless --force).

Usage:
  python3 batch_analyze.py <folder> [--model MODEL] [--concurrency N] [--force]

Examples:
  python3 batch_analyze.py videos/titantrek
  python3 batch_analyze.py videos/competitors --concurrency 8 --model gemini-2.5-pro
"""
import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_video import analyze

VIDEO_EXTS = {".mp4", ".mov", ".webm", ".m4v", ".mkv"}
ROOT = Path(__file__).resolve().parent.parent

# Retry config for 429 errors
MAX_RETRIES = 5
INITIAL_BACKOFF = 5  # seconds


def safe_analyze(video: Path, model: str, out: Path):
    """Run analyze() with retry on 429 (rate limit) errors."""
    backoff = INITIAL_BACKOFF
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            analyze(video, model, out)
            return ("ok", None)
        except Exception as e:
            msg = str(e)
            last_err = msg
            transient = ("429" in msg or "RESOURCE_EXHAUSTED" in msg
                         or "503" in msg or "UNAVAILABLE" in msg
                         or "500" in msg or "INTERNAL" in msg)
            if transient:
                if attempt < MAX_RETRIES - 1:
                    label = "rate-limited" if "429" in msg else "server unavailable"
                    print(f"  ⏳ {video.name}: {label}, retry in {backoff}s "
                          f"(attempt {attempt+2}/{MAX_RETRIES})")
                    time.sleep(backoff)
                    backoff *= 2
                    continue
            return ("error", msg[:200])
    return ("error", f"max retries exceeded: {last_err[:200] if last_err else 'unknown'}")


def resolve_folder(folder_arg: str) -> Path:
    """Accept absolute path, or relative to project root or to videos/."""
    p = Path(folder_arg)
    if p.is_absolute() and p.exists():
        return p
    for base in [ROOT, ROOT / "videos", Path.cwd()]:
        candidate = base / folder_arg
        if candidate.exists():
            return candidate
    raise SystemExit(f"Folder not found: {folder_arg}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folder", help="Folder containing videos to analyze")
    parser.add_argument("--model", default="gemini-2.5-flash",
                        help="Gemini model (default: gemini-2.5-flash)")
    parser.add_argument("--concurrency", type=int, default=5,
                        help="Parallel jobs (default: 5, safe for free tier)")
    parser.add_argument("--force", action="store_true",
                        help="Re-analyze videos even if .md already exists")
    args = parser.parse_args()

    folder = resolve_folder(args.folder)
    print(f"\n📁 Folder: {folder}")
    print(f"🤖 Model: {args.model}")
    print(f"⚡ Concurrency: {args.concurrency}\n")

    # Scan for videos
    videos = sorted([p for p in folder.iterdir()
                     if p.is_file() and p.suffix.lower() in VIDEO_EXTS])
    if not videos:
        print(f"No videos found in {folder} (looking for {VIDEO_EXTS}).")
        return

    # Determine what to process vs skip
    # Gemini raw output goes to .gemini.md; the .md slot is reserved for Stage 2 (Claude) output.
    to_process = []
    skipped = []
    for v in videos:
        out = v.with_name(v.stem + ".gemini.md")
        if out.exists() and not args.force:
            skipped.append(v.name)
        else:
            to_process.append((v, out))

    print(f"Found {len(videos)} video(s): {len(to_process)} to analyze, {len(skipped)} already done")
    if skipped:
        for s in skipped[:5]:
            print(f"  ⏭  skip {s}")
        if len(skipped) > 5:
            print(f"  ... and {len(skipped) - 5} more")
    if not to_process:
        print("\nNothing to do. Use --force to re-analyze.\n")
        return
    print()

    # Process in parallel
    t_start = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futures = {
            ex.submit(safe_analyze, v, args.model, out): v.name
            for v, out in to_process
        }
        for fut in as_completed(futures):
            name = futures[fut]
            status, err = fut.result()
            results.append((name, status, err))

    elapsed = time.time() - t_start

    # Summary
    ok = sum(1 for _, s, _ in results if s == "ok")
    errors = [(n, e) for n, s, e in results if s != "ok"]
    print(f"\n=== DONE in {elapsed/60:.1f} min ({elapsed:.0f}s) ===")
    print(f"  ✓ Analyzed: {ok}/{len(to_process)}")
    if errors:
        print(f"  ✗ Errors: {len(errors)}")
        for name, err in errors:
            print(f"    - {name}: {err}")
    print(f"\n📁 Output: {folder}\n")


if __name__ == "__main__":
    main()
