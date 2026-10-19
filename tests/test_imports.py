import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ImportTests(unittest.TestCase):
    def test_imports_do_not_authenticate_open_database_or_call_models(self):
        root = str(Path(__file__).resolve().parents[1])
        script = '''
import builtins, importlib, pathlib
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in ('chromadb','ollama','googleapiclient','google_auth_oauthlib'):
        raise AssertionError('Service library imported at module import: '+name)
    return original(name,*args,**kwargs)
builtins.__import__ = guarded
for module in ('src.main','src.pipeline','src.backend','src.Gmail.reader','src.Gmail.client',
               'src.Gmail.sender','src.Model.Llama','src.Model.memry.Vector_lib',
               'src.eval_model.eval','src.benchmarks.sample'):
    importlib.import_module(module)
assert not list(pathlib.Path('.').iterdir()), 'Import created files'
'''
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable,'-B','-c',script],cwd=directory,
                                    env=dict(os.environ,PYTHONPATH=root),capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
