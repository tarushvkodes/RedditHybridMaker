# RedditHybridMaker — Usage Context (Tarushv setup)

This file captures the exact context needed to run the project reliably on this machine.

## Current Goal
Generate **long-form horizontal videos** (10+ min) by combining **multiple Reddit posts** into one final MP4.

## Stable Runtime Notes
- Python: **3.13.x**
- MoviePy: **1.0.3** (important; v2 API breaks this codebase paths)
- Voice mode in use: `qwen3clone`

## Important Content/Policy Settings
These are intentionally configured:
- `ai_similarity_enabled = false`
- AutoModerator comments excluded in `reddit/subreddit.py`
- Profanity words are silenced (timing preserved) in `TTS/engine_wrapper.py`

## config.toml shape for long-form horizontal generation
Use values in this range (exact values can be tuned):

```toml
[settings]
times_to_run = 8                # generate multiple posts
storymode = true
hybrid_mode = true
hybrid_comments_count = 8       # include post + comments
storymode_max_length = 25000
resolution_w = 1920
resolution_h = 1080

[reddit.thread]
max_comment_length = 10000      # must be <= 10000 in this build
min_comment_length = 1
min_comments = 10
subreddit = "Sat+SAT_Math+satprep+digitalSATs"
```

## One-shot workflow for a single long-form combined output
1. Generate multiple posts in one run:
```powershell
python main.py --times 8
```

2. Concatenate newest outputs into one long video:
```powershell
$repo='C:\Users\tarus\Downloads\RedditHybridMaker'
$outDir=Join-Path $repo 'results\Sat+SAT_Math+satprep+digitalSATs'
$joinedDir=Join-Path $repo 'results\joined'
New-Item -ItemType Directory -Force -Path $joinedDir | Out-Null

$newest = Get-ChildItem $outDir -Filter *.mp4 -File |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 8 |
  Sort-Object LastWriteTime

$listPath = Join-Path $joinedDir 'concat_list.txt'
$newest | ForEach-Object { "file '$($_.FullName.Replace("'","''"))'" } |
  Set-Content -Path $listPath -Encoding UTF8

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$outFile = Join-Path $joinedDir ("SAT_longform_horizontal_"+$stamp+".mp4")

& "$repo\ffmpeg.exe" -y -f concat -safe 0 -i $listPath -c copy $outFile
if($LASTEXITCODE -ne 0){
  & "$repo\ffmpeg.exe" -y -f concat -safe 0 -i $listPath \
    -c:v libx264 -preset veryfast -crf 20 -c:a aac -b:a 192k $outFile
}

& "$repo\ffprobe.exe" -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 $outFile
Write-Output "FINAL_FILE=$outFile"
```

## Known failure mode
If run pauses with:
- `Non-optional max_comment_length=` prompt

then `max_comment_length` is out of template bounds. Keep it `<= 10000`.

## Security note
`config.toml` is intentionally gitignored. Keep secrets (Reddit creds, API keys) local only.
