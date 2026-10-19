import http.client
import json
import threading
import unittest
from dataclasses import replace
from http.server import HTTPServer
from src.backend import Backend, handler_for
from src.config import Config
from src.demo import DemoMailbox, DemoModel, DemoMemory
from src.pipeline import Assistant


class DashboardTests(unittest.TestCase):
    def test_local_origin_and_queue_validation(self):
        mailbox = DemoMailbox()
        app = Backend(mailbox,Assistant(DemoModel()),DemoMemory(),'synthetic-token-'*4,Config())
        self.assertTrue(app.allowed_origin('http://127.0.0.1:8765'))
        self.assertFalse(app.allowed_origin('http://localhost:8765'))
        self.assertFalse(app.allowed_origin('null'))
        app.authorize({'Host':'127.0.0.1:8765','Origin':'http://127.0.0.1:8765',
                       'Authorization':'Bearer '+app.token})
        result = app.dispatch('/queue',{})
        self.assertEqual(result['counts'],dict(needs_reply=1,review=1,filtered=3))
        with self.assertRaises(ValueError):
            app.dispatch('/queue',{'refresh':'yes'})
        with self.assertRaises(ValueError):
            app.dispatch('/queue',{'unexpected':True})

    def test_http_static_shell_and_authenticated_queue(self):
        app = Backend(DemoMailbox(),Assistant(DemoModel()),DemoMemory(),'synthetic-token-'*4,Config())
        server = HTTPServer(('127.0.0.1',0),handler_for(app))
        app.config = replace(app.config,port=server.server_port)
        worker = threading.Thread(target=server.serve_forever,daemon=True)
        worker.start()
        try:
            def request(method,path,body=None,headers=None):
                client = http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3)
                client.request(method,path,body,headers or {})
                response = client.getresponse()
                result = response.status,response.read(),response.getheaders()
                client.close()
                return result
            code,body,headers = request('GET','/')
            self.assertEqual(code,200)
            self.assertIn(b'Your reply desk.',body)
            self.assertNotIn(b'organizer@example.test',body)
            self.assertNotIn(app.token.encode(),body)
            self.assertIn("frame-ancestors 'none'",dict(headers)['Content-Security-Policy'])
            self.assertEqual(request('GET','/dashboard.js')[0],200)
            self.assertEqual(request('GET','/../private/backend-token')[0],404)
            self.assertEqual(request('GET','/',headers={'Host':'attacker.test'})[0],403)
            self.assertEqual(request('POST','/queue','{}',{'Content-Type':'application/json'})[0],401)
            good={'Content-Type':'application/json','Authorization':'Bearer '+app.token,
                  'Origin':f'http://127.0.0.1:{server.server_port}'}
            code,body,_ = request('POST','/queue','{}',good)
            self.assertEqual(code,200)
            self.assertEqual(json.loads(body)['counts']['filtered'],3)
            self.assertEqual(request('POST','/queue','{}',dict(good,Origin='https://evil.test'))[0],403)
        finally:
            server.shutdown()
            server.server_close()
            worker.join()
