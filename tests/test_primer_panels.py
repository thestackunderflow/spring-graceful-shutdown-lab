"""Every log line shown in the video's terminal panels comes from this lab's evidence.
Checks the primer at Refream-Canvas/mcp-canvas/primers/spring-graceful-shutdown.primer.json (skipped if absent):
- a line starting with a time (HH:MM:SS.mmm) must match an app.log line with that time containing the line's first words;
- a "client: ..." line must appear in a client.txt or newcomer.txt;
- "exit code: N" and "took N s" must match some scenario's result.json.
Run: python -m unittest discover -s tests -p "test_primer_panels.py" """
import glob
import json
import os
import re
import unittest

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIMER = os.path.join(LAB, '..', 'Refream-Canvas', 'mcp-canvas', 'primers', 'spring-graceful-shutdown.primer.json')


def panel_lines():
    p = json.load(open(PRIMER, encoding='utf8'))
    for c in p['chapters']:
        for b in c['beats']:
            if b.get('panel', {}).get('kind') == 'terminal':
                for ln in b['panel']['lines']:
                    yield b['id'], ln


class PanelsComeFromEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(PRIMER):
            raise unittest.SkipTest('primer not found')
        cls.logs = [l for f in glob.glob(os.path.join(LAB, 'evidence', '*', 'app.log'))
                    for l in open(f, encoding='utf8', errors='replace')]
        cls.client = ''.join(open(f, encoding='utf8', errors='replace').read()
                             for f in glob.glob(os.path.join(LAB, 'evidence', '*', '*.txt')))
        cls.results = [json.load(open(f)) for f in glob.glob(os.path.join(LAB, 'evidence', '*', 'result.json'))]

    def test_timestamped_lines(self):
        n = 0
        for beat, ln in panel_lines():
            m = re.match(r'^(\d\d:\d\d:\d\d\.\d{3})\s+(.*)', ln)
            if not m:
                continue
            words = [w for w in m.group(2).replace('GracefulShutdown :', '').replace('…', ' ').split() if w][:3]
            hit = [l for l in self.logs if m.group(1) in l and all(w in l for w in words)]
            self.assertTrue(hit, f'{beat}: "{ln}" not in any app.log')
            n += 1
        self.assertGreater(n, 5)

    def test_client_lines(self):
        for beat, ln in panel_lines():
            if ln.startswith('client: curl:'):
                self.assertIn(ln[len('client: '):], self.client, f'{beat}: {ln}')

    def test_exit_codes_and_stop_times(self):
        codes = {r['exit_code'] for r in self.results}
        times = {f"{r['stop_seconds']:.2f}" for r in self.results}
        for beat, ln in panel_lines():
            for c in re.findall(r'exit code: (\d+)', ln):
                self.assertIn(int(c), codes, f'{beat}: {ln}')
            for t in re.findall(r'took ([\d.]+) s', ln):
                self.assertIn(t, times, f'{beat}: {ln}')


if __name__ == '__main__':
    unittest.main()
