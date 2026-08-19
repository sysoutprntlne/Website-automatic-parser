## Website-automatic-parser: Generative emails made easy

---

This project is a personal passion project from me that i wanted to use to experiement on ML.
It aims to make answering emails easy with a click of a button

This web application uses ML learning to automatically send emails and track replies 



(SCRAPER) -> (EMAIL) -> INPUT INTO DATABASE FOR MODEL -> OUTPUT MODEL GIVE RESPONSE

Develop database first

Create a simplified version of scraper (on a file or something)

Create a seperate script for looking at emails

Make model and feed it kaggle to learn how to use it

## ISSUES: 8/19

Architecture

No separation between I/O, business logic, and orchestration. main.py is 8 lines that do nothing; the actual control flow is buried inside Llama.py's import statements and a function that recurses into itself. A senior engineer would look at this and be unable to tell you, without running it, what order things execute in.
No dependency injection anywhere. creds, service, collection are grabbed from module scope by side effect. This isn't "not senior-level" — it's actively hostile to testing, mocking, and reasoning about the system.
No interfaces/abstractions between the Gmail layer, the model layer, and the storage layer. Swapping Ollama for OpenAI, or Gmail for Outlook, would require rewriting call sites throughout, not swapping an implementation behind a boundary.

Correctness

There is no evidence any part of the send path has ever executed successfully ("Gmail" typo). At the standard you're asking about, code that has never run its primary function isn't "buggy," it's unfinished by definition — best-of-best engineers don't ship or present code they haven't verified executes.
Parsing an LLM's free-text completion by splitting on ; with hardcoded indices, with zero validation, schema enforcement, or retry-with-correction logic, would not pass review at any company doing LLM work seriously. The standard approach — structured output / function calling / JSON mode with schema validation — exists precisely because this is a known failure mode, and it's not used here.
Unbounded recursion as an error-handling strategy is a correctness bug, not a style nitpick. It will stack-overflow in production under exactly the condition it's meant to handle (bad model output).

Security

Live OAuth secret and refresh token committed to a distributable artifact. At any company, this triggers an incident response, not a code review comment. This alone would fail the code at the "best of the best" bar — that bar doesn't just mean "clever," it means "wouldn't cause an incident."
No secret management (env vars, vault, secret manager) at all — not even a stub for it.

Reliability / observability

Every failure mode resolves to print(). No logging framework, no structured logs, no error codes, no way to know in production what failed and why without reading stdout live.
No retries with backoff on network/API calls (Gmail API, Ollama). Both can transiently fail; nothing here survives that.
No idempotency — if grab_messages_list runs twice, there's no dedup; if give_message_back is retried after a false failure, it could double-send an email to a real person.

Maintainability

Circular imports between Llama.py and eval.py. Best-of-best codebases treat circular imports as a design smell to be refactored immediately, not worked around.
Windows-only path separators hardcoded as string literals. This is a "have you shipped cross-platform code before" tell — professional codebases use pathlib reflexively.
requirements.txt is an unaudited environment dump, not a dependency manifest. No pinned lockfile discipline (poetry.lock / pip-compile), no separation of dev vs. runtime deps.
Zero tests. Zero CI. Zero type hints. Zero docstrings beyond a couple of leftover comments. At a "best of the best" bar, untested code with no static typing on an LLM pipeline that parses untrusted free text is considered actively risky, not just "could be improved."

Where it'd stand in a real review
At a company with a strong engineering culture, this wouldn't get "changes requested" — it would get blocked outright at the PR stage on the credentials leak alone, before a reviewer even reads the logic. Setting that aside and judging the logic in isolation: it reads as a weekend prototype validating a concept, which is a completely legitimate and useful thing to write — but it is not close to code that's been hardened, tested, or reviewed to production standard, and measuring it against that standard rather than "for a first project" is genuinely a different exercise than what we did yesterday.

The honest gap: the idea would survive a design review. The code would not survive a code review at a serious engineering org, on security grounds alone, before anyone even gets to style.


