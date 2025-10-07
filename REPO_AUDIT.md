# Repository Audit

## Local Checks
- `pytest` (pass): All 4 tests succeed locally.

## Noted Issues
- `chatbot.parse_args` help text for `--model` breaks the example name "qwen2.5:7b-instruct" across a newline, which can confuse CLI help output.
- No linting or type-checking configuration is present; adding tools like `ruff` and `mypy` would help catch issues early.

## External Pull Request Review
Attempted to fetch PR [#1](https://github.com/ErinConradMountain/qwen-chatbot/pull/1) but the environment cannot reach GitHub (HTTP 403 via CONNECT tunnel), so code review could not be completed here.
