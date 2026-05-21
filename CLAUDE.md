# Video Analysis Project — Claude Instructions

This file is auto-loaded by Claude Code when this project is opened. It defines the workflow, output format, taxonomies, and conventions for analyzing video ad creatives.

## What this project does

A 3-stage pipeline that turns a folder of ad video files into a browsable interactive HTML dashboard with structured creative analysis:

```
folder of .mp4/.mov  →  Gemini Flash transcription  →  Claude strategic table  →  HTML dashboard
                            (Stage 1 — script)         (Stage 2 — YOU)          (Stage 3 — script)
```

## When the user says "analyze videos in <folder>"

Run all three stages automatically. Do not ask for confirmation between stages — proceed end-to-end unless something fails.

**Stage 1 — Gemini transcription (script)**
```bash
python3 scripts/batch_analyze.py <folder>
```
- Reads videos from `videos/<folder>/`
- For each `.mp4`/`.mov`/`.webm`/`.m4v`/`.mkv`, sends to Gemini Flash and saves raw 3-track transcription as `videos/<folder>/<video>.gemini.md`
- Already-processed videos are skipped (delete the `.gemini.md` to force re-analysis)
- `.mov` files: leave them alone — Stage 3 converts to `.mp4` for browser playback
- Free tier: 15 RPM. Script handles 429/503 retries automatically. ~30 sec per video at concurrency 5.

**Stage 2 — Strategic table (YOU, this Claude)**
- For each `.gemini.md` that doesn't yet have a matching `.md` in `videos/<folder>/analysis/`, produce a Stage 2 markdown using the exact format described below
- Save the result to `videos/<folder>/analysis/<video_stem>.md`
- The `analysis/` subfolder must exist (create it if missing)

**Stage 3 — HTML dashboard (script)**
```bash
python3 scripts/render_project.py <folder>
```
- Extracts thumbnails via ffmpeg (embedded if available, else 20% of duration)
- Converts `.mov` to `.mp4`
- Generates `videos/<folder>/dashboard/data/<video>.html` per video (sticky video player + clickable timestamps that seek the video)
- Generates `videos/<folder>/dashboard/dashboard_<folder>.html` with all cards + cross-stats

After all three stages complete, tell the user: "Dashboard ready at `videos/<folder>/dashboard/dashboard_<folder>.html`. Open with double-click."

## Folder convention

```
videos/<project>/
├── <video>.mp4                ← original video
├── <video>.gemini.md          ← Stage 1 raw (kept for audit / debugging)
├── analysis/
│   └── <video>.md             ← Stage 2 final table (the useful output)
└── dashboard/
    ├── dashboard_<project>.html  ← main entry point
    └── data/
        ├── <video>.html          ← per-video interactive view
        └── <video>.thumb.jpg     ← thumbnail for the card
```

## Stage 2 — Output format (CRITICAL — follow exactly)

For each `.gemini.md`, parse the three tracks (VISUAL, ON-SCREEN TEXT, AUDIO) and produce a markdown file with this exact structure:

```markdown
# <video filename stem>

**Brand:** <brand name or product>
**Concept type:** <one label from the Concept Taxonomy below, or a new CamelCase-ish label if none fit>
**Format:** <higher-level format description, e.g. "UGC talking head + kinetic typography demo">
**Tone:** <e.g. "Friendly, slightly conspiratorial">
**Vertical:** <e.g. "Tech accessories / travel gear">
**Key takeaway:** <one sentence describing what's most powerful about this creative and why — a learning, not a description>

## Hook (0 — <end>s)

| Time | Script | Overlay | Visual | Pattern | Why it works |
|---|---|---|---|---|---|
| <row...>

## Body (<start>s — <end>s)

| Time | Script | Overlay | Visual | Pattern | Why it works |
|---|---|---|---|---|---|
| <row...>

## CTA (<start>s — <end>s)

| Time | Script | Overlay | Visual | Pattern | Why it works |
|---|---|---|---|---|---|
| <row...>
```

### Row alignment rules

Each row in the table corresponds to a discrete unit of action — typically anchored to a visual scene boundary. For each row:

- **Time** — start-end in `0.0–2.1s` format. Use the visual scene's time range from Stage 1 as the anchor. The Script and Overlay columns aggregate everything that happens during that visual window.
- **Script** — verbatim VO that was active during this time window. If no VO, write `_(no VO)_` or describe what audio is present (e.g. `_(typing SFX)_`).
- **Overlay** — every on-screen text element that appeared during this time, joined with ` / ` if multiple. Preserve original casing.
- **Visual** — one-line description of what's on screen (subject, action, key visual detail).
- **Pattern** — one or more labels from the Pattern Taxonomy below, combined with ` + ` if multiple apply. Use ` (N/M) ` markers when the same pattern spans multiple rows (e.g. `Demo / Proof (2/4)`).
- **Why it works** — strategic insight in one sentence. NOT a description of what's there — an explanation of why this beat lands. Use marketing reasoning (e.g. "Live demo replaces claim with evidence" or "Specific dollar amount makes loss concrete").

### Hook duration rule

Hook must be **3.0 seconds ± 1 second** (range 2.0–4.0s).

How to pick the end of Hook:
1. **Find scene boundaries** in the [2.0s, 4.0s] window from Stage 1's VISUAL track
2. **If a boundary exists** in that range → cut Hook there (prefer closest to 3.0s)
3. **If no boundary** in that range → cut Hook exactly at 3.0s, even if mid-scene. Mark the next Body row with `(cont.)` to indicate continuation.
4. **If video is very short** (total under 2.5s) → Hook is the whole intro until the natural break

Examples:
- Visual scenes at 0–0.4s, 0.4–4.5s → no boundary in [2.0, 4.0] → Hook ends at 3.0s (mid-scene cut). Body starts with a `(cont.)` row.
- Visual scenes at 0–2.9s, 2.9–12.8s → boundary at 2.9s falls in [2.0, 4.0] → Hook ends at 2.9s.
- Visual scenes at 0–1.1s, 1.1–2.0s, 2.0–3.1s, 3.1–4.0s → boundary at 3.1s (closest to 3.0) → Hook ends at 3.1s.

Never let Hook exceed 4.0s or fall below 2.0s unless the entire video is shorter than that.

### Body and CTA boundaries

- **Body** starts where Hook ends and goes until the CTA begins
- **CTA** starts when the verbal/visual call-to-action begins. Typically signals: imperative VO ("Click below", "Visit X", "Get yours"), end-card overlays ("SHOP NOW", "LEARN MORE"), or domain drops, or the final 5–10 seconds with the offer/closing message
- For videos with no explicit CTA (e.g. wordless POV reaction skits) — write a `## CTA — implicit` section with prose explanation instead of a table

## Concept Taxonomy

Pick the closest label from this list. If genuinely nothing fits, invent a new CamelCase-ish label that describes the format. Common labels:

- `Fake Phone Call` — dramatized phone-call dialog (customer ↔ rep)
- `Unboxing UGC` — package arrival + reveal, with or without dialog
- `Man-on-the-Street Interview` — documentary-style interviewer + responses, brand reveal at end
- `POV Reaction Skit` — wordless or near-wordless face reaction with persistent overlay caption
- `Storytime Pain Stack → Before/After Demo` — extended problem narrative then product solution
- `Frustration → Comparison + Offer` — visual frustration cold open, then side-by-side comparison, then discount close
- `Kinetic Typography + Live Demo` — rapid word-by-word overlay text synced with product demonstration
- `Visual Gag UGC + Offer Stack` — single physical metaphor gag (reaching for signal, crumpling bills, etc.) + benefit stack
- `Authority Drop UGC` — talking head referencing a celebrity, doctor, or expert authority
- `Symptom Stack + Authority Drop` — rapid symptom-button stack in hook + authority pivot in body
- `Direct Response Talking Head` — presenter on camera, claim + agitation + proof + CTA in rapid succession
- `Voiceover Listicle + B-roll` — VO-driven feature-stack with synced B-roll cutaways
- `Testimonial Compilation` — multiple users sharing experience, brand reveal at end
- `Split-Screen Comparison` — old way vs new way side by side
- `Tutorial / How-To` — step-by-step instruction with product as the tool
- `Day-in-the-Life Lifestyle` — aspirational use-case montage with the product

When picking, focus on **the overall structural concept**, not the individual beats. A video that uses kinetic typography in the body but is fundamentally about a phone-call dialog is still `Fake Phone Call`.

## Pattern Taxonomy

Used in the **Pattern** column of each row. Combine with ` + ` when multiple patterns apply.

### Hook patterns
- `Pattern Interrupt` — sudden visual/audio surprise that breaks autoplay scroll
- `Question Hook` — "What if…", "Did you know…", "Are you struggling with…"
- `Bold Claim` — "Lost 30 lbs in 30 days", "The #1 X for Y"
- `Vulnerable Confession` — "I used to think…", "I didn't realize…"
- `Authority Drop` — "Doctors don't want…", "Mike Tyson's brand"
- `Curiosity Gap` — "The one thing nobody tells you…"
- `Negative Open` — "Stop doing X", "Don't buy X until…"
- `Social Proof Open` — "Over 100K people…", "Trending on TikTok"
- `POV/Relatability` — "If you're a [audience type]…", direct address
- `Storytime` — narrative opener implying a tale will be told
- `Visual Gag` — physical metaphor acting out an abstract concept
- `Trend-jack` — using a viral sound, meme, or format

### Body patterns
- `Problem Agitation` — describing the pain in detail, often stacked
- `Solution Reveal` — introducing/naming the product
- `Demo / Proof` — product in action, physical demonstration
- `Mechanism` — explaining how/why it works (the "science" beat)
- `Feature → Benefit` — property + its outcome for the user
- `Before / After` — transformation visualization
- `Social Proof` — testimonials, user counts, ratings, peer use
- `Comparison` — vs competitor, vs "old way"
- `Stack Value` — listing benefits, bundling, "and you also get…"
- `Story` — narrative arc with character/setting
- `Authority` — expert in frame, credentials, certification
- `Objection Handling` — pre-empting doubts ("but what about…")
- `Lifestyle Proof` — aspirational use-case context
- `Urgency Build` — limited time, scarcity
- `Specific Claim` — numeric/concrete promise ("$9/month", "5 minutes")

### CTA patterns
- `Soft CTA` — "Check it out", "This is the one", recommendation tone
- `Hard CTA` — "Buy now", "Get yours today", imperative
- `Risk Reversal` — money-back, free trial, guarantee
- `Scarcity` — "Almost sold out", limited stock
- `Discount / Offer` — % off, free shipping, bundle
- `Implicit CTA` — no explicit ask, just end-card with brand + product
- `Domain Drop` — specific URL spoken or displayed

## Stage 2 quality bar

- **Be specific, not generic.** "Visual gag" alone is weak. "Reaching arm = literal acting-out of 'losing signal'" is the goal.
- **Why-it-works column must explain mechanism**, not describe content. Bad: "Shows the product." Good: "Live water-pour demo replaces the claim with evidence."
- **Use exact timestamps from Stage 1** — don't round or invent
- **Acknowledge edge cases** — if Gemini truncated the visual track, note it. If VO says one thing but overlay says another, flag the copy drift.
- **No marketing fluff adjectives** in the Why column — avoid "engaging", "compelling", "powerful". Use mechanism words: "primes", "anchors", "pre-empts", "stacks", "pivots", "lands".

## Pipeline triggers (how user requests work)

- **"analyze videos in <folder>"** or **"проанализируй видео в <folder>"** → run Stage 1 (batch_analyze.py), then do Stage 2 for any missing `.md` in `analysis/`, then run Stage 3 (render_project.py). Tell user where the dashboard is when done.
- **"re-render <folder>"** → just Stage 3 (rebuilds HTML/dashboard without re-analyzing)
- **"refresh analysis for <video>"** → delete `<video>.gemini.md` and the matching `<video>.md`, re-run pipeline
- **"summarize <folder>"** or **"what's in <folder>"** → read all `analysis/*.md` and produce a cross-video summary inline (don't re-run anything)
- **"write a script in the style of <concept>"** or **"based on these, draft a new ad for X"** → read all relevant `.md` files, then produce a creative brief drawing on the patterns observed

## Concurrency and rate limits (Stage 1)

- Default concurrency is 5 (safe for Gemini free tier)
- If user has paid Gemini billing enabled, can raise to 15-20 via `--concurrency` flag
- On 429 (rate limit) or 503 (server unavailable), the script retries up to 5 times with exponential backoff
- Per-video time: ~30 seconds (upload-bound for large files, analysis ~10-30 seconds)

## Model selection

- **Default**: `gemini-2.5-flash` (free tier supports unlimited, paid tier ~$0.05-0.10 per video)
- **Pro alternative**: `gemini-2.5-pro` requires paid billing (free tier rejects with 429). Used via `--model gemini-2.5-pro` for deeper analysis on individual videos. For batch agency work, Flash is sufficient — Pro's reasoning advantage is in interpretation, which YOU (Claude in Stage 2) handle anyway.

## What NOT to do

- Do NOT add `Hook rating` or any subjective scoring to the Stage 2 output. It was deliberately removed.
- Do NOT include keyframe images in the per-video table rows. The dashboard has thumbnails on cards only.
- Do NOT auto-commit to git. The `.gitignore` excludes secrets and videos, but the user controls commits.
- Do NOT read the `.env` file unless explicitly asked. The Gemini key lives there, and the user prefers to keep it untouched.
- Do NOT modify scripts to add experimental features without asking. They're stable; iterate on prompts and taxonomies first.
