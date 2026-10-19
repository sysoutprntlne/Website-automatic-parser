import tempfile
import unittest
from unittest.mock import MagicMock
from email.message import EmailMessage
import base64
from src.config import Config
from src.Gmail.client import GmailClient, authenticate, AuthenticationRequired
from src.Gmail.sender import reply_for, approval_digest, send_gmail_msg
from src.Model.memry.Vector_lib import Memory
from src.pipeline import Assistant, remember_confirmed
from src.demo import DemoModel
from test_gmail import fixture


class WorkflowTests(unittest.TestCase):
    def test_import_draft_edit_approve_send_confirm_persist(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Config(memory_path=directory+'/memory')
            service = MagicMock()
            gmail, memory = GmailClient(service,config), Memory(config)
            historical = fixture('Thanks! Sounds good.',sent=True,id='historical')
            historical['threadId'] = 'historical-thread'
            service.users().messages().list().execute.return_value = {'messages':[{'id':'historical'}]}
            service.users().messages().get().execute.return_value = historical
            memory.import_sent(gmail,limit=1)
            self.assertEqual(memory.collection.count(),1)
            service.users().messages().get().execute.return_value = fixture()
            incoming = gmail.get('m1')
            result = Assistant(DemoModel(),memory,config).run(incoming,'yeah sure')
            self.assertTrue(result.passed)
            self.assertEqual(memory.collection.count(),1)
            reply = reply_for(incoming,'me@example.test','My final edited response.')
            service.users().getProfile().execute.return_value = {'emailAddress':'me@example.test'}
            service.users().messages().send().execute.return_value = {'id':'final'}
            self.assertEqual(send_gmail_msg(gmail,reply,approval_digest(reply)),'final')
            self.assertEqual(memory.collection.count(),1)  # send acknowledgment is not memory confirmation
            final = fixture(reply.body,sent=True,id='final')
            service.users().messages().get().execute.return_value = final
            remember_confirmed(gmail,memory,'final')
            memory.import_sent(gmail,limit=1)  # same fixture upserts, does not duplicate
            restored = Memory(config)
            self.assertEqual(restored.collection.count(),2)
            entry = next(item for item in restored.inspect(include_content=True) if item['source_message_id']=='final')
            self.assertEqual(entry['body'].strip(),'My final edited response.')

    def test_auth_is_explicit_without_token(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(AuthenticationRequired):
                authenticate(Config(token_path=directory+'/missing-token'))

    def test_expired_auth_failure_is_actionable_and_redacted(self):
        from unittest.mock import patch, Mock
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'token'
            path.write_text('{}')
            creds = Mock(valid=False,expired=True,refresh_token='SYNTHETIC')
            creds.refresh.side_effect = RuntimeError('PRIVATE ERROR PAYLOAD')
            with patch('google.oauth2.credentials.Credentials.from_authorized_user_file',return_value=creds):
                with self.assertRaisesRegex(AuthenticationRequired,'reauthorize') as caught:
                    authenticate(Config(token_path=str(path)))
                self.assertNotIn('PRIVATE',str(caught.exception))

    def test_read_only_token_requires_explicit_send_reauthorization(self):
        from unittest.mock import patch, Mock
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'token'
            path.write_text('{}')
            creds = Mock(valid=True,expired=False)
            creds.has_scopes.side_effect = lambda scopes: not any(scope.endswith('gmail.send') for scope in scopes)
            with patch('google.oauth2.credentials.Credentials.from_authorized_user_file',return_value=creds) as loader:
                with self.assertRaises(AuthenticationRequired):
                    authenticate(Config(token_path=str(path)),allow_send=True)
                loader.assert_called_once_with(str(path))
