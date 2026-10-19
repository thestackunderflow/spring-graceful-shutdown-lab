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

In s2 a second, new request is sent 2 s after the stop starts, to see what a newcomer gets during shutdown.

## Tests
- `tests/test_evidence.py` asserts what each scenario's evidence must show (written before the runs).
- `src/test/java/lab/SlowControllerTest.java` checks the endpoints.
Run: `bash tests/run-tests.sh`.
