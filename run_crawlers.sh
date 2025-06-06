#!/bin/bash
set -e

run_and_sample() {
  local module="$1"
  local path="$2"

  echo "Running $module..."
  python -m "$module"

  echo "Sample from $path"
  local file
  if [[ -f $path ]]; then
    file="$path"
  else
    file=$(ls $path 2>/dev/null | head -n 1)
  fi
  if [[ -f $file ]]; then
    head -n 5 "$file"
  else
    echo "No output file found"
  fi
  echo "-----"
}

run_and_sample src.crawlers.academic_calendar data/raw/academic_calendar/data.json
run_and_sample src.crawlers.shuttle_bus data/raw/shuttle_bus/data.json
run_and_sample src.crawlers.graduation_req data/raw/graduation_req/data.csv
run_and_sample src.crawlers.meals "data/raw/meals/*.json"
run_and_sample src.crawlers.notices "data/raw/notices/*.csv"
