# Validation record

Validated locally on October 18, 2026. All automated email content is synthetic.

- 29 Python unittest tests pass with loopback socket permission.
- Tests cover MIME/plain/HTML/multipart parsing; addresses, reply-all and threading;
  empty inboxes; API failures; bounded prior context; exact approval and single send
  attempt; explicit/malformed/expired authentication; Chroma persistence, import,
  deduplication, relevance, exclusion of current thread and unsent examples; deletion
  and reset; structured output validation; first-run token counters; evaluator
  feedback reaching revisions; maximum attempts; missing information; untrusted data
  placement in prompts; benchmark isolation/leakage checks; Host/origin/auth/body-size
  and schema validation; no browser send endpoint; complete mocked workflow with
  actual temporary persistent memory and user-edited confirmed sent text.
- Import checks deny service-library imports and detect filesystem creation in a
  fresh directory: application imports perform no service IO.
- `python -m src.main demo` runs without Gmail credentials, memory, or Ollama.
- `python -m compileall -q src scripts tests` and `node --check extension/popup.js` pass.
- `python -m pip check` reports no broken requirements in the supplied environment.
- Actual headless Chrome 155 MV3 popup smoke test passes against a temporary HTTP
  backend with mocked Gmail/model services. Pairing storage, HTTP summary/generation,
  evaluator display, and rejection are verified. No Gmail page/account is opened.
- Benchmark harness completed 18 mock trials (six cases × three configurations),
  with configuration, package versions, fixture hash and actual results saved in
  docs/benchmarks/mock. Fixed mock failures are expected and are not real-model results.

The sandbox prevents local sockets. HTTP tests were rerun with elevated process
permission and passed; the failure was environmental. Chrome's old load-extension
flag also failed; the smoke test uses its supported pipe-based Extensions.loadUnpacked
interface instead. Neither failure is counted as a live Gmail/model verification.

The final local-copy audit caught Git branch transitions deleting formerly tracked,
ignored runtime files. Missing copies were restored without overwriting existing
files from the original tracked snapshot. The token, log and Chroma SQLite file
were verified byte-for-byte against that original snapshot, and remain untracked.

## Remaining environment-dependent checks

1. Ollama answers at 127.0.0.1:11434 outside the sandbox, but `/api/tags` returned no
   installed models. Install the configured model, then run synthetic real-model
   benchmarks and inspect real summary, generation, structured-output support, and
   evaluator behavior. No real model-quality improvement is claimed.
2. Gmail OAuth, token refresh against Google, live mailbox MIME/thread reads, actual
   delivery, and SENT confirmation require a real account. None was accessed in QA.
3. Load the extension manually and test Gmail's current DOM/layout with a real
   account: choose the right expanded message, verify addresses/subject, open an
   inline reply, insert edited text, reject/regenerate, and confirm via Sent API ID.
   Selector/input-event compatibility is not established by the popup smoke test.
4. Evaluator approval and prompt defenses are heuristics. Automated injection checks
   validate data separation and synthetic guard behavior, not immunity of an actual
   LLM. Human review and independent benchmark assessment remain necessary.
5. Memory is bounded lexical RAG, not semantic model training. Historical quotations
   and signatures may need manual curation. Very large emails are fetched as MIME
   before body truncation; token limits are approximate character budgets.
6. No automatic sent detection, background mailbox polling, attachments, pop-out
   reply support, browser reply-all selection, or multiuser deployment is implemented.
   Explicit sent-ID confirmation/import is the supported memory update path.
7. Tracked historical secrets remain in earlier Git commits. Local runtime copies
   were retained; revoke the exposed token and treat original history as sensitive.

## Accurate résumé wording

Built a local Gmail reply assistant in Python using Ollama structured outputs and
ChromaDB persistent-memory RAG, with deterministic MIME parsing, bounded evaluator
feedback revisions, human-reviewed delivery, and a Manifest V3 Gmail extension backed
by an authenticated loopback API. Added 29 automated synthetic tests, a Chrome popup
integration smoke test, and a reproducible three-configuration benchmark harness.
Live Gmail integration and real-model quality benchmarking remain pending.
