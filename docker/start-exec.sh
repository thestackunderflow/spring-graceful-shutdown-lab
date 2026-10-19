#!/bin/sh
echo "start-exec.sh: starting the app"
exec java -jar /app.jar "$@"
