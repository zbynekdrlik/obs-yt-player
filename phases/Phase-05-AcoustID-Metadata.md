# Phase 5: AcoustID Metadata Extraction

## ⚠️ NOT IMPLEMENTED - Removed in v3.0 ⚠️

This phase was originally planned to implement AcoustID audio fingerprinting for metadata extraction. However, in version 3.0 of the OBS YouTube Player, the metadata system was simplified to use only:

1. **Google Gemini AI** (Primary) - AI-powered extraction with Google Search grounding
2. **Smart Title Parser** (Fallback) - Handles common YouTube title patterns

## Why Was This Removed?

- **Complexity**: AcoustID required additional dependencies (fpcalc.exe) and API management
- **Reliability**: Network-based fingerprinting could fail for obscure or new content
- **Accuracy**: Google Gemini with search grounding provides superior results
- **Simplicity**: Fewer moving parts means fewer potential failure points

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

Failed Gemini extractions are automatically retried on the next startup, ensuring maximum accuracy over time.

## Original Phase Description

*For historical reference only - this functionality is not implemented in the current version.*

The original plan included:
- Audio fingerprinting using Chromaprint (fpcalc)
- AcoustID API integration
- MusicBrainz database lookups
- Fallback to other sources on failure

---

*See Phase-13-Gemini-Metadata.md for the current metadata implementation.*