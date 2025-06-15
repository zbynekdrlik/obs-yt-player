# Contributing to OBS YouTube Player

Thank you for your interest in contributing to this project!

## Development Process

This project follows a structured phase-based development approach. Each phase builds upon the previous one:

### Phase Overview

1. **Phase 01**: Scaffolding & Project Skeleton
2. **Phase 02**: Playlist Synchronisation  
3. **Phase 03**: Video Download & Caching
4. **Phase 04**: Audio Normalisation
5. **Phase 05**: Playback Control & Scene Logic
6. **Phase 06**: Metadata Retrieval
7. **Phase 07**: Final Review & Polish

### Getting Started

1. Read through the documentation in the `docs/` directory:
   - Start with `01-overview.md` for project goals
   - Review `02-requirements.md` for functional specifications
   - Understand `03-obs_api.md` for OBS constraints
   - Follow `04-guidelines.md` for coding standards

2. Examine the phase documentation in `phases/` directory to understand the step-by-step implementation approach

### Code Standards

- Follow PEP-8 style guidelines
- Keep lines ≤ 120 characters where practical
- Use meaningful function and variable names
- Add comments for complex logic
- Ensure thread safety with proper locking
- All OBS API calls must run on the main thread

### Testing

- Test with OBS Studio on multiple platforms if possible
- Verify thread safety and performance
- Test with various YouTube playlist formats
- Check error handling and edge cases

### Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Make your changes following the coding standards
4. Test thoroughly
5. Submit a pull request with a clear description

### Issues

When reporting issues, please include:
- OBS Studio version
- Operating system
- Python version
- Error messages or logs
- Steps to reproduce

## Questions?

Feel free to open an issue for questions about the codebase or development process.