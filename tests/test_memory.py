import tempfile
import unittest
from unittest.mock import Mock
from src.config import Config
from src.domain import Email
from src.Model.memry.Vector_lib import Memory


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.config = Config(memory_path=self.directory.name, style_chars=100)
        self.memory = Memory(self.config)

    def tearDown(self):
        self.directory.cleanup()

    def sent(self, id='1', thread='old', body='Thanks, I can attend the meeting.'):
        return Email(id=id, thread_id=thread, sender='me@example.test', subject='meeting',
                     body=body, sent_by_user=True, timestamp='1000')

    def test_empty_import_dedup_and_persistence(self):
        self.assertEqual(self.memory.retrieve('meeting'), [])
        gmail = Mock()
        gmail.messages.return_value = ['1']
        gmail.confirm_sent.return_value = self.sent()
        self.memory.import_sent(gmail)
        self.memory.import_sent(gmail)
        self.assertEqual(self.memory.collection.count(), 1)
        other = Memory(self.config)
        self.assertEqual(other.retrieve('meeting')[0]['metadata']['source_message_id'], '1')
        self.assertNotIn('body', other.inspect()[0])

    def test_unsent_and_thread_exclusion(self):
        with self.assertRaises(ValueError):
            self.memory.remember_sent(self.sent().model_copy(update={'sent_by_user': False}))
        self.memory.remember_sent(self.sent())
        self.assertEqual(self.memory.retrieve('meeting', exclude_thread='old'), [])
        self.assertEqual(self.memory.retrieve('meeting', exclude_ids=['1']), [])
        self.assertEqual(self.memory.collection.count(), 1)

    def test_relevance_budget_delete_reset(self):
        self.memory.remember_sent(self.sent('1', body='meeting attendance confirm thanks'))
        self.memory.remember_sent(self.sent('2', body='apples oranges bananas fruit'))
        examples = self.memory.retrieve('meeting attendance confirm')
        self.assertEqual(examples[0]['metadata']['source_message_id'], '1')
        self.assertLessEqual(sum(len(e['body']) for e in examples), 100)
        self.memory.delete('1')
        self.assertEqual(self.memory.collection.count(), 1)
        with self.assertRaises(ValueError):
            self.memory.reset()
        self.memory.reset(confirmed=True)
        self.assertEqual(self.memory.collection.count(), 0)
