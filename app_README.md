---
title: DJANGLER
emoji: 🎵
colorFrom: purple
colorTo: pink
sdk: streamlit
sdk_version: 1.28.0
app_file: app.py
pinned: false
---

# 🎵 DJANGLER

**Find songs by what they mean, not just what they say.**

Semantic search engine for song lyrics. Search by meaning, theme, or mood instead of keywords.

## Features

- **Semantic Search**: "feeling lost" finds songs about confusion and searching
- **Genre Boosting**: Weight results by musical style
- **Section Matching**: See the exact verse/chorus that matches

## Examples
```
indie songs about loneliness
heartbreak and longing
childhood memories
rock anthems rebellion
```

## Dataset

~9,000 songs with vector embeddings of lyrics and metadata (genres, artists, release dates).

## Tech

- **Embeddings**: sentence-transformers (all-mpnet-base-v2)
- **Vector DB**: ChromaDB
- **Data Sources**: Spotify + Genius

## Source

Full pipeline + code: [github.com/youruser/djangler](https://github.com/youruser/djangler)