# Rebuild plan and inspection

Existing Git history is present; main starts at f0fe4e6. Remote branches include
Structure_Improvements and feature/core-foundation. Reflog records this clone;
no lost branch recovery is claimed. Original local changes fixed the main import
case and added whitespace in pipeline; their patch is preserved outside Git at
/tmp/gmail-assistant-original-edits.patch. Keep the corrected lowercase entry point.
No AGENTS.md or tests were found. Requirements were UTF-16; dependencies are installed
in .venv (Python 3.14). Existing structured generation and prompt perspective rules
are reusable. Gmail snippets, random memory IDs, import-time Chroma creation,
pre-send memory writes, retrying sends, and the unused evaluator need replacement.

Tracked token, logs, database and bytecode will be removed from the index only.
Local copies remain. History still contains sensitive material: revoke the exposed
OAuth token, and arrange any history cleanup separately. Never print secret values.

## Branches and commit boundaries

Integration: rebuild/integration. Each branch starts from its latest state,
passes focused unittest checks, commits, and merges without squashing.

1. qa/core-and-config: sanitize tracking, typed configuration/domain objects,
   valid dependencies and documented module entry point; import/validation checks.
2. qa/gmail-client: explicit OAuth, deterministic MIME/header parsing, bounded
   threads, addressing, single-attempt approved send; synthetic Gmail tests.
3. qa/persistent-memory: lazy Chroma, local deterministic embeddings, stable IDs,
   explicit sent import and inspect/delete/reset; persistent temporary DB tests.
4. qa/generation-and-evaluation: bounded structured summaries/drafts/evaluation,
   feedback revisions, CLI demo and review; injected fake model workflow tests.
5. qa/benchmarks: held-out synthetic cases and three controlled configurations,
   independent checks, JSON/report output; mock harness verification. Real model
   results only if a local Ollama instance is available.
6. qa/gmail-extension: loopback authenticated backend, exact origin/Host checks,
   MV3 popup and composer insertion, explicit API verification of sent memory;
   HTTP and extension syntax checks, local smoke test.

## Architecture and acceptance

Retain src/Gmail, Model/Llama.py, Model/memry/Vector_lib.py, prompt and eval_model.
Add config/domain types, orchestrate with pipeline, expose CLI through
python -m src.main, and use a small stdlib HTTP interface. Imports must have no
network/auth/database side effects. User delivery stays in Gmail's normal UI;
backend has no browser-facing send endpoint. Draft insertion never writes memory.
All automated checks use synthetic content and mocked Gmail/model services.
Inspect actual Chroma persistence without touching the existing private database.
Keep attempt metadata content-free by default. Document limitations and separate
mock verification from live Gmail/Ollama/browser validation.
