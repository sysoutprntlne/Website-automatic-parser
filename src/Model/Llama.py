"""Local Ollama structured chat adapter. Construction/imports have no IO."""

from src.config import Config


class ModelOutputError(RuntimeError):
    pass


class Model:
    def __init__(self, config=None):
        self.config = config or Config()
        self.calls = 0
        self.prompt_tokens = 0
        self.output_tokens = 0
        self.usage_available = False
        self._client = None

    def structured(self, task, instructions, data, schema, evaluator=False):
        import json
        from ollama import Client

        if self._client is None:
            self._client = Client(host=self.config.ollama_host, timeout=120)
        self.calls += 1
        response = self._client.chat(
            model=self.config.evaluator_model if evaluator else self.config.model,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": json.dumps({"task": task, "data": data})},
            ],
            format=schema.model_json_schema(),
            options={
                "temperature": self.config.temperature,
                "seed": self.config.seed,
                "num_ctx": 16384,
                "num_predict": 2048,
            },
        )
        if response.prompt_eval_count is not None and response.eval_count is not None:
            self.usage_available = True
            self.prompt_tokens += response.prompt_eval_count
            self.output_tokens += response.eval_count
        try:
            return schema.model_validate_json(response.message.content)
        except (ValueError, TypeError):
            raise ModelOutputError("Model returned invalid structured output") from None

    def metrics(self):
        return {
            "model_calls": self.calls,
            "prompt_tokens": self.prompt_tokens if self.usage_available else None,
            "output_tokens": self.output_tokens if self.usage_available else None,
        }
