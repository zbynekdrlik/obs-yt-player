# Contributing to OBS YouTube Player

Thank you for your interest in contributing to OBS YouTube Player! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)

## Development Setup

### Prerequisites

- Python 3.9 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/zbynekdrlik/obs-yt-player.git
   cd obs-yt-player
   ```

2. **Install uv (if not already installed):**
   ```bash
   pip install uv
   ```

3. **Install dependencies:**
   ```bash
   uv sync --dev
   ```

4. **Verify installation:**
   ```bash
   uv run pytest tests/ -v
   ```

### IDE Setup

For VS Code, recommended extensions:
- Python (Microsoft)
- Ruff (Astral)
- Mypy Type Checker

## Code Standards

### Python Version

- Target Python 3.9+ for compatibility
- Use type hints where practical
- Follow PEP 8 style guidelines

### Linting and Formatting

We use [Ruff](https://github.com/astral-sh/ruff) for both linting and formatting:

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check . --fix

# Format code
uv run ruff format .
```

### Type Checking

We use [Mypy](https://mypy.readthedocs.io/) for static type checking:

```bash
uv run mypy yt-player-main/ytplay_modules
```

### Security Scanning

We use [Bandit](https://bandit.readthedocs.io/) for security analysis:

```bash
uv run bandit -c pyproject.toml -r yt-player-main/ytplay_modules -ll
```

### Pre-commit Hooks

Install pre-commit hooks to automatically check code before commits:

```bash
uv run pre-commit install
```

This runs Ruff, Mypy, and Bandit on every commit.

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=yt-player-main/ytplay_modules --cov-report=term-missing

# Run specific test file
uv run pytest tests/unit/test_state.py -v

# Run tests matching a pattern
uv run pytest tests/ -k "test_play_history" -v
```

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── mocks/                   # Mock implementations
│   └── obspython/           # Mock OBS Python API
├── unit/                    # Unit tests (fast, isolated)
├── integration/             # Integration tests (mocked externals)
└── obs_integration/         # Tests requiring mock OBS
```

### Coverage Requirements

- **Project coverage**: Minimum 70%
- **Patch coverage**: Minimum 80% for new code
- Coverage is enforced by CI and Codecov

### Writing Tests

1. **Unit tests** go in `tests/unit/`
2. **Integration tests** go in `tests/integration/`
3. **OBS-related tests** go in `tests/obs_integration/`

Example test:

```python
import pytest
from ytplay_modules.video_selector import select_next_video

class TestVideoSelector:
    def test_returns_none_when_no_videos(self, reset_state_module):
        """Should return None when no videos are cached."""
        result = select_next_video()
        assert result is None

    def test_selects_random_video(self, reset_state_module):
        """Should select a random video from cache."""
        # Setup
        from ytplay_modules import state
        state.add_cached_video("video1", {"path": "/test.mp4", "song": "Test", "artist": "Artist"})

        # Execute
        result = select_next_video()

        # Verify
        assert result == "video1"
```

## Pull Request Process

### Before Submitting

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following code standards

3. **Run all checks locally:**
   ```bash
   uv run ruff check .
   uv run ruff format --check .
   uv run mypy yt-player-main/ytplay_modules
   uv run pytest tests/ -v
   ```

4. **Commit with a clear message:**
   ```bash
   git commit -m "feat: Add new feature description"
   ```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

### Submitting a PR

1. Push your branch to GitHub
2. Create a Pull Request against `main`
3. Fill in the PR template
4. Wait for CI checks to pass
5. Address any review feedback

### CI Requirements

All PRs must pass:
- ✅ Ruff linting
- ✅ Ruff formatting
- ✅ Mypy type checking
- ✅ Bandit security scan
- ✅ Tests on Python 3.9-3.13
- ✅ Tests on Ubuntu and Windows
- ✅ Coverage thresholds

## Project Structure

```
obs-yt-player/
├── yt-player-main/              # Main script template
│   ├── ytplay.py                # Entry point (loaded by OBS)
│   ├── ytplay_modules/          # All modules
│   │   ├── config.py            # Configuration
│   │   ├── state.py             # Thread-safe state management
│   │   ├── playback_controller.py  # Main playback loop
│   │   ├── download.py          # yt-dlp integration
│   │   ├── normalize.py         # FFmpeg audio processing
│   │   └── ...                  # Other modules
│   └── cache/                   # Video cache directory
├── tests/                       # Test suite
├── docs/                        # Documentation
├── .github/                     # GitHub Actions workflows
├── pyproject.toml               # Project configuration
└── CLAUDE.md                    # AI assistant instructions
```

### Key Modules

| Module | Responsibility |
|--------|----------------|
| `playback_controller.py` | Main 1-second timer loop, state machine |
| `state.py` | Thread-safe global state with accessors |
| `state_handlers.py` | Media state handling (playing, ended, etc.) |
| `download.py` | yt-dlp video downloading |
| `normalize.py` | FFmpeg loudness normalization |
| `gemini_metadata.py` | AI-powered metadata extraction |
| `video_selector.py` | Random selection with no-repeat logic |
| `play_history.py` | Persistent play tracking |

## Getting Help

- Check existing [Issues](https://github.com/zbynekdrlik/obs-yt-player/issues)
- Read the [CLAUDE.md](CLAUDE.md) for architecture details
- Open a new issue for questions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
