#!/usr/bin/env bash
# Builds the jar and three images in Docker, then runs every scenario in the README and saves its evidence to
# evidence/<scenario>/ (app.log with timestamps, client.txt, newcomer.txt, result.json). These are the video's evidence.
# Usage (Git Bash or Linux): bash run-scenarios.sh [scenario ...]
set -uo pipefail
cd "$(dirname "$0")"
LAB=$(pwd -W 2>/dev/null || pwd)
NET=sgs-net
CURL=curlimages/curl:8.11.1

MSYS_NO_PATHCONV=1 docker run --rm -v "$LAB:/lab" -v spring-graceful-m2:/root/.m2 -w /lab maven:3.9-eclipse-temurin-21 \
  mvn -q -B -DskipTests package || exit 1
for k in exec script shell; do docker build -q -t sgs-$k -f docker/Dockerfile.$k . >/dev/null || exit 1; done
docker network create $NET >/dev/null 2>&1 || true
docker version --format 'docker {{.Server.Version}}' > evidence/docker-version.txt

client() {  # client <container-name> <path>: curl in its own container, prints body, then time and exit code
  MSYS_NO_PATHCONV=1 docker run -d --name "$1" --network $NET --entrypoint sh $CURL -c \
    "curl -sS -m 90 http://sgs-app:8080$2 -w '\ntime_total=%{time_total}\n'; echo curl_exit=\$?" >/dev/null
}

scenario() {  # scenario <name> <image> <stop-timeout or ''> [docker run -e ...]
  local name=$1 image=$2 grace=$3; shift 3
  local dir=evidence/$name; rm -rf "$dir"; mkdir -p "$dir"
  docker rm -f sgs-app sgs-client sgs-new >/dev/null 2>&1
  docker run -d --name sgs-app --network $NET "$@" "$image" >/dev/null
  for i in $(seq 1 90); do  # wait until the app answers
    MSYS_NO_PATHCONV=1 docker run --rm --network $NET $CURL -s -m 2 http://sgs-app:8080/hello 2>/dev/null | grep -q Hello && break
    sleep 1
  done
  MSYS_NO_PATHCONV=1 docker exec sgs-app sh -c "tr '\0' ' ' < /proc/1/cmdline" > "$dir/pid1.txt"
  client sgs-client "/slow?seconds=20"
  sleep 2                                   # the request is now running
  local stop=(docker stop); [ -n "$grace" ] && stop+=(-t "$grace")
  if [ "$name" = s2-longer-grace ]; then (sleep 2; client sgs-new /hello) & fi
  local t0 t1; t0=$(date +%s.%N); "${stop[@]}" sgs-app >/dev/null; t1=$(date +%s.%N)
  wait
  docker wait sgs-client >/dev/null
  docker logs -t sgs-app > "$dir/app.log" 2>&1
  docker logs sgs-client > "$dir/client.txt" 2>&1
  if docker inspect sgs-new >/dev/null 2>&1; then docker wait sgs-new >/dev/null; docker logs sgs-new > "$dir/newcomer.txt" 2>&1; fi
  local code; code=$(docker inspect -f '{{.State.ExitCode}}' sgs-app)
  python - "$dir" "$code" "$t0" "$t1" "${stop[*]}" <<'EOF'
import json, os, re, sys
d, code, t0, t1, stop = sys.argv[1:]
def parse(f):
    p = os.path.join(d, f)
    if not os.path.exists(p): return None
    t = open(p, encoding='utf8', errors='replace').read()
    m = re.search(r'curl_exit=(\d+)', t); tt = re.search(r'time_total=([\d.]+)', t)
    body = re.split(r'\ntime_total=', t)[0].strip()
    return {'body': body, 'curl_exit': int(m.group(1)) if m else None, 'time_total': float(tt.group(1)) if tt else None}
r = {'scenario': os.path.basename(d), 'stop_command': stop + ' sgs-app', 'exit_code': int(code),
     'stop_seconds': round(float(t1) - float(t0), 2), 'pid1': open(os.path.join(d, 'pid1.txt')).read().strip(),
     'client': parse('client.txt')}
n = parse('newcomer.txt')
if n: r['newcomer'] = n
json.dump(r, open(os.path.join(d, 'result.json'), 'w'), indent=2)
print(f"{r['scenario']:20} exit {code}  stop {r['stop_seconds']:6.2f} s  curl_exit {r['client']['curl_exit']}  pid1: {r['pid1'][:40]}")
EOF
  docker rm -f sgs-app sgs-client sgs-new >/dev/null 2>&1
}

want() { [ $# -eq 0 ] || [[ " $ARGS " == *" $1 "* ]]; }
ARGS="$*"
want s1-default        && scenario s1-default        sgs-exec   ''
want s2-longer-grace   && scenario s2-longer-grace   sgs-exec   40
want s3-short-phase    && scenario s3-short-phase    sgs-exec   40 -e SPRING_LIFECYCLE_TIMEOUTPERSHUTDOWNPHASE=5s
want s4-immediate      && scenario s4-immediate      sgs-exec   40 -e SERVER_SHUTDOWN=immediate
want s5-script-no-exec && scenario s5-script-no-exec sgs-script ''
want s6-shell-form     && scenario s6-shell-form     sgs-shell  ''
