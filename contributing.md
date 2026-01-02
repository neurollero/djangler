# Contributing to DJANGLER

Thanks for your interest in improving DJANGLER! Here's how you can help.

## Ways to Contribute

### 1. Playlist Suggestions
Help expand the dataset with curated playlists:

**What we're looking for:**
- Genre-specific playlists (underrepresented: jazz, country, metal, folk)
- Mood/vibe playlists (chill, energetic, melancholic)
- Era-specific (60s, 70s, 80s, etc.)
- High-quality curation (not auto-generated)

**How to suggest:**
1. Open an issue with title: "Playlist: [Genre/Theme]"
2. Include Spotify playlist URL
3. Brief description of why it fills a gap

### 2. Bug Reports
Found something broken?

**Include:**
- Your Python version
- Full error message
- Steps to reproduce
- What you expected vs. what happened

### 3. Feature Requests
Have an idea?

Open an issue describing:
- The problem it solves
- Proposed solution
- Any implementation ideas

### 4. Code Contributions

**Before submitting a PR:**
- Open an issue to discuss major changes
- Follow existing code style
- Test your changes thoroughly
- Update documentation if needed

**Setup:**
```bash
git clone https://github.com/[your-username]/djangler.git
cd djangler
pip install -r requirements.txt
cp .env.example .env
# Add your API keys to .env
```

**PR Guidelines:**
- Clear description of changes
- Reference related issues
- Keep PRs focused (one feature/fix per PR)
- Add tests if applicable

## Important Notes

### Genius API Restrictions
- **Non-commercial use only** per Genius API TOS
- Do not commit API keys or tokens
- Each contributor uses their own API credentials

### Copyrighted Content
- Never commit `songs_data.json` (contains copyrighted lyrics)
- Distribution uses metadata-only format
- Users fetch lyrics with their own API keys

### Code of Conduct
- Be respectful and constructive
- Focus on ideas, not people
- Help create a welcoming community

## Questions?
Open an issue or reach out in discussions.

Thanks for contributing! 🎵