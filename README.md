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

=============================================================================

1. Rotate the leaked Gmail credentials (do this before anything else, unrelated to code)

Revoke access at https://myaccount.google.com/permissions
Regenerate the client secret in Google Cloud Console
Update .gitignore to match the actual current path (lib/chromaDB/gmailAPI/credentials.json and token.json, or wherever they end up after #2)

2. Create Gmail/client.py — shared auth, single source of truth

Extract the duplicated auth block out of reader.py and sender.py
Expose one get_service(scopes) function; both files import and call it
Move creds/token files out of lib/chromaDB/ into their own config/ or secrets/ folder — not nested inside the ChromaDB directory

3. Fix path handling — use pathlib, not hardcoded strings

Every hardcoded path (email_snatch/token.json, Model\memoryDB\pirate.json, etc.) is currently wrong, since files have moved, and backslash-only paths break on non-Windows
Use pathlib.Path(**file**).parent / "..." style relative resolution so paths survive future reorganization

4. Fix give_message_back's "Gmail" → "gmail" typo

This is why sending has likely never worked at all

5. Fix the eager-default-argument bug in get_response_output

prompt=get_prompt(...) as a default is computed once at import time, not per-call — this silently disconnects your retrieved context from what actually gets sent to the model
Pass the prompt explicitly on every call instead

6. Fix prompt_splitting

repr(response_output).split is missing () — currently assigns the method, not a list
Consider replacing semicolon-splitting entirely with structured output (Pydantic model + JSON), per the instructor library example — this removes an entire category of fragility at once

7. Remove unbounded recursion — replace with a bounded retry loop

personality_taker calling itself inside except IndexError has no base case
Move retry logic into pipeline.py as a for attempt in range(max_retries): loop instead

8. Break the circular import between Llama.py and eval.py

Move the evaluator's prompt into prompt/prompting_model.py (or a new prompt/evaluation.py) — eval.py shouldn't need to import Llama.py at all once its prompt lives elsewhere

9. Remove module-level side effects

No API calls, DB inits, or function calls should run just from importing a file (grab_messages_list() at the bottom of files, client = chromadb.PersistentClient(...) at module scope)
Wrap everything actionable inside functions, called explicitly from pipeline.py / main.py

10. Fill in pipeline.py

This is the one file that ties every subsystem together — writing it will also reveal whether your current folder boundaries actually compose cleanly

11. Clean up requirements.txt

Trim to actual runtime deps (google-api-python-client, google-auth-oauthlib, ollama, chromadb, etc.) — not a full environment dump

12. Fix broad exception handling

Replace except HttpError as e: print(...) with handling that actually distinguishes recoverable vs. fatal errors, and never swallow an exception silently with no signal to the caller
