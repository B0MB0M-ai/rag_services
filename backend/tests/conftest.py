from __future__ import annotations

import os
import tempfile

# Automated tests intentionally exercise the deterministic generator unless a test
# injects a mocked OpenAI client. Real application runs default to GPT generation.
os.environ.setdefault("MOCK_AI", "true")
os.environ.setdefault("APP_DATA_DIR", tempfile.mkdtemp(prefix="serviceiq-tests-"))
