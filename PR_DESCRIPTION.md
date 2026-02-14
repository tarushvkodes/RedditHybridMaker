# Description

This PR introduces a brand new **Hybrid Mode** feature to the Reddit Video Maker Bot that combines both post content and comments in a single video. This feature is specifically designed to work well with educational subreddits like SAT/Math communities where posts often contain images with explanatory content in the comments.

## New Features Added:

### 1. **Hybrid Mode Implementation**
- Introduces a new video creation mode that combines post content with top comments
- Configurable via new `hybrid_mode` setting in config.toml
- Creates videos with structure: Title → Post Content → Top Comments
- Perfect for educational content where discussions add value

### 2. **Intelligent Post Selection**
- Uses HOT ranking instead of TOP for more current and engaging posts
- Increased post limits (100+ posts) to find suitable content
- Handles both text posts and image/link posts with explanatory comments
- Marks processed posts to prevent duplicate video creation
- Includes robust error handling and fallback mechanisms
- Progressive fallback: hot → new → week → month → year → all time posts

### 3. **Smart Content Detection**
- Prioritizes post selftext (≥30 characters) as primary content
- Falls back to OP comments when selftext is insufficient or missing
- Searches through comments to find substantial OP explanations
- Ensures videos always have meaningful content

### 4. **Configurable Comment Requirements**
- New `hybrid_comments_count` setting to control minimum comments needed
- Default set to 1 for maximum subreddit compatibility
- Prevents videos from posts with insufficient discussion
- Balances content quality with availability

### 5. **Enhanced Video Creation**
- Modified video generation to properly display title frames
- Ensures title frame is visible before content overlays begin
- Improved video pacing and readability for hybrid content
- Maintains compatibility with existing video creation pipeline

### 6. **User Experience Features**
- Clear console feedback about post selection process
- Debug output for troubleshooting post filtering
- Progress indicators during video processing
- Comprehensive documentation and usage examples

## New Configuration Options:
```toml
[settings]
hybrid_mode = true                # Enable/disable hybrid mode
hybrid_comments_count = 1         # Minimum comments required
```

## Files Added/Modified:
- `reddit/subreddit.py` - Enhanced post selection logic for hybrid mode
- `utils/subreddit.py` - Added post filtering and validation logic
- `video_creation/final_video.py` - Modified video creation for hybrid content
- `config.toml` - Added new hybrid mode configuration options
- `README.md` - Added comprehensive hybrid mode documentation and usage guide

# Issue Fixes

<!-- Fixes #(issue) if relevant-->

None - This introduces a new hybrid mode feature to expand the bot's capabilities for educational content creation.

# Checklist:

- [x] I am pushing changes to the **develop** branch
- [x] I am using the recommended development environment
- [x] I have performed a self-review of my own code
- [x] I have commented my code, particularly in hard-to-understand areas
- [x] I have formatted and linted my code using python-black and pylint
- [x] I have cleaned up unnecessary files
- [x] My changes generate no new warnings
- [x] My changes follow the existing code-style
- [x] My changes are relevant to the project

# Any other information (e.g how to test the changes)

## Quick Start for Testing:
```powershell
# Navigate to project directory
cd "c:\Users\ayaan\Downloads\RedditHybridMaker"

# Backup current videos.json (optional)
Copy-Item "video_creation\data\videos.json" "video_creation\data\videos_backup.json"

# Clear videos.json for fresh testing
echo "[]" > "video_creation\data\videos.json"

# Run the bot
python main.py
```

## Testing Instructions:

### 1. **Test New Hybrid Mode Feature**
```bash
# Test the new hybrid mode
python main.py
# When prompted, select "yes" for hybrid mode
# Choose educational subreddits like: SAT, satprep, APStudents, HomeworkHelp
```

### 2. **Test Configuration Options**
```toml
# Add to config.toml to test different settings
[settings]
hybrid_mode = true
hybrid_comments_count = 1  # Try values: 1, 3, 5
```

### 3. **Test Post Selection Logic**
```bash
# Clear existing videos to test fresh post selection (IMPORTANT!)
# Backup current videos.json first
copy "video_creation\data\videos.json" "video_creation\data\videos_backup.json"
# Then clear it for fresh testing
echo "[]" > "video_creation\data\videos.json"
python main.py
# Monitor console output for post filtering messages
```

### 4. **Test Video Creation**
- Generate a hybrid mode video
- Verify title frame displays properly
- Check that video includes both post content and comments
- Ensure video pacing feels natural

### 5. **Test Error Handling**
- Try with subreddits that have few posts
- Test with different comment requirements
- Verify graceful handling when no suitable posts found

## Expected Behavior:
- **New Hybrid Mode Option**: Bot should prompt for hybrid mode selection during setup
- **Smart Content Detection**: Should find content from both post selftext and OP comments
- **Combined Videos**: Videos should include both post content and top comments
- **Proper Video Layout**: Title frame should be visible before content overlays
- **Robust Operation**: Should handle various subreddit types without issues

## What This Feature Enables:
- **Educational Content**: Perfect for SAT, Math, and other educational subreddits
- **Discussion-Based Videos**: Combines original posts with valuable community discussions
- **Flexible Content Sources**: Works with text posts, image posts, and link posts
- **Quality Control**: Ensures videos only include posts with sufficient engagement

## Troubleshooting the New Feature:
If you encounter issues with hybrid mode:
1. **Clear processed posts**: Delete or backup `video_creation/data/videos.json` to reset post history
2. Ensure `hybrid_mode = true` is set in config.toml
3. Try lowering `hybrid_comments_count` for better post availability
4. Disable AI similarity: Set `ai_similarity_enabled = false` in config.toml
5. Check console output for detailed selection process information

**Important Note**: If the bot says "Post already processed" for all posts, you need to clear the videos.json file to allow reprocessing of posts.

This new hybrid mode significantly expands the bot's capabilities, making it ideal for educational content creation and discussion-based subreddits.
