"""Summary -> retrieve -> draft -> evaluate/revise -> human review.

No draft is stored. Memory writes require a separately fetched Gmail SENT message.
"""

import re
import time
from dataclasses import dataclass, field
from src.config import Config
from src.domain import Draft, Summary
from src.Model.Llama import ModelOutputError
from src.prompt.prompting_model import SUMMARY_RULES, DRAFT_RULES, context_data
from src.eval_model.eval import eval_model


@dataclass
class Result:
    summary: Summary
    draft: Draft | None
    passed: bool
    issues: list[str]
    attempts: list[dict] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)

    def public(self):
        return {
            "summary": self.summary.model_dump(),
            "draft": self.draft.model_dump() if self.draft else None,
            "evaluation_passed": self.passed,
            "requires_review": True,
            "issues": self.issues,
            "attempts": self.attempts,
            "metrics": self.metrics,
        }


def required_information(email, intent):
    # Conservative deterministic guard for the documented open-availability case.
    open_times = re.search(
        r"(what|which)\s+(times?|days?).{0,100}(available|free)|"
        r"(when are you|your availability)",
        email.body,
        re.I | re.S,
    )
    generic_yes = re.fullmatch(
        r"(yeah|yes|sure|ok|okay|yep|sounds good)[\s,.!]*(sure)?[.!]?",
        intent.strip(),
        re.I,
    )
    if open_times and generic_yes:
        return ["What times are you available? Please provide your availability."]
    return []


class Assistant:
    def __init__(self, model, memory=None, config=None):
        self.model, self.memory = model, memory
        self.config = config or Config()

    def summarize(self, email, thread=()):
        return self.model.structured(
            "summarize",
            SUMMARY_RULES,
            context_data(*self._bounded(email, thread), [], ""),
            Summary,
        )
        
# For incoming emails to fit character limit. Current email is given priority
    def _bounded(self, email, thread):
        budget = self.config.context_chars
        email = email.model_copy(update={"body": email.body[:budget]})
        budget -= len(email.body)
        previous = []
        for item in reversed(list(thread)[-self.config.thread_limit :]):
            if budget <= 0:
                break
            item = item.model_copy(update={"body": item.body[:budget]})
            previous.insert(0, item)
            budget -= len(item.body)
        return email, previous

    def run(self, email, intent, thread=(), retrieval=True, feedback=True):
        if not intent.strip() or len(intent) > 4000:
            raise ValueError("Reply intent must be 1..4000 characters")
        started = time.perf_counter()
        before = self.model.metrics()
        email, thread = self._bounded(email, thread)
        summary = self.summarize(email, thread)
        examples = (
            self.memory.retrieve(
                email.subject + "\n" + email.body + "\n" + intent,
                exclude_thread=email.thread_id,
                exclude_ids=[email.id],
            )
            if retrieval and self.memory
            else []
        )
        context = context_data(email, thread, examples, intent)
        issues, history, previous, draft, passed = [], [], None, None, False
        missing = required_information(email, intent)
        for attempt in range(1, (self.config.attempts if feedback else 1) + 1):
            try:
                candidate = self.model.structured(
                    "draft",
                    DRAFT_RULES,
                    dict(
                        context,
                        summary=summary.model_dump(),
                        previous_draft=previous,
                        feedback=issues,
                        required_information=missing,
                    ),
                    Draft,
                )
                if missing:
                    candidate = Draft(body="", missing_information=missing)
                draft = candidate
                if feedback:
                    evaluation = eval_model(self.model, context, draft)
                    passed, issues = evaluation.passed, evaluation.issues
                else:
                    issues = [
                        "Draft has not been evaluated."
                    ] + draft.missing_information
                if missing or draft.missing_information or not draft.body:
                    passed = False
                    issues = list(dict.fromkeys(issues + draft.missing_information))
            except (ModelOutputError, ValueError, TypeError):
                passed = False
                issues = ["Return valid JSON matching the required output schema."]
            history.append(
                {"attempt": attempt, "passed": passed, "issue_count": len(issues)}
            )
            previous = draft.model_dump() if draft else None
            if passed or missing or (draft and draft.missing_information):
                break
        after = self.model.metrics()
        metrics = {
            key: after[key] - (before[key] or 0) if after[key] is not None else None
            for key in after
        }
        metrics.update(
            latency_seconds=time.perf_counter() - started,
            revisions=max(0, len(history) - 1),
            retrieved_examples=len(examples),
        )
        return Result(summary, draft, passed, issues, history, metrics)


def remember_confirmed(gmail, memory, sent_message_id):
    email = gmail.confirm_sent(sent_message_id)
    memory.remember_sent(email)
    return email

#Initialize Start

def start():
    from src.main import main

    main()
