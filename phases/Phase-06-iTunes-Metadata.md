# Phase 6: iTunes Metadata Search

## ⚠️ NOT IMPLEMENTED - Removed in v3.0 ⚠️

This phase was originally planned to implement iTunes API metadata search as a secondary source. However, in version 3.0 of the OBS YouTube Player, the metadata system was simplified to use only:

1. **Google Gemini AI** (Primary) - AI-powered extraction with Google Search grounding
2. **Smart Title Parser** (Fallback) - Handles common YouTube title patterns

## Why Was This Removed?

- **Limited Coverage**: iTunes API only covers commercially released music
- **Genre Limitations**: Poor results for worship music, covers, and international content
- **API Restrictions**: Rate limits and geographic restrictions
- **Better Alternative**: Google Gemini provides superior coverage across all genres

## Current Metadata Flow

```
Video Title → Gemini AI (with Google Search)
                ↓ (if fails)
            Title Parser
                ↓
            Universal Cleaning
                ↓
            Final Metadata
```

The Gemini + fallback approach provides better results than the original multi-source system, with automatic retry for any failures.

## Original Phase Description

*For historical reference only - this functionality is not implemented in the current version.*

The original plan included:
- iTunes Search API integration
- Fuzzy matching for song titles
- Album artwork retrieval (not used)
- Geographic handling for API restrictions

---

*See Phase-13-Gemini-Metadata.md for the current metadata implementation.*