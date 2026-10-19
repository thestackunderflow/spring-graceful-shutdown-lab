"""What each scenario's evidence must show. Written before the runs (red until run-scenarios.sh has produced evidence).
Expectations come from the docs (Docker: SIGKILL after the stop timeout, 10 s by default on Linux; Spring Boot 4.1.1:
graceful shutdown on by default, 30 s per phase). Where the docs don't say (shell form), the test only asserts what was
recorded, and the video reports that.
Run: python -m unittest discover -s tests -p "test_evidence.py" """
import json
import os
import unittest

EV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'evidence')


def load(s):
    with open(os.path.join(EV, s, 'result.json'), encoding='utf8') as f:
        r = json.load(f)
    with open(os.path.join(EV, s, 'app.log'), encoding='utf8') as f:
        r['log'] = f.read()
    return r


class Default(unittest.TestCase):
    """s1: docker stop's default grace is shorter than the 20 s request: the JVM is killed mid-request."""
    def test_request_is_cut_and_container_killed(self):
        r = load('s1-default')
        self.assertNotEqual(r['client']['curl_exit'], 0)
        self.assertNotIn('done after', r['client']['body'])
        self.assertEqual(r['exit_code'], 137)                      # 128 + 9: SIGKILL
        self.assertIn('Commencing graceful shutdown', r['log'])   # Spring did get SIGTERM and started waiting
        self.assertNotIn('Graceful shutdown complete', r['log'])
        self.assertNotIn('Graceful shutdown aborted', r['log'])   # killed before Spring's own 30 s limit
        self.assertTrue(9 <= r['stop_seconds'] <= 13, r['stop_seconds'])


class LongerGrace(unittest.TestCase):
    """s2: docker stop -t 40 lets the request finish; the JVM exits on its own after SIGTERM."""
    def test_request_completes(self):
        r = load('s2-longer-grace')
        self.assertEqual(r['client']['curl_exit'], 0)
        self.assertIn('done after 20 s', r['client']['body'])
        self.assertIn('Graceful shutdown complete', r['log'])
        self.assertEqual(r['exit_code'], 143)                      # 128 + 15: ended by SIGTERM, not killed
        self.assertLess(r['stop_seconds'], 40)

    def test_a_new_request_during_shutdown_is_not_served(self):
        r = load('s2-longer-grace')
        self.assertNotEqual(r['newcomer']['curl_exit'], 0)
        self.assertNotIn('Hello', r['newcomer']['body'])


class ShortPhase(unittest.TestCase):
    """s3: Spring's own limit (5 s) ends the wait before Docker's (40 s)."""
    def test_spring_gives_up_first(self):
        r = load('s3-short-phase')
        self.assertIn('Graceful shutdown aborted with one or more requests still active', r['log'])
        self.assertNotIn('done after', r['client']['body'])
        self.assertNotEqual(r['exit_code'], 137)
        self.assertLess(r['stop_seconds'], 20)


class Immediate(unittest.TestCase):
    """s4: server.shutdown=immediate: no waiting for the request."""
    def test_no_graceful_wait(self):
        r = load('s4-immediate')
        self.assertNotIn('Commencing graceful shutdown', r['log'])
        self.assertNotIn('done after', r['client']['body'])
        self.assertLess(r['stop_seconds'], 10)


class ScriptWithoutExec(unittest.TestCase):
    """s5: a start script that runs java without exec: the shell is PID 1 and java never hears SIGTERM."""
    def test_java_never_starts_graceful_shutdown(self):
        r = load('s5-script-no-exec')
        self.assertNotIn('Commencing graceful shutdown', r['log'])
        self.assertEqual(r['exit_code'], 137)
        self.assertTrue(9 <= r['stop_seconds'] <= 13, r['stop_seconds'])
        self.assertNotEqual(r['pid1'].split()[0], 'java')            # PID 1 is the shell, not the JVM


class ShellForm(unittest.TestCase):
    """s6: shell-form ENTRYPOINT. Docker's docs warn it can block signals; whether it does depends on the image's
    /bin/sh. The test only checks the evidence is complete and self-consistent; the video reports what happened."""
    def test_recorded_and_consistent(self):
        r = load('s6-shell-form')
        graceful = 'Commencing graceful shutdown' in r['log']
        self.assertEqual(graceful, r['pid1'].split()[0] == 'java')  # graceful exactly when java itself is PID 1
        self.assertIn(r['exit_code'], (137, 143))


if __name__ == '__main__':
    unittest.main()
