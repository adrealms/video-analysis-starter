# Video Analysis Starter

A complete setup for analyzing ad video creatives with Claude Code + Google Gemini.

Drop a folder of `.mp4`/`.mov` files into the project, tell Claude to analyze them, and get back an interactive HTML dashboard with structured creative breakdowns — concept type, hook/body/CTA tables, click-to-seek video player, cross-video pattern stats.

**Time to first dashboard from a clean machine:** ~30 minutes for setup, then ~5 minutes per batch of 10-20 videos.

---

## What you'll need before starting

1. **A computer.** Windows, macOS, or Linux all work. Instructions below cover each.
2. **Claude Code installed.** Download from <https://www.anthropic.com/claude-code> (free during setup; usage requires Claude subscription).
3. **A Google account.** For the free Gemini API key.
4. **About 30 minutes of setup time, one time.** After that, daily use is "drop videos → ask Claude → open dashboard".
5. **Optional but recommended:** a terminal-curious friend or willingness to read scary-looking commands. Most of it Claude Code does for you, but you'll need to copy-paste a few commands.

You do NOT need to know Python, JavaScript, or any programming. The scripts are pre-built. You're following a recipe.

---

## Step 0 — Get the starter kit

You need to obtain the project files (this README, the scripts, the CLAUDE.md, etc.) before you can do anything else. Pick whichever path matches how you received them.

### Option A — From GitHub as ZIP (recommended, no terminal needed)

1. Open <https://github.com/adrealms/video-analysis-starter> in your browser.
2. Click the green **"Code"** button (top right of the file list).
3. Click **"Download ZIP"** at the bottom of the dropdown.
4. The ZIP downloads to your `Downloads` folder.
5. Find the ZIP, **right-click → Extract All** (Windows) or double-click (macOS/Linux).
6. **Remember the path** where you extracted it (typically `Downloads/video-analysis-starter-main/`). You'll need this in Step 2.

### Option B — Clone with git (if you already use git)

If you're comfortable with a terminal:

```bash
git clone https://github.com/adrealms/video-analysis-starter.git
```

The folder appears wherever you ran the command. Remember the path for Step 2.

### Option C — Received as a ZIP / folder from someone

If a colleague shared the kit directly:

1. Save the ZIP / folder somewhere easy to find (e.g. Desktop).
2. If it's a ZIP — extract it (right-click → Extract All on Windows, double-click on macOS/Linux).
3. Remember the path for Step 2.

> ✅ **Checkpoint:** You have a folder somewhere on your computer that contains `README.md`, `CLAUDE.md`, `.env.example`, `.gitignore`, a `scripts/` folder with 5 Python files, and an empty `videos/` folder.

---

## Step 1 — Pick a folder for the project on your computer

This folder will hold the scripts, configuration, and your video projects. Pick a location you can easily find again.

**On Windows:**
- Recommended: `C:\Users\<your-name>\video-analysis\`
- Or any folder under `Documents`, `Desktop`, etc.

**On macOS:**
- Recommended: `~/video-analysis/` (which is `/Users/<your-name>/video-analysis/`)

**On Linux:**
- Recommended: `~/video-analysis/`

**How to actually create the folder:**
- **Windows:** Open File Explorer, navigate to `C:\Users\<your-name>\`, right-click in empty space → New → Folder → name it `video-analysis`.
- **macOS:** Open Finder, press `Cmd+Shift+H` (your home folder), File menu → New Folder → name it `video-analysis`.
- **Linux:** In your file manager, navigate to your home directory, create a new folder named `video-analysis`. Or in terminal: `mkdir ~/video-analysis`.

> ✅ **Checkpoint:** An empty folder named `video-analysis` exists at the location of your choice. You know exactly where it is so you can navigate to it later.

---

## Step 2 — Copy the starter files into your folder

Copy ALL of the following from this starter kit into your new `video-analysis/` folder:

- `README.md` — this file
- `CLAUDE.md` — instructions for Claude Code (don't edit this without reason)
- `.env.example` — template for your Gemini API key
- `.gitignore` — git exclusions (only relevant if you use git)
- `scripts/` (entire folder, contains 5 Python scripts)
- `videos/` (entire folder, currently empty except for `.gitkeep`)

After copying, your folder should look like this:

```
video-analysis/
├── README.md
├── CLAUDE.md
├── .env.example
├── .gitignore
├── scripts/
│   ├── analyze_video.py
│   ├── batch_analyze.py
│   ├── compare_models.py
│   ├── render_project.py
│   └── test_api.py
└── videos/
    └── .gitkeep
```

> **Tip for Windows users:** if `.env.example` and `.gitignore` are hidden, enable "Show hidden files" in File Explorer → View tab → check "Hidden items".

> ✅ **Checkpoint:** Your `video-analysis/` folder now contains all 4 root files (`README.md`, `CLAUDE.md`, `.env.example`, `.gitignore`), the `scripts/` folder with 5 `.py` files, and the empty `videos/` folder. The original starter kit you downloaded in Step 0 can be deleted if you want.

---

## Step 3 — Open the folder in Claude Code

Claude Code is the AI assistant that will run the pipeline for you. It needs to be "connected" to your project folder.

1. **Launch Claude Code** from your Start Menu (Windows) / Applications (macOS) / app launcher (Linux).
2. When Claude Code opens, you'll see a prompt to **choose a working directory**. Click **"Open folder"** or use the equivalent menu option.
3. Navigate to your `video-analysis/` folder (the one you created in Step 1).
4. Click **"Open"** / **"Select folder"**.

Claude Code will now read the `CLAUDE.md` file automatically. This means it already knows what your project is and how to run the pipeline — you don't need to teach it from scratch.

To confirm it's working, in the Claude Code chat type:

```
What is this project?
```

Claude should respond explaining the 3-stage video analysis pipeline. If it says "I don't know what this project is" — verify that `CLAUDE.md` exists in the root of your folder and try reopening the folder.

> ✅ **Checkpoint:** Claude Code is open with `video-analysis/` as the working folder. Claude correctly describes the 3-stage video analysis pipeline when asked "What is this project?".

---

## Step 4 — Install Python and ffmpeg (one-time setup)

This is the only "technical" step. Claude Code will do most of the work — you just need to ask it.

### If you're on Windows

You need **WSL (Windows Subsystem for Linux)** because the Meta/Google Python packages don't ship Windows binaries reliably. WSL gives you a mini-Linux inside Windows where everything works smoothly.

In Claude Code chat, type:

```
Set up WSL with Ubuntu, install Python 3.12, ffmpeg, and the Python packages I need for this project (google-genai, weasyprint, pypdf, pymupdf, pillow).
```

Claude Code will:
1. Check if WSL is already installed
2. If not, run the installation command (this may require a Windows restart — Claude will tell you)
3. Install Ubuntu inside WSL
4. Install Python 3.12 inside Ubuntu
5. Install ffmpeg via `apt install ffmpeg`
6. Install the Python packages: `google-genai`, `weasyprint`, `pypdf`, `pymupdf`, `pillow`

Follow the prompts. If at any point Claude says "please run this command yourself in PowerShell" — copy the command, open PowerShell from Start Menu, paste, press Enter, and tell Claude when it's done.

**Total time:** 15–25 minutes including download time.

### If you're on macOS

You probably already have most of what you need. In Claude Code chat, type:

```
Install Homebrew if it's not already installed, then install ffmpeg and Python 3.12. Then install the Python packages: google-genai, weasyprint, pypdf, pymupdf, pillow.
```

Claude Code will:
1. Check for Homebrew (the macOS package manager)
2. Install it if missing (one command)
3. Install ffmpeg and Python via Homebrew
4. Install the Python packages via pip

**Total time:** 5–10 minutes.

### If you're on Linux (Ubuntu / Debian-based)

In Claude Code chat, type:

```
Install ffmpeg, Python 3.12, and the Python packages google-genai, weasyprint, pypdf, pymupdf, pillow.
```

Claude will use `apt` and `pip`. Done in 3–5 minutes.

### Verifying installation

After Claude says installation is complete, ask:

```
Run the API health check script to verify Python and the Gemini package are installed correctly.
```

Claude will run `python3 scripts/test_api.py`. You should see "No API key in .env" — that's expected. You haven't added the key yet (next step). It confirms Python + the package are working.

> ✅ **Checkpoint:** Python, ffmpeg, and the required packages are installed. The health-check script runs and shows the expected "No API key in .env" message (not a "module not found" error).

---

## Step 5 — Get a free Gemini API key

You need this for the Stage 1 video transcription. Free tier covers ~50 videos/day, more than enough for testing and small agency batches.

1. **Open** <https://aistudio.google.com/app/apikey> in your browser.
2. **Sign in** with any Google account.
3. Click **"Create API key"** (top right or middle of page).
4. **Choose "Create API key in new project"** (or pick an existing project if you have one).
5. A long string starting with `AIza...` will appear. **Copy it to clipboard.**
6. **Do NOT close the page yet** — if you lose this key, you'll need to generate a new one.

> **Privacy note:** on free tier, Google may use your video uploads for model improvement. For client-confidential work, enable paid billing (see "Going to paid tier" section near the bottom of this file). For your own brand testing, free tier is fine.

> ✅ **Checkpoint:** You have a long string starting with `AIza...` copied to your clipboard. The AI Studio tab is still open in your browser (in case you need to copy it again).

---

## Step 6 — Save the API key in `.env`

The key lives in a file called `.env` inside your project folder. Claude needs it to call the Gemini API, but Claude itself should NEVER see the actual key — so you'll paste it manually.

You have **two ways** to create the `.env` file. Method A is recommended — it works the same on Windows, macOS, and Linux without any extension-related Windows headaches.

### Method A — Ask Claude Code to do it (recommended)

In Claude Code chat, type:

```
Create a .env file in this project from .env.example. Don't put a real key in it — leave the placeholder. I'll paste the key myself.
```

Claude will create `.env` with the placeholder text. Then jump to the **"Paste your key"** section below.

### Method B — Through File Explorer manually (if you prefer)

You'll work inside your `video-analysis/` folder — the one you copied the starter files into in Step 2. Open it in your file manager:
- **Windows:** open File Explorer, navigate to wherever you placed `video-analysis/` (e.g. `C:\Users\<your-name>\video-analysis\`).
- **macOS:** open Finder and go to that folder.
- **Linux:** open your file manager at that folder.

**On Windows:**

1. **Enable file extensions first** so you can see them properly: File Explorer → **View** tab (top) → check **"File name extensions"**. Without this, Windows hides extensions and you won't be able to verify the file is really named `.env`.
2. Find the file `.env.example` in the folder. Right-click it → **Copy**.
3. Right-click in empty space inside the same folder → **Paste**. A file named `.env.example - Copy` (or similar) appears.
4. Right-click the new file → **Rename** → type exactly `.env` (no `.txt`, no `- Copy`, just `.env`).
5. Windows will warn "the file has no extension". Click **Yes**.

**On macOS:**

1. In Finder, find `.env.example` in the folder.
2. Right-click → **Duplicate**.
3. The copy is named `.env example copy`. Right-click → **Rename** → change to `.env`.
4. macOS will warn about the leading dot. Click **Use "."**.

### Paste your key

Once `.env` exists (by any of the three methods above), open it in a plain text editor:
- **Windows:** Right-click `.env` → **Open with** → **Notepad**. (If Notepad isn't in the list, click "Choose another app" → Notepad.)
- **macOS:** Right-click `.env` → **Open with** → **TextEdit**. Or in terminal: `open -a TextEdit .env`.
- **Linux:** Right-click → **Open with text editor**. Or `nano .env` in terminal.

You'll see:

```
GEMINI_API_KEY=PASTE_YOUR_KEY_HERE
```

**Replace** `PASTE_YOUR_KEY_HERE` with the long `AIza...` key you copied from Google AI Studio. The line should look like:

```
GEMINI_API_KEY=AIzaSyABC...long_string_here...XYZ123
```

> ⚠️ **Critical:** no quotes around the key, no spaces around the `=` sign. Pure `KEY=VALUE` format.

**Save** the file:
- Notepad: `Ctrl+S` → close.
- TextEdit: `Cmd+S` → close. If asked about format, choose **"Make Plain Text"**.
- nano: `Ctrl+O` → Enter → `Ctrl+X`.

### Verify the file is really called `.env` (not `.env.txt`)

On Windows specifically, Notepad sometimes saves files with a hidden `.txt` extension even if you typed `.env` as the name. To verify, ask Claude Code:

```
Check whether I have a file named exactly ".env" (not ".env.txt" or ".env.example") in this project folder.
```

Claude will list what it finds. If it reports `.env.txt` instead of `.env` — ask Claude to rename it:

```
Rename .env.txt to .env in this project folder.
```

### Verify the key works

In Claude Code chat, type:

```
Verify my Gemini API key works by running the test API script.
```

Claude will run `python3 scripts/test_api.py`. If everything is set up, you'll see:

```
Connecting to Gemini API...
  ✓ 50 models available

Models suitable for video analysis (Gemini 2.x / 1.5):
  - gemini-2.0-flash
  - gemini-2.5-flash
  - gemini-2.5-pro
  ...
```

If you see an error about the key — re-check that you pasted it correctly (no extra spaces, no quotes around it).

> ✅ **Checkpoint:** Running the test script shows "Connecting to Gemini API… ✓ 50 models available" plus a list of `gemini-2.x-flash`, `gemini-2.5-pro`, etc. Setup is complete.

---

## Step 7 — Do your first video analysis

Now the fun part. Time to analyze some videos.

### Drop videos into a project folder

1. Inside your `video-analysis/videos/` folder, **create a subfolder** for your project. Name it whatever makes sense to you — for example `my-first-test`, `competitor-research-may`, `client-fitness-brand`.
2. **Put 1–10 video files** inside that subfolder. Supported formats: `.mp4`, `.mov`, `.webm`, `.m4v`, `.mkv`.

Example structure:
```
videos/
└── my-first-test/
    ├── creative_01.mp4
    ├── creative_02.mp4
    └── creative_03.mov
```

> **Tip:** start with 2–3 short videos (under 30 seconds each) for your first run. You'll see results faster.

### Tell Claude to analyze them

In Claude Code chat, type:

```
Analyze videos in my-first-test
```

(Replace `my-first-test` with whatever you named your subfolder.)

Claude will:
1. Run Stage 1 — send each video to Gemini Flash for transcription (~30 sec per video, parallel)
2. Run Stage 2 — read each transcription and produce a strategic markdown table with concept type, hook/body/CTA breakdown, pattern labels
3. Run Stage 3 — extract thumbnails, generate the interactive HTML dashboard

For 3 videos, total time ≈ 3–5 minutes.

When done, Claude will tell you:

> Dashboard ready at `videos/my-first-test/dashboard/dashboard_my-first-test.html`. Open with double-click.

### Open the dashboard

Navigate to that file in your file manager and double-click. Your default browser will open it.

You'll see:
- **Project header** with concept counts, pattern counts, vertical breakdown
- **Cards for each video** with thumbnail, concept type, brand, format, key takeaway
- **Click any card** → opens the per-video page with sticky video player on the left, hook/body/CTA tables on the right with clickable timestamps that seek the video

> ✅ **Checkpoint:** The dashboard opens in your browser. You see one card per video with a thumbnail and concept label. Clicking a card opens the per-video page where the video plays in the left column and timestamps in the right tables jump the video to that moment when clicked.

---

## Step 8 — Daily workflow (after setup is done)

For new batches:

1. Create a new subfolder under `videos/` (e.g. `videos/promo-june/`)
2. Drop videos in
3. In Claude Code, say: `analyze videos in promo-june`
4. Wait 5–10 minutes
5. Open the dashboard

That's it.

You can also ask Claude things like:

- `Summarize the videos in promo-june` — cross-video insights without re-running the pipeline
- `Compare the hook patterns between promo-may and promo-june` — works across multiple folders
- `Write a new ad script in the style of the videos in competitor-research-may, but for [my product]` — uses the analyzed videos as a swipe-file reference
- `Refresh analysis for video creative_03` — re-analyze a specific video (e.g. after editing it)

---

## Troubleshooting

### "I don't know what this project is" when asking Claude

Claude Code didn't load `CLAUDE.md`. Make sure:
- The file is named exactly `CLAUDE.md` (not `claude.md` or `Claude.md`)
- It's in the root of your folder, not in a subfolder
- You opened the correct folder in Claude Code (try reopening)

### "GEMINI_API_KEY not found" or "No valid GEMINI_API_KEY in .env"

- Check `.env` exists in the root of your folder (NOT `.env.example`)
- Open `.env` in Notepad — the line should be exactly `GEMINI_API_KEY=AIza...` with no spaces around `=`
- No quotes around the key value: `GEMINI_API_KEY=AIza...` ✓ , `GEMINI_API_KEY="AIza..."` ✗

### "429 RESOURCE_EXHAUSTED" during analysis

You hit the free tier rate limit. The script will retry automatically (up to 5 times). If it still fails after retries:
- Wait 1 minute and re-run (`analyze videos in <folder>` again — the script skips already-processed videos)
- Or enable Gemini paid tier (see below)

### `.mov` files not playing in the dashboard

The script auto-converts `.mov` → `.mp4` for browser compatibility. If a `.mov` still doesn't play, ask Claude:

```
Re-render the dashboard for <folder> and force-convert all .mov files.
```

### Thumbnails not showing in dashboard

The browser might be blocking local file images. Try:
- Right-click the dashboard tab → reload
- Or open the file via the terminal command Claude can give you (uses a localhost server for one-click testing)

### Claude wants to do something destructive

Claude Code asks for confirmation before deleting files, modifying scripts, or running anything risky. If you're unsure — just say "no, don't do that" and ask what alternative exists.

---

## Going to paid Gemini tier (optional)

For agency work with client data, paid tier offers:
- No data used for training (privacy-safe for client confidentiality)
- Higher rate limits (15 RPM → 2000 RPM)
- Access to Gemini 2.5 Pro (free tier blocks it)
- Per-token pricing: ~$0.05 per video on Flash, ~$0.10 on Pro

Cost example: 100 videos/month on Flash ≈ $3–5 total.

To enable:
1. Go to <https://console.cloud.google.com/billing>
2. Link a billing account to your AI Studio project
3. Set a budget cap ($20–50/month is plenty for typical agency volumes) under Billing → Budgets & Alerts

That's it. The same API key works. No script changes needed.

---

## What's actually in this project

If you want to understand the moving parts:

- **`scripts/batch_analyze.py`** — Runs Gemini Flash on a folder of videos. Saves `.gemini.md` files (raw 3-track transcriptions: visual, on-screen text, audio).
- **Stage 2 (Claude does this manually in chat)** — Reads each `.gemini.md` and produces a `.md` in `analysis/` subfolder with the table format defined in `CLAUDE.md`.
- **`scripts/render_project.py`** — Extracts thumbnails, converts `.mov`→`.mp4`, generates the interactive HTML dashboard from the `.md` files.
- **`scripts/analyze_video.py`** — Single-video version of Stage 1 (called by `batch_analyze.py`, also usable standalone).
- **`scripts/compare_models.py`** — Optional tool: runs the same prompt through Flash and Pro models for side-by-side comparison.
- **`scripts/test_api.py`** — Health check for your Gemini API key.

You don't need to touch any of these scripts to use the project. They're documented if you want to extend.

---

## Updating the starter kit

If you got this kit and later want to update it:
- The `CLAUDE.md` file evolves as the workflow improves. Pull the latest version and replace yours.
- Scripts are stable; only update if a bugfix is mentioned.
- Your `.env`, your `videos/`, and your generated `analysis/` and `dashboard/` folders are yours — never overwrite them.

---

## License

MIT — do whatever you want with this. Credit appreciated but not required.

---

## Questions and contributions

If you hit something this README didn't cover, that's a bug in the docs. Open an issue / send a message and it'll get fixed.

If you build something cool on top of this — share it. The whole point of templates is collective leverage.
