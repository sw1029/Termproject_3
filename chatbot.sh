#!/bin/bash
set -e

# Run crawlers (placeholders)
python -m src.crawlers.academic_calendar
python -m src.crawlers.notices
python -m src.crawlers.shuttle_bus
python -m src.crawlers.graduation_req
python -m src.crawlers.meals

# Build search indexes
python -m src.retrieval.build_index

# Launch API server
exec uvicorn src.realtime_model:app --reload --port 8000
