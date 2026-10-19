import unittest
from unittest.mock import patch
from src.config import Config
from src.domain import Reply


class CoreTests(unittest.TestCase):
    def test_env_and_bounds(self):
        with patch.dict('os.environ', {'REPLY_ATTEMPTS': '2'}):
            self.assertEqual(Config.from_env().attempts, 2)
        with self.assertRaises(ValueError):
            Config(attempts=0)

    def test_header_injection(self):
        with self.assertRaises(ValueError):
            Reply(to=['a@example.test'], subject='OK\nBcc: x@y.test', body='yes',
                  thread_id='t', in_reply_to='', references='')
