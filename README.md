# Reddit Video Maker Bot 🎥

All done WITHOUT video editing or asset compiling. Just pure ✨programming magic✨.

Created by Lewis Menelaws & [TMRRW](https://tmrrwinc.ca)

<a target="_blank" href="https://tmrrwinc.ca">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://user-images.githubusercontent.com/6053155/170528535-e274dc0b-7972-4b27-af22-637f8c370133.png">
  <source media="(prefers-color-scheme: light)" srcset="https://user-images.githubusercontent.com/6053155/170528582-cb6671e7-5a2f-4bd4-a048-0e6cfa54f0f7.png">
  <img src="https://user-images.githubusercontent.com/6053155/170528582-cb6671e7-5a2f-4bd4-a048-0e6cfa54f0f7.png" width="350">
</picture>

</a>

## Video Explainer

[![lewisthumbnail](https://user-images.githubusercontent.com/6053155/173631669-1d1b14ad-c478-4010-b57d-d79592a789f2.png)
](https://www.youtube.com/watch?v=3gjcY_00U1w)

## Motivation 🤔

These videos on TikTok, YouTube and Instagram get MILLIONS of views across all platforms and require very little effort.
The only original thing being done is the editing and gathering of all materials...

... but what if we can automate that process? 🤔

## Disclaimers 🚨

- **At the moment**, this repository won't attempt to upload this content through this bot. It will give you a file that
  you will then have to upload manually. This is for the sake of avoiding any sort of community guideline issues.

## Requirements

- Python 3.10
- Playwright (this should install automatically in installation)

## Installation 👩‍💻

1. Clone this repository
2. Run `pip install -r requirements.txt`
3. Run `python -m playwright install` and `python -m playwright install-deps`

**EXPERIMENTAL!!!!**

On macOS and Linux (debian, arch, fedora and centos, and based on those), you can run an install script that will automatically install steps 1 to 3. (requires bash)

`bash <(curl -sL https://raw.githubusercontent.com/elebumm/RedditVideoMakerBot/master/install.sh)`

This can also be used to update the installation

4. Run `python main.py`
5. Visit [the Reddit Apps page.](https://www.reddit.com/prefs/apps), and set up an app that is a "script". Paste any URL in redirect URL. Ex:`https://jasoncameron.dev`
6. The bot will ask you to fill in your details to connect to the Reddit API, and configure the bot to your liking
7. Enjoy 😎
8. If you need to reconfigure the bot, simply open the `config.toml` file and delete the lines that need to be changed. On the next run of the bot, it will help you reconfigure those options.

(Note if you got an error installing or running the bot try first rerunning the command with a three after the name e.g. python3 or pip3)

If you want to read more detailed guide about the bot, please refer to the [documentation](https://reddit-video-maker-bot.netlify.app/)

## Features ✨

### Hybrid Mode
This bot includes an enhanced **Hybrid Mode** that combines both post content and comments in a single video, perfect for educational content and discussion-based subreddits like SAT/Math communities.

#### Hybrid Mode Improvements:
- **Smart Content Detection**: Automatically detects text content from both self-posts and OP comments
- **Flexible Post Types**: Works with both text posts and image/link posts where the Original Poster provides explanation in comments
- **Configurable Comment Requirements**: Set minimum comment count via `hybrid_comments_count` in config.toml
- **Intelligent Filtering**: Skips posts without sufficient content and marks them as processed to avoid loops
- **Enhanced Video Layout**: Title frame displays properly before content overlay begins

#### Configuration:
```toml
[settings]
hybrid_mode = true
hybrid_comments_count = 1  # Minimum comments required (recommended: 1-3)
```

#### How It Works:
1. **Content Priority**: Uses post selftext if available (≥30 characters)
2. **Fallback to OP Comments**: If no selftext, searches first 5 comments for substantial OP explanations
3. **Video Structure**: Title → Post Content → Top Comments
4. **Timing Fix**: Ensures title frame is visible before content overlays

This makes hybrid mode ideal for educational subreddits where posts often contain images with explanatory comments.

## Troubleshooting 🔧

### Hybrid Mode Issues

**"No suitable posts found" / Infinite loops:**
- **Solution**: Lower `hybrid_comments_count` to 1 in config.toml
- **Cause**: Many posts in educational subreddits have few comments

**"All submissions have been processed":**
- **Solution**: Delete `video_creation/data/videos.json` to reset processed posts
- **Alternative**: Use different subreddits with more text-based content

**Video title frame not visible:**
- **Fixed**: Title frame now displays properly before content overlay
- **Config**: Ensure `hybrid_mode = true` in settings

**Posts being skipped for "no text content":**
- **Fixed**: Bot now checks OP comments for content explanation
- **Works with**: Image posts where OP explains in comments

### General Issues

**"object of type 'ListingGenerator' has no len()" errors:**
- **Fixed**: Improved Reddit API handling for submission counting

**Import/module errors:**
- **Solution**: Run `pip install -r requirements.txt` and `python -m playwright install`

## Video

https://user-images.githubusercontent.com/66544866/173453972-6526e4e6-c6ef-41c5-ab40-5d275e724e7c.mp4

## Contributing & Ways to improve 📈

In its current state, this bot does exactly what it needs to do. However, improvements can always be made!

I have tried to simplify the code so anyone can read it and start contributing at any skill level. Don't be shy :) contribute!

- [ ] Creating better documentation and adding a command line interface.
- [x] Allowing the user to choose background music for their videos.
- [x] Allowing users to choose a reddit thread instead of being randomized.
- [x] Allowing users to choose a background that is picked instead of the Minecraft one.
- [x] Allowing users to choose between any subreddit.
- [x] Allowing users to change voice.
- [x] Checks if a video has already been created
- [x] Light and Dark modes
- [x] NSFW post filter
- [x] Enhanced Hybrid Mode with smart content detection
- [x] Improved post filtering and loop prevention
- [x] Better video timing for title frames
- [x] Support for image posts with OP explanations

Please read our [contributing guidelines](CONTRIBUTING.md) for more detailed information.

### For any questions or support join the [Discord](https://discord.gg/qfQSx45xCV) server

## Developers and maintainers.

Elebumm (Lewis#6305) - https://github.com/elebumm (Founder)

Jason (personality.json) - https://github.com/JasonLovesDoggo (Maintainer)

Simon (OpenSourceSimon) - https://github.com/OpenSourceSimon

CallumIO (c.#6837) - https://github.com/CallumIO

Verq (Verq#2338) - https://github.com/CordlessCoder

LukaHietala (Pix.#0001) - https://github.com/LukaHietala

Freebiell (Freebie#3263) - https://github.com/FreebieII

Aman Raza (electro199#8130) - https://github.com/electro199

Cyteon (cyteon) - https://github.com/cyteon


## LICENSE
[Roboto Fonts](https://fonts.google.com/specimen/Roboto/about) are licensed under [Apache License V2](https://www.apache.org/licenses/LICENSE-2.0)
