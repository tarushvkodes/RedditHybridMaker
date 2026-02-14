# RedditHybridMaker Runbook (for future me)

## Goal
Get stable multi-run generation working (e.g., 10/100 runs) without dependency churn.

## What worked before
The pipeline worked when using **Python Store env (3.13)** with **moviepy 1.0.3** API expectations (`moviepy.editor`, `subclip`, `volumex`).

## What broke it
- Installing broad/unpinned deps upgraded `moviepy` to v2 API.
- v2 removed/renamed APIs used by this code (`editor`, `subclip`, `volumex`).
- Trying to force old `playwright==1.44.0` on py313 triggers greenlet build failures.

## Stable recovery steps
From `C:\Users\tarus\Downloads\RedditHybridMaker`:

1) Ensure required modules exist (minimal set):
```powershell
python -m pip install --user --no-input boto3==1.34.127 botocore==1.34.127 gTTS==2.5.1 praw==7.7.1 clean-text==0.6.0 unidecode==1.3.8
```

2) Pin moviepy stack to v1-compatible (without touching playwright):
```powershell
python -m pip uninstall -y moviepy imageio imageio-ffmpeg
python -m pip install --user --no-input moviepy==1.0.3 --no-deps
python -m pip install --user --no-input imageio==2.37.0 imageio-ffmpeg==0.6.0 decorator==4.4.2
```

3) Verify:
```powershell
python -c "import moviepy,gtts,praw,boto3; print(moviepy.__version__)"
```
Expected: `1.0.3`

4) Run:
```powershell
python main.py
```

## Content rules to keep
- `config.toml`: `ai_similarity_enabled = false`
- Exclude AutoModerator comments in `reddit/subreddit.py`
- Swear-word silence mode enabled in TTS censor settings

## Guardrails
- Do **not** run broad `pip install -r requirements.txt` blindly on py313 if it downgrades playwright/greenlet.
- Do **not** run unpinned global upgrade sweeps during active production run.
- If MoviePy errors return, first check `moviepy.__version__`.
