"""Descriptive, paired comparisons of completed benchmark trials. No model calls."""

import math
import statistics

MODES = ("baseline", "rag", "rag_feedback")
PAIRS = (("baseline", "rag"), ("baseline", "rag_feedback"), ("rag", "rag_feedback"))
# Direction describes an individual metric, not an overall quality ranking.
METRICS = {
    "intent_preservation_proxy": ("rate", "higher"),
    "relevance_completeness_proxy": ("rate", "higher"),
    "style_fit_proxy": ("rate", "higher"),
    "output_valid": ("rate", "higher"),
    "unsupported_claims_per_trial": ("flags/trial", "lower"),
    "failure_rate": ("rate", "lower"),
    "error_rate": ("rate", "lower"),
    "latency_seconds": ("seconds", "lower"),
    "trial_wall_seconds": ("seconds", "lower"),
    "model_calls": ("calls/trial", "lower"),
    "revisions": ("revisions/trial", "lower"),
    "prompt_tokens": ("tokens/trial", "lower"),
    "output_tokens": ("tokens/trial", "lower"),
}


def metric_value(row, name):
    checks = row.get("deterministic") or {}
    if name == "unsupported_claims_per_trial":
        flags = checks.get("unsupported_claims_proxy")
        value = len(flags) if flags is not None else None
    elif name == "failure_rate":
        value = row.get("failed")
    elif name == "error_rate":
        value = row.get("error") is not None
    elif name == "trial_wall_seconds":
        value = row.get(name)
    elif name in checks:
        value = checks[name]
    else:
        value = (row.get("metrics") or {}).get(name)
    return (
        float(value)
        if isinstance(value, (int, float)) and math.isfinite(value)
        else None
    )


def mean(values):
    return statistics.mean(values) if values else None


def build_comparison(data):
    """Match the same case/repetition across modes; exclude missing metric pairs."""
    if data.get("status") != "completed":
        raise ValueError("Comparison requires a completed benchmark run")
    rows = {mode: {} for mode in MODES}
    for row in data["results"]:
        mode = row["mode"]
        if mode not in rows:
            raise ValueError("Unknown benchmark configuration")
        key = (row["case"], row["repeat"])
        if key in rows[mode]:
            raise ValueError("Duplicate case/repetition within a configuration")
        rows[mode][key] = row

    configurations = {}
    for mode, trials in rows.items():
        metrics = {}
        for name, (unit, preferred) in METRICS.items():
            values = [metric_value(row, name) for row in trials.values()]
            available = [value for value in values if value is not None]
            metrics[name] = {
                "mean": mean(available),
                "observations": len(available),
                "missing": len(values) - len(available),
                "unit": unit,
                "preferred_direction": preferred,
            }
        configurations[mode] = {"trials": len(trials), "metrics": metrics}

    comparisons = []
    for reference, candidate in PAIRS:
        shared = rows[reference].keys() & rows[candidate].keys()
        metrics = {}
        for name, (unit, preferred) in METRICS.items():
            matched = []
            for key in sorted(shared):
                before = metric_value(rows[reference][key], name)
                after = metric_value(rows[candidate][key], name)
                if before is not None and after is not None:
                    matched.append((before, after))
            before = mean([values[0] for values in matched])
            after = mean([values[1] for values in matched])
            delta = after - before if matched else None
            trend = (
                "unavailable"
                if delta is None
                else "unchanged" if delta == 0 else "higher" if delta > 0 else "lower"
            )
            metrics[name] = {
                "reference_mean": before,
                "candidate_mean": after,
                "delta": delta,
                "percent_change": (
                    delta / abs(before) * 100 if before not in (None, 0) else None
                ),
                "percentage_point_change": (
                    delta * 100 if unit == "rate" and delta is not None else None
                ),
                "paired_observations": len(matched),
                "missing_metric_pairs": len(shared) - len(matched),
                "unit": unit,
                "preferred_direction": preferred,
                "observed_change": trend,
            }
        comparisons.append(
            {
                "reference": reference,
                "candidate": candidate,
                "matched_trials": len(shared),
                "unmatched_reference_trials": len(rows[reference].keys() - shared),
                "unmatched_candidate_trials": len(rows[candidate].keys() - shared),
                "metrics": metrics,
            }
        )

    return {
        "schema_version": 1,
        "run_id": data["run_id"],
        "run_type": data["run_type"],
        "status": "completed",
        "timestamp_utc": data["timestamp_utc"],
        "fixture_sha256": data["fixture_sha256"],
        "config": data["config"],
        "repeats": data["repeats"],
        "configurations": configurations,
        "comparisons": comparisons,
        "interpretation": {
            "delta_definition": "candidate minus reference, using matched case/repetition pairs",
            "percent_change_definition": "100 * delta / abs(reference_mean); null for zero or missing reference",
            "statistical_significance": "not_tested",
            "overall_winner": None,
            "quality_measurement": "deterministic proxies, not evaluator approval or human assessment",
            "limitations": [
                "Mock runs verify the harness and cannot establish real model quality.",
                "Lower resource cost does not imply a better reply; assess quality and cost together.",
                "Quality metrics omit unavailable checks; failure/error rates include failed trials.",
                "Paired samples and coverage may differ across metrics; inspect observation counts.",
                "Repeated fixed-seed trials are not independent quality samples.",
            ],
        },
    }
