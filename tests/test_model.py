from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from src.config import Config
from src.demo import DEMO_EMAIL
from src.domain import Draft
from src.Model.Llama import Model, ModelOutputError
from src.pipeline import Assistant


class ModelTests(unittest.TestCase):
    def test_schema_options_usage_and_malformed_output(self):
        model = Model(Config(model='synthetic',seed=7,temperature=.1))
        model._client = Mock()
        model._client.chat.return_value = SimpleNamespace(
            prompt_eval_count=10,eval_count=5,
            message=SimpleNamespace(content='{"body":"Yes","missing_information":[]}'))
        result = model.structured('draft','rules',{'incoming':'untrusted'},Draft)
        self.assertEqual(result.body,'Yes')
        call = model._client.chat.call_args.kwargs
        self.assertEqual(call['format'],Draft.model_json_schema())
        self.assertEqual(call['options']['seed'],7)
        self.assertEqual(call['model'],'synthetic')
        self.assertEqual(call['messages'][0]['role'],'system')
        self.assertEqual(model.metrics()['prompt_tokens'],10)
        model._client.chat.return_value.message.content = 'not json'
        with self.assertRaises(ModelOutputError):
            model.structured('draft','rules',{},Draft)

    def test_first_run_token_counts(self):
        model = Model()
        model._client = Mock()
        def chat(**kwargs):
            schema = kwargs['format']['title']
            content = {'Summary':'{"overview":"Meeting?","requests":[],"deadlines":[]}',
                       'Draft':'{"body":"Yes","missing_information":[]}',
                       'Evaluation':'{"passed":true,"issues":[]}'}[schema]
            return SimpleNamespace(prompt_eval_count=10,eval_count=5,
                                   message=SimpleNamespace(content=content))
        model._client.chat.side_effect = chat
        result = Assistant(model).run(DEMO_EMAIL,'yes')
        self.assertEqual(result.metrics['prompt_tokens'],30)
        self.assertEqual(result.metrics['output_tokens'],15)
