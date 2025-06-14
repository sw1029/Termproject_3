#!/bin/bash
set -e

echo "===== 1. 데이터베이스 초기화 및 오프라인 크롤링 시작 ====="
python -m src.offline_crawl

echo "===== 2. 벡터 인덱스(Vector Store) 생성 시작 ====="
python -m src.retrieval.build_index

echo "===== 3. 백엔드(FastAPI) 및 프론트엔드(Flask) 서버 실행 ====="
uvicorn src.realtime_model:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
sleep 3
python webui/app.py &
FRONTEND_PID=$!
echo "UI 접속: http://localhost:5000"
wait $FRONTEND_PID
