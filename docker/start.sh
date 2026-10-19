#!/bin/sh
echo "start.sh: starting the app"
java -jar /app.jar "$@"
echo "start.sh: the app exited with $?"
