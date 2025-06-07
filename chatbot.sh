#!/bin/bash
set -e

# Run crawlers (placeholders)
if [[ "$EVAL_ONLY" != "1" ]]; then
  python -m src.crawlers.academic_calendar || true
  python -m src.crawlers.notices || true
  python -m src.crawlers.shuttle_bus || true
  python -m src.crawlers.graduation_req || true
  python -m src.crawlers.meals || true
fi

# Build search indexes
python -m src.retrieval.build_index

# Launch API server in background
uvicorn src.realtime_model:app --reload --port 8000 &
SERVER_PID=$!
sleep 3

# Launch web UI in background
python webui/app.py &
WEBUI_PID=$!
sleep 1

# Generate evaluation outputs
python -m src.evaluation.generate_outputs || true

# Keep servers running if script invoked normally
if [[ "$EVAL_ONLY" == "1" ]]; then
  kill $SERVER_PID $WEBUI_PID
  wait $SERVER_PID $WEBUI_PID 2>/dev/null || true
else
  wait $SERVER_PID $WEBUI_PID
fi
