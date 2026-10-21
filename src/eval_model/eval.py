from src.domain import Evaluation
from src.prompt.prompting_model import EVALUATION_RULES


def eval_model(model, context, draft):
    result = model.structured(
        "evaluate",
        EVALUATION_RULES,
        dict(context, draft=draft.model_dump()),
        Evaluation,
        evaluator=True,
    )
    issues = list(result.issues)
    if not draft.body.strip():
        issues.append("Write a nonempty reply after resolving missing information.")
    issues.extend("Supply missing information: " + q for q in draft.missing_information)
    if issues or not result.passed:
        return Evaluation(
            passed=False,
            issues=issues
            or ["Evaluator rejected draft; revise for fidelity and completeness."],
        )
    return result
