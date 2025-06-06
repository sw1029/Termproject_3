#!/bin/bash
set -e

run_sample() {
  local module="$1"
  local question="$2"

  echo "$module -- $question"
  python - <<PY
import $module as mod
print(mod.generate_answer("""$question"""))
PY
  echo "-----"
}

run_sample src.answers.academic_calendar_answer "5월 3일 학사일정 알려줘"
run_sample src.answers.meals_answer "5월 3일 2학생회관 중식 뭐야"
run_sample src.answers.notices_answer "컴퓨터공학부 공지 알려줘"
run_sample src.answers.shuttle_bus_answer "셔틀버스 노선 알려줘"
run_sample src.answers.graduation_req_answer "컴퓨터공학부 졸업 요건 알려줘"
