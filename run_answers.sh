#!/bin/bash
set -e

compile_all() {
  python -m py_compile src/answers/*.py
}

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

compile_all

run_sample src.answers.academic_calendar_answer "5월 1일 학사일정 알려줘"
run_sample src.answers.meals_answer "5월 1일 2학생회관 중식 뭐야"
run_sample src.answers.notices_answer "수학과 공지 알려줘"
run_sample src.answers.shuttle_bus_answer "셔틀버스 노선 알려줘"
run_sample src.answers.shuttle_bus_answer "셔틀버스 변동 사항 보여줘"
run_sample src.answers.graduation_req_answer "인공지능학과 졸업 요건 알려줘"
