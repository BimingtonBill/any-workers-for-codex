import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'launcher'))
import ds_worker as worker

REPORT = 'Status: done\nVerdict: answered\nSummary: Found value.\nLeft: nothing\nNext: none\n\nsrc.py:1'


def response(content=REPORT, calls=None, prompt=100, output=50):
    return {'id': os.urandom(8).hex(), 'choices': [{'finish_reason': 'stop', 'message':
        dict(role='assistant', content=content, **({'tool_calls': calls} if calls else {}))}],
        'usage': dict(prompt_tokens=prompt, completion_tokens=output, prompt_cache_hit_tokens=10)}


def call(name, **args):
    return dict(id='tool-1', type='function', function=dict(name=name, arguments=json.dumps(args)))


class PortTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'project'
        self.root.mkdir()
        (self.root / 'src.py').write_text('value = 42\n', encoding='utf-8')
        self.state = Path(self.temp.name) / 'state'
        self.spend = Path(self.temp.name) / 'spend'
        self.env = patch.dict(os.environ, DS_STATE_DIR=str(self.state), DS_SPEND_DIR=str(self.spend),
                              DS_PROVIDERS_USER=str(Path(self.temp.name) / 'providers.json'),
                              DEEPSEEK_API_KEY='fake-private-test-key')
        self.env.start()
        self.addCleanup(self.env.stop)

    def args(self, **kwargs):
        from types import SimpleNamespace
        base = dict(dir=str(self.root), task='Find value in src.py', task_file='', extra='', mode='read',
            max_turns=4, timeout_minutes=1, max_cost=0, provider='deepseek', tier='', label='research-001-value',
            kind='research', model='', dry_run=False, title='', parent='', schema='', full_report=False)
        base.update(kwargs)
        return SimpleNamespace(**base)

    def run_worker(self, responses, **kwargs):
        transport = unittest.mock.Mock(side_effect=responses)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = worker.run(self.args(**kwargs), transport=transport)
        return code, transport

    def manifests(self):
        return [json.loads(p.read_text()) for p in self.state.glob('runs/*/manifest.json')]

    def test_read_and_search_numbered_evidence(self):
        tools = worker.FileTools(self.root)
        self.assertEqual(tools.call('read_file', {'path': 'src.py'}), '1: value = 42')
        self.assertIn('src.py:1:', tools.call('search', {'text': '42'}))

    def test_private_traversal_and_ntfs_streams(self):
        tools = worker.FileTools(self.root)
        for name in ('../outside', '.git/config', '.env', 'src.py:secret', 'C:/outside', '/outside', '.env.local'):
            with self.subTest(name=name), self.assertRaises(PermissionError):
                tools.path(name)

    def test_denied_files_not_listed_or_searched(self):
        (self.root / 'secrets').mkdir()
        (self.root / 'secrets/key.txt').write_text('value = private')
        tools = worker.FileTools(self.root, config={'denyRead': ['secrets/**']})
        self.assertNotIn('secrets', tools.call('list_files', {}))
        self.assertNotIn('private', tools.call('search', {'text': 'value'}))

    def test_symlink_cannot_escape_or_bypass_policy(self):
        outside = Path(self.temp.name) / 'outside.txt'
        outside.write_text('secret')
        try:
            (self.root / 'link').symlink_to(outside)
        except OSError:
            self.skipTest('symlink creation unavailable for this Windows account')
        with self.assertRaises(PermissionError):
            worker.FileTools(self.root).path('link')

    def test_owned_paths_and_read_mode_are_enforced(self):
        tools = worker.FileTools(self.root, 'edit', owned=['src.py'])
        tools.call('write_file', {'path': 'src.py', 'content': 'value = 43\n'})
        self.assertIn('43', (self.root / 'src.py').read_text())
        with self.assertRaises(PermissionError):
            tools.call('write_file', {'path': 'other.py', 'content': 'x'})
        with self.assertRaises(PermissionError):
            worker.FileTools(self.root).call('write_file', {'path': 'src.py', 'content': 'x'})

    def test_edit_denies_override_ownership(self):
        tools = worker.FileTools(self.root, 'edit', {'denyEdit': ['src.py']}, owned=['src.py'])
        with self.assertRaises(PermissionError):
            tools.path('src.py', write=True)

    def test_real_request_shape_and_http_credentials(self):
        class Reply:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, size): return json.dumps(response()).encode()
        opener = unittest.mock.Mock()
        opener.open.return_value = Reply()
        with patch.object(worker.urllib.request, 'build_opener', return_value=opener):
            worker.request({'chatBaseUrl': 'https://api.deepseek.com'}, 'key', [], [], 5, 'model', 100)
        req = opener.open.call_args.args[0]
        self.assertEqual(req.full_url, 'https://api.deepseek.com/chat/completions')
        self.assertEqual(req.get_header('Authorization'), 'Bearer key')
        self.assertEqual(json.loads(req.data)['model'], 'model')

    def test_tool_loop_reports_and_accounts_cached_usage(self):
        code, transport = self.run_worker([response('', [call('read_file', path='src.py')]), response()])
        self.assertEqual(code, 0)
        self.assertEqual(transport.call_count, 2)
        self.assertIn('1: value = 42', str(transport.call_args.args[2]))
        self.assertEqual(self.manifests()[0]['status'], 'ok')
        self.assertEqual(worker.ds_spend.usage(next(self.state.glob('runs/*/transcript.jsonl')))['cache_read'], 20)
        self.assertFalse(list((self.spend / 'live').glob('*.json')))

    def test_unknown_tool_is_refused_and_worker_can_recover(self):
        code, transport = self.run_worker([response('', [call('shell', command='echo private')]), response()])
        self.assertEqual(code, 0)
        self.assertIn('Tool refused', str(transport.call_args.args[2]))

    def test_api_error_redacts_key_and_records_partial(self):
        code, _ = self.run_worker([RuntimeError('bad fake-private-test-key')])
        self.assertEqual(code, 1)
        self.assertNotIn('fake-private-test-key', str(self.manifests()))
        self.assertEqual(self.manifests()[0]['status'], 'error')
        self.assertTrue((self.spend / 'spend.jsonl').exists())
        self.assertFalse(list((self.spend / 'live').glob('*.json')))

    def test_missing_usage_fails_closed(self):
        reply = response()
        reply.pop('usage')
        code, _ = self.run_worker([reply])
        self.assertEqual(code, 1)
        self.assertIn('omitted token usage', self.manifests()[0]['error'])

    def test_turn_limit_is_incomplete(self):
        code, _ = self.run_worker([response('', [call('read_file', path='src.py')])], max_turns=1)
        self.assertEqual(code, 1)
        self.assertEqual(self.manifests()[0]['status'], 'partial')

    def test_deadline_stops_without_an_api_request(self):
        code, transport = self.run_worker([], timeout_minutes=0.00000000001)
        self.assertEqual(code, 3)
        transport.assert_not_called()
        self.assertEqual(self.manifests()[0]['status'], 'timed-out')

    def test_cap_stops_before_response_tools_execute(self):
        code, transport = self.run_worker([response('', [call('read_file', path='src.py')], output=100000)], max_cost=0.001)
        self.assertEqual(code, 4)
        self.assertEqual(transport.call_count, 1)
        self.assertFalse(list(self.state.glob('runs/*/tools.jsonl')))
        self.assertGreater(self.manifests()[0]['cost'], 0)

    def test_admission_budget_prevents_request(self):
        self.spend.mkdir()
        (self.spend / 'limits.json').write_text('{"day": 0.00001}')
        code, transport = self.run_worker([])
        self.assertEqual(code, 4)
        transport.assert_not_called()

    def test_truncated_final_response_is_not_accepted(self):
        reply = response()
        reply['choices'][0]['finish_reason'] = 'length'
        code, _ = self.run_worker([reply])
        self.assertEqual(code, 1)

    def test_explicit_partial_report_is_not_accepted(self):
        code, _ = self.run_worker([response(REPORT.replace('Status: done', 'Status: partial'))])
        self.assertEqual(code, 1)
        self.assertEqual(self.manifests()[0]['status'], 'partial')

    def test_schema_rejects_wrong_fields(self):
        schema = self.root / 'schema.json'
        schema.write_text('{"type":"object","properties":{"summary":{"type":"string"}},"required":["summary"],"additionalProperties":false}')
        code, _ = self.run_worker([response('{"summary": 3}')], schema=str(schema))
        self.assertEqual(code, 1)
        code, _ = self.run_worker([response('{"summary": "done"}')], schema=str(schema))
        self.assertEqual(code, 0)

    def test_schema_setup_error_does_not_claim_budget(self):
        with self.assertRaises(ValueError):
            worker.run(self.args(schema=str(self.root / 'missing.json')))
        self.assertFalse(self.spend.exists())

    def test_edit_worker_rejects_main_checkout(self):
        with self.assertRaises(ValueError):
            worker.run(self.args(mode='edit'))

    def test_coder_worktree_and_host_acceptance_gate(self):
        def git(*args):
            result = subprocess.run(['git', '-C', str(self.root), *args], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            return result.stdout.strip()
        git('init')
        git('add', 'src.py')
        git('-c', 'user.name=Port Test', '-c', 'user.email=port-test@example.invalid', 'commit', '-m', 'fixture')
        base = git('rev-parse', 'HEAD')
        worktree = self.root / 'local' / 'impl' / 'impl-001-value'
        git('worktree', 'add', '--detach', str(worktree), 'HEAD')
        self.addCleanup(lambda: subprocess.run(['git', '-C', str(self.root), 'worktree', 'remove', '--force', str(worktree)], capture_output=True))
        meta = dict(task='impl-001-value', base=base, files=['src.py'], accept=['python -c "assert 1 == 1"'])
        (worktree / '.ds-impl.json').write_text(json.dumps(meta))
        code, _ = self.run_worker([response('', [call('write_file', path='src.py', content='value = 43\n')]), response()],
                                 dir=str(worktree), mode='edit', kind='impl')
        self.assertEqual(code, 0)
        self.assertIn('43', (worktree / 'src.py').read_text())
        self.assertIn('42', (self.root / 'src.py').read_text())
        if os.name == 'nt':
            result_path = worktree / '.ds-result.json'
            result_path.write_text('[ds-agent] run=test session=test status=partial')
            result = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                str(ROOT / 'tools/ds_impl.ps1'), '-Post', 'impl-001-value'], cwd=self.root,
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn('accept(0)', result.stdout)
            self.assertIn('acceptance FAIL', result.stdout)
            result_path.write_text('[ds-agent] run=test session=test status=ok')
            result = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                str(ROOT / 'tools/ds_impl.ps1'), '-Post', 'impl-001-value'], cwd=self.root,
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('acceptance PASS', result.stdout)

    def test_unsupported_provider_and_web_kind_rejected(self):
        for kwargs in ({'provider': 'meta'}, {'kind': 'websearch'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                worker.run(self.args(**kwargs))

    @unittest.skipUnless(os.name == 'nt', 'Windows installer')
    def test_installer_and_installed_entry_point(self):
        target = Path(self.temp.name) / 'test skills'
        for _ in range(2):
            result = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                str(ROOT / 'tools/install-skill.ps1'), '-Target', str(target)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        installed = target / 'deepseek-agents'
        self.assertTrue((installed / 'ds_worker.py').exists())
        self.assertTrue(list((target.parent / 'any-workers-backups').glob('deepseek-agents-*')))
        result = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
            str(installed / 'ds-agent.ps1'), '-Task', 'Read src.py', '-Dir', str(self.root), '-DryRun'],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('python-chat-completions', result.stdout)


if __name__ == '__main__':
    unittest.main()
