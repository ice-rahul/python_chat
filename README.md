# Prompt Verification Backend

FastAPI service that powers [Verification Lab](https://github.com/ice-rahul/simple_eval_ui) — generates golden test datasets from a task description and runs LLM-as-judge evaluations against a prompt, using the caller's own Claude API key.

## Endpoints

**`POST /chat`**
Rate-limited (5/min), streams a Claude response back as plain text — a small standalone chat endpoint, separate from the eval flow.

**`POST /generate-testcases`**
Takes a task description, optional extra constraints, and a target case count. Generates a set of unique test scenarios, then produces a full test case (`prompt_inputs` + `solution_criteria`) for each one — concurrently, via a thread pool, not sequentially.

**`POST /evaluate`**
Takes a prompt template (`{{variable}}` placeholders), a JSON array of test cases, and optional additional acceptance criteria. Fills the template per test case, runs it against Claude, grades each output with an LLM-as-judge call (score out of 10, strengths/weaknesses, reasoning), and returns a fully rendered HTML report.

All three endpoints (except the health check) require an `X-API-KEY` header — no key is ever stored server-side; it's used for that request's Anthropic calls and discarded.

## Design notes

- **`fill_template`** (a static method on `PromptEvaluator`) replaces `{{variable}}` placeholders in a *user-authored* prompt. This is deliberately separate from `render()`, an older method used only for the evaluator's own internal meta-prompts, which uses single-brace `{var}` substitution with `{{ }}` as an *escape* — a different, incompatible convention. Reusing `render()` for user prompts would silently do the wrong thing.
- **Defensive dataset parsing.** `run_evaluation` treats the incoming test case JSON as untrusted client input: malformed JSON, wrong shape (not an array), an empty array, or a test case missing required fields all raise a `ValueError` with a specific, actionable message, caught in `main.py` and returned as `400` — separate from genuine server errors (`500`).
- **Concurrent test case generation** via `ThreadPoolExecutor` and a future-to-input mapping, so N test cases generate in parallel rather than one at a time.
- **Grading** uses a dedicated `grade_output` call per test case, then `generate_prompt_evaluation_report` assembles a self-contained HTML report (inline styles, no external assets) — safe to render in a sandboxed iframe or save standalone.

## Local setup

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

The frontend expects this running at the URL set in its `NEXT_PUBLIC_SERVICE_URL` env var (defaults to matching `http://localhost:8000` in local dev).

## Deployment

Configured for [Render](https://render.com) via `render.yaml` — Docker-free, `pip install` + `uvicorn` start command, free tier.

## Notes on scope

- `/generate-testcases` and `/evaluate` are currently request/response, not streamed. An SSE variant — multiplexing N concurrent per-case Claude streams over one connection via a thread-safe queue, so test cases populate the UI as they finish rather than all at once — is designed and unit-tested in isolation, but not yet wired into these endpoints.
- No CI-gating yet (an exit-code/threshold check that fails a build on regression) — the eval loop currently runs on demand from the UI only.

---

<details>
<summary>Build notes (original project setup log)</summary>

- Step 1 — Created boilerplate files: `main.py`, `requirements.txt`, `.env`, `.gitignore`, `README.md`
- Step 2 — Created a virtual environment: `python3 -m venv venv` · `source venv/bin/activate`
- Step 3 — Installed dependencies: `pip install fastapi uvicorn anthropic python-dotenv`
- Step 4 — Registered dependencies: `pip freeze > requirements.txt`
- Step 5 — Ran locally: `uvicorn main:app --reload`

</details>
