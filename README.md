# Personalized Gmail reply assistant

Draft replies using a local Ollama model, Gmail API context, and confirmed sent
messages retrieved from persistent Chroma memory. Personalization is RAG: model
weights are unchanged. Every draft needs human review. Evaluator approval is a
heuristic and never triggers sending.

The backend, CLI, and minimal Gmail extension are implemented. Automated QA uses
synthetic messages and mocked Gmail/model services; live Gmail behavior still
needs manual validation. See [validation and limitations](docs/VALIDATION.md),
[branch history](docs/DELIVERY.md), and [inspection plan](docs/REBUILD_PLAN.md).

## Setup and credential-free demo

Python 3.11+ is required; development checks ran with Python 3.14.4 on Linux.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m src.main demo
.venv/bin/python -m unittest discover -s tests -v
node --check extension/popup.js
```

The demo uses fixed synthetic model output, no mailbox, no database, and no model
server. Tests use temporary databases; the HTTP integration test needs permission
to open a loopback socket. Run commands from the repository root using `-m` so
Linux imports resolve consistently. Dependencies are UTF-8 and compatible ranges;
the benchmark records installed versions, settings, fixture hash, and seed.

Install and run [Ollama](https://docs.ollama.com/quickstart), then install a local
model before using real drafting:

```bash
ollama pull llama3.2
ollama serve
```

If Ollama is already running, skip `ollama serve`. The inspected local service had
no installed models, so real generation and benchmarking have not been verified.

## Configuration

[.env.example](.env.example) lists supported `REPLY_*` environment variables.
Export values in your shell; the application does not automatically load `.env`.
Defaults: generation/evaluation model `llama3.2`, host `127.0.0.1:11434`, memory
`private/memory`, four style examples, 6000 style characters, 16000 conversation
characters, eight previous thread messages, three generation attempts, seed 42,
and temperature 0.2. Ollama receives a 16384-token context setting and a 2048-token
output limit. Character budgets approximate tokens; unusual text/model limits
may still require smaller budgets. These budgets limit bodies, not raw MIME fetch
size. Optional `REPLY_EVALUATOR_MODEL` selects a separate evaluator model.

Imports perform no authentication, network calls, model calls, or database creation.
Chroma opens lazily on explicit memory operations. Its versioned `sent_examples_v1`
collection uses local deterministic feature-hashed word embeddings, with no embedding
model download. Retrieval is lexical and approximate. The old `chromadata` directory
is preserved locally but deliberately not migrated into the new memory.

## Gmail authorization and sent-message import

1. Enable the Gmail API in your Google Cloud project, configure the OAuth consent
   screen/test user, and create a Desktop OAuth client using the official
   [Python quickstart](https://developers.google.com/workspace/gmail/api/quickstart/python).
2. Put its downloaded client file at `lib/cred/credentials.json` (ignored by Git).
3. Authorize explicitly. A token is saved with owner-only permissions.

```bash
.venv/bin/python -m src.main auth
.venv/bin/python -m src.main inbox
.venv/bin/python -m src.main import-sent --limit 100 --query 'after:2025/01/01'
```

The default OAuth scope is Gmail read-only. It supports extension reads and Sent
confirmation. Import is explicit, bounded, paginated, and deduplicated by Gmail
message ID. `--query` accepts Gmail search syntax. Reimport upserts messages.
Stored metadata includes message ID, thread ID, internal timestamp, subject,
body digest, and confirmed sent status. Current thread examples are excluded from
style retrieval, and conversation context is kept separate. A truncated message
excerpt is stored, not an unlimited archive. Quoted text/signatures may remain in
historical bodies; curate imported examples for better style quality.

```bash
.venv/bin/python -m src.main memory inspect
.venv/bin/python -m src.main memory inspect --show-content
.venv/bin/python -m src.main memory delete --id GMAIL_MESSAGE_ID
.venv/bin/python -m src.main memory reset --confirm-reset
```

Inspect hides subjects and bodies by default. Delete targets one source ID. Reset
only removes this application's versioned collection, not other Chroma collections.
Keep memory in a private directory; treat its contents as private email data.

## Gmail extension

1. Open `chrome://extensions`, enable Developer mode, choose **Load unpacked**,
   and select this repository's `extension` directory. See Chrome's
   [development basics](https://developer.chrome.com/docs/extensions/get-started/tutorial/hello-world).
2. Copy its extension ID and configure exactly that origin:

```bash
export REPLY_EXTENSION_ORIGIN=chrome-extension://YOUR_32_CHARACTER_EXTENSION_ID
.venv/bin/python -m src.main serve
```

3. Open the extension popup and pair using the random token in
   `private/backend-token`. Read the file locally; do not commit or share it.
   Pairing is stored only in Chrome session storage for trusted extension contexts.
   OAuth credentials never go into the extension. Restarting Chrome requires pairing
   again. Deleting the backend token file while stopped causes a new token on restart.
4. Open a Gmail conversation, click the extension, find the visible messages,
   choose the incoming message and summarize it. Check sender/recipient/subject.
   If Gmail's DOM does not expose its legacy API ID, use an ID from
   `python -m src.main inbox` in the fallback field. RFC `Message-ID` shown in
   Gmail's **Show original** is different from a Gmail API message ID.
5. Enter your intent, generate, inspect evaluator feedback, and edit the body.
   Regenerate by changing the intent and clicking Generate again. Missing required
   information must be supplied by you. Reject discards the popup draft.
6. Open an empty **inline reply composer** in the selected conversation first.
   Approve the final recipients, subject and body, then insert. The extension
   refuses nonempty, ambiguous, missing, or detached composers. Check the actual
   Gmail recipient chips and body, then use Gmail's normal Send button.
7. After delivery, run `python -m src.main sent` to find the sent API ID. Reopen the
   popup and use **Verify sent message and remember**. The backend independently
   fetches the message, requires Gmail's SENT label and a recently selected thread,
   and stores actual sent content, including your final edits. Composer insertion
   never writes memory. Selection associations expire after 24 hours or backend
   restart; summarize the original incoming message again if needed.

Keep the popup open during model requests. Closing it loses its draft and UI state.
The backend retains only recent selected-thread associations, not rejected drafts.
Automatic send detection is deliberately absent. You can also explicitly store
an already-sent message with `python -m src.main confirm-sent SENT_API_ID`.

The extension uses Manifest V3, user-triggered `activeTab`/`scripting` access, session
storage, and only loopback host access. Chrome match patterns cannot restrict the
host permission to a port; extension CSP restricts requests to port 8765. Use that
port unless you also update `extension/popup.js` and manifest CSP. There are no
remote scripts, page message bridge, Gmail cookies, or OAuth secrets in browser code.
The backend binds only `127.0.0.1`, validates exact Host and configured browser
Origin, requires a random bearer token, validates JSON fields and sizes, disables
content logging, and has no send endpoint. Authenticated nonbrowser requests may
omit Origin; any supplied Origin must match. It is a local single-user service,
not a multiuser Internet server. Do not expose it through a proxy/tunnel.

Chrome documents [extension cross-origin requests](https://developer.chrome.com/docs/extensions/develop/concepts/network-requests)
and [isolated content scripts](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts).
Gmail exposes no supported reply-composer DOM API: selectors and input events are
best effort, locale/layout changes may break them, and inline insertion still needs
manual account-backed testing. Separate compose windows and pop-out replies are not
supported. The extension does not change Gmail recipients or subject automatically.

## Optional CLI review and delivery

The extension is the intended interface. The CLI also supports an explicit send
flow if you authorize the additional Gmail send scope:

```bash
.venv/bin/python -m src.main auth --allow-send
.venv/bin/python -m src.main reply INCOMING_API_ID
```

The CLI summarizes, accepts intent, generates/evaluates, and offers edit, regenerate,
reject, or final send review. Sending requires typing `SEND` after displaying the
final recipient, subject and body. Editing does not imply renewed evaluator approval.
The exact reviewed object is fingerprinted; modifications invalidate approval.
Delivery makes one API attempt, with no retry. A timeout may mean the message was
already delivered: inspect Gmail Sent before taking another action. A successful
send followed by failed memory confirmation is reported separately; do not resend.
Use `confirm-sent` or `import-sent` later. CLI reply defaults to the sender/Reply-To,
not reply-all. The underlying addressing function supports explicit reply-all.

MIME is parsed with Python's email library, including charsets, encoded headers,
plain text, HTML-only and multipart alternatives. HTML scripts/styles and attachments
are excluded from body text. Replies carry Gmail threadId, References, In-Reply-To,
and a matching reply subject as required by Google's
[thread guide](https://developers.google.com/workspace/gmail/api/guides/threads).
API read failures propagate; expired credentials produce a reauthorization error.
No background inbox polling or private-data import occurs during QA.

## Benchmarking

```bash
# Mock harness verification only; synthetic fixtures and temporary memory
.venv/bin/python -m src.benchmarks.sample --output benchmark-results/mock
# Real model experiment, once Ollama has an installed model
.venv/bin/python -m src.benchmarks.sample --real --repeats 3 --output benchmark-results/real
# Optional separate model judgment, additional model calls
.venv/bin/python -m src.benchmarks.sample --real --judge --output benchmark-results/judged
```

The runner compares baseline (no retrieval/no feedback), RAG (no feedback), and
RAG plus bounded feedback with shared generation model/settings, inputs, intents,
and summary step. It shuffles mode order reproducibly per repetition. Six held-out
cases cover formality, refusal, missing information, conflicting thread context,
empty memory, and malicious instructions. Held-out targets stay out of retrieval
and generator prompts. Synthetic style examples live separately in
[fixtures](tests/fixtures/benchmark.json).

JSON results and a Markdown comparison report distinguish deterministic phrase/regex
quality proxies, optional independent model judgments, and pending human review.
They record intent, unsupported-claim flags, relevance/completeness, style proxies,
latency, calls, revisions, failures, and token counts when Ollama exposes them.
Evaluator approval is recorded separately and is not the quality metric. Model
judgments are heuristics; proxy success is not evidence of complete factual safety.

[Actual mock results](docs/benchmarks/mock/report.md) cover 18 synthetic trials.
The fixed mock intentionally fails many cases; these results verify harness behavior
and make no claim that RAG/evaluation improves real model quality. Real benchmarking
and human assessment remain pending. No model was downloaded during this rebuild.

## Privacy and verification

A token, vector database, log, and bytecode were tracked in the supplied history.
They are now ignored/untracked on the rebuilt branch and local copies are retained.
**Revoke the historically exposed OAuth token.** Removing tracking does not remove
historical exposure; history cleanup would be a separate operation. Never distribute
the original history, raw workspace, private memory, logs, or credentials. An archive
of this branch's current tracked tree excludes those runtime files.

The application does not log private message bodies by default. Attempt history
contains attempt number, status, and issue count. Replies/feedback are shown in the
local UI for review; synthetic benchmark output deliberately includes generated
text. External runtime logging, OS backups, and local disk security remain under
your control. Prompt isolation and evaluation reduce risk but cannot prove that a
real model will resist every malicious email or avoid unsupported claims.

The real popup can be tested in a fresh Chrome profile with synthetic services:

```bash
.venv/bin/python scripts/browser_smoke.py
```

This needs Google Chrome, local socket/process permission, and an unused port 8765.
It uses Chrome's pipe-based unpacked-extension loader in an isolated temporary profile,
not your browser profile. It verifies popup pairing, real authenticated local HTTP
summary/generation, evaluation display and rejection; it does not open Gmail or
verify live composer selectors. No real mail is sent by automated checks.
