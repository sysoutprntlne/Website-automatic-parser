"""Deterministic synthetic services: demonstration only, not a real LLM."""
from src.domain import Email

DEMO_EMAIL = Email(id='synthetic-incoming', thread_id='demo-thread',
    sender='organizer@example.test', to=['me@example.test'], subject='Tuesday meeting',
    body='Are you able to attend Tuesday at 3?', message_id='<demo@example.test>')


class DemoModel:
    def __init__(self):
        self.calls = 0

    def metrics(self):
        return {'model_calls': self.calls, 'prompt_tokens': None, 'output_tokens': None}

    def structured(self, task, instructions, data, schema, evaluator=False):
        self.calls += 1
        if task == 'summarize':
            result = dict(overview='The sender asks about attending a meeting.',
                          requests=['Confirm whether you can attend Tuesday at 3.'], deadlines=[])
        elif task == 'evaluate':
            result = dict(passed=True, issues=[])
        elif task == 'draft':
            result = dict(body='Yes, I can attend Tuesday at 3. Thanks for checking!', missing_information=[])
        else:
            raise ValueError('Unknown demo task')
        return schema.model_validate(result)
