#!/bin/bash
set -e

echo "===== 1. 데이터베이스 초기화 및 오프라인 크롤링 시작 ====="
python -m src.offline_crawl

echo "===== 2. 벡터 인덱스(Vector Store) 생성 시작 ====="
python -m src.retrieval.build_index

echo "===== 3. 챗봇 서버 실행 ====="
python webui/app.py
