#!/bin/bash
set -e

python -m src.crawlers.academic_calendar
python -m src.crawlers.shuttle_bus
python -m src.crawlers.graduation_req
python -m src.crawlers.meals
python -m src.crawlers.notices
