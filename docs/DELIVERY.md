# Branch and commit summary

Original main remains at f0fe4e6; no history was reset, rewritten, or published.
Integration branch: `rebuild/integration`. Features were committed and fast-forward
integrated without squashing. Each dependent branch starts from the latest integration.

| Branch | Commit | Scope | Passing checks at integration |
|---|---|---|---|
| qa/core-and-config | eb2c976 | Preserve original local fixes, record inspection/plan, stop tracking private runtime files | Inspection and local-copy preservation |
| qa/core-and-config | e302d37 | UTF-8 dependencies, config, validated domain types | 2 tests |
| qa/gmail-client | 9cb262e | Explicit auth, MIME parsing, bounded threads, addressing, one-attempt approved sends | 8 tests |
| qa/persistent-memory | f7faaa0 | Lazy Chroma, stable sent IDs, import/retrieve/inspect/delete/reset | 11 tests |
| qa/generation-and-evaluation | df05194 | Structured summary/draft/evaluation, feedback loop, review CLI and mock demo | 16 tests |
| qa/benchmarks | 0e0ca4a | Isolated synthetic comparison runner and labelled mock results | 18 tests; 18 mock trials |
| qa/gmail-extension | 516bf45 | MV3 popup, protected loopback API, actual browser smoke harness | 22 tests; Chrome popup smoke |
| qa/final-validation | see branch log | Read-only default OAuth, sent confirmation commands, first-run token fix, expanded validation and setup docs | 29 tests; full Chrome smoke |

Author name is sysoutprntlne, configured only in this repository, with the existing
repository commit email. The original two local edits were saved as a patch at
/tmp/gmail-assistant-original-edits.patch and committed in the preserved baseline.
The main entry point now uses documented package-relative module execution.

The retained remote feature/core-foundation branch was inspected, not represented
as a recovered lost branch. Git fsck reported no unreachable recovery objects.

The final audit restored runtime copies removed by earlier Git transitions from the
original tracked snapshot, verifying the token/log/SQLite bytes. All later integration
states already exclude them, so the final feature merge preserves those ignored files.

## Automatic reply dashboard follow-up

- `qa/inbox-triage` — aeceb51: paginated metadata scanning, reply/review/filtered
  queues, thread deduplication/latest-SENT check, reasons and caching.
- `qa/reply-dashboard` — see branch log: local authenticated dashboard, automatic
  refresh, search and pagination, summaries and edited drafts, Gmail handoff,
  synthetic dashboard mode, HTTP and actual Chrome browser validation.

Both feature branches start from integration and preserve the previous commits.
The follow-up expands validation to 36 synthetic tests and the dashboard browser
smoke test; no mailbox access, Gmail writes, deployment or publication is performed.
