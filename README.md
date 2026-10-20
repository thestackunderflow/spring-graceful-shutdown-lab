# Spring Boot graceful shutdown under `docker stop` (lab)

What happens to a request that is still running when a Spring Boot container is stopped? This lab measures it, with
real logs, for the video "Spring Boot Graceful Shutdown: What docker stop Does to Live Requests" (The Stack Underflow).

Everything runs in Docker. Spring Boot 4.1.1, Java 21.

## The app
`GET /slow?seconds=N` sleeps N seconds, then answers `done after N s`. It logs when a request starts and ends.
`GET /hello` answers at once.

## Scenarios (`bash run-scenarios.sh`)
Each scenario starts the app container, sends a 20 s request from a separate client container (curl), waits 2 s,
stops the container, and records: what curl got (body, curl exit code, time), how long `docker stop` took, the
container's exit code, and the app's log. Results land in `evidence/<scenario>/`.

| Scenario | Image | Stop | Spring settings |
|---|---|---|---|
| `s1-default` | exec-form ENTRYPOINT | `docker stop` (default grace) | defaults |
| `s2-longer-grace` | exec-form | `docker stop -t 40` | defaults |
| `s3-short-phase` | exec-form | `docker stop -t 40` | `spring.lifecycle.timeout-per-shutdown-phase=5s` |
| `s4-immediate` | exec-form | `docker stop -t 40` | `server.shutdown=immediate` |
| `s5-script-no-exec` | start script that runs `java` without `exec` | `docker stop` | defaults |
| `s6-shell-form` | shell-form ENTRYPOINT | `docker stop` | defaults |
| `s7-script-exec` | start script that ends with `exec java` | `docker stop -t 40` | defaults |

In s2 a poller container, started before the stop, sends a new request every 0.5 s and logs the time of each, to see what newcomers get during shutdown.

## What we measured (Docker 27.4.0, 19 Oct 2026)

A 20 s request was in flight when the stop began. Graceful shutdown is on by default in Spring Boot, with a 30 s
limit per shutdown phase; `docker stop` waits 10 s by default before it sends SIGKILL.

| Scenario | `docker stop` took | Container exit code | What the in-flight request got |
|---|---|---|---|
| `s1-default` | 10.42 s | 137 (SIGKILL) | `curl: (52) Empty reply from server` |
| `s2-longer-grace` | 18.23 s | 143 (SIGTERM) | `done after 20 s` |
| `s3-short-phase` | 7.26 s | 143 | `curl: (52) Empty reply from server` (the 5 s phase ran out) |
| `s4-immediate` | 0.41 s | 143 | `curl: (52) Empty reply from server` |
| `s5-script-no-exec` | 10.43 s | 137 | `curl: (52) Empty reply from server` (PID 1 is `/bin/sh /start.sh`; java never got SIGTERM) |
| `s6-shell-form` | 10.32 s | 137 | `curl: (52) Empty reply from server` (PID 1 is `/bin/sh -c java ...`) |
| `s7-script-exec` | 18.20 s | 143 | `done after 20 s` |

In s2, new requests were refused (`curl: (7) Failed to connect`) from the moment shutdown began, while the
in-flight request still finished. Raw logs, curl output and PID 1 for every run are in `evidence/`.

## Tests
- `tests/test_evidence.py` asserts what each scenario's evidence must show (written before the runs).
- `src/test/java/lab/SlowControllerTest.java` checks the endpoints.
- `tests/test_primer_panels.py` checks that log lines shown in the video come from `evidence/`; it needs the video's
  source file, which is not in this repo, so it is skipped here.

Run: `bash tests/run-tests.sh` (JUnit runs in a `maven:3.9-eclipse-temurin-21` container; the Python tests need only
Python 3). `tests/out/` holds the logs of the red and green test runs.

`video/` holds the two frame cards used for the video and the script that drew them from `evidence/s1-default`.

## Licence

Lab code: Apache License 2.0 (`LICENSE`).
