from __future__ import annotations

import os

# Automated tests intentionally exercise the deterministic generator unless a test
# injects a mocked OpenAI client. Real application runs default to GPT generation.
os.environ.setdefault("MOCK_AI", "true")
