# Termproject_3

> **Goal**  
> - 5종 정보(학사일정·공지사항·셔틀버스·졸업요건·식단)를 주기적으로 **크롤링**  
> - **LLM 0-4 분류기 + RAG 파이프라인**으로 실시간 Q&A 제공  
> - Flask web ui/CLI/REST 세 가지 인터페이스 지원  

---

## 📂 프로젝트 구조

> 오른쪽 `# ---` 주석은 **각 파일의 핵심 역할**입니다.

```text
Termproject_{3}/
├── data/                                # 테스트·원본·캐시 데이터 저장
│   ├── test_cls.json             # --- 0~4 분류기 단위 테스트 질문·정답 세트
│   ├── test_chat.json            # --- 챗봇 E2E 테스트 질문·정답 세트
│   └── raw/                      # --- 크롤링 원본 HTML/PDF/CSV 일자별 스냅샷
│
├── src/                                 # 애플리케이션 소스 코드
│   ├── classifier.ipynb         *# --- LLM 분류기 실험·파인튜닝·ONNX 추출 노트북
│   ├── chatbot_ui.py            *# --- Flask 기반 web UI: 실시간 대화 + 시각화
│   ├── realtime_model.py        *# --- FastAPI 서버: 분류→RAG→응답 REST 엔드포인트
│   │
│   ├── crawlers/                        # 항목별 크롤러 5종
│   │   ├── __init__.py          # --- 패키지 초기화
│   │   ├── academic_calendar.py # --- plus.cnu.ac.kr 학사일정 HTML/PDF 파싱
│   │   ├── notices.py           # --- 학과·대학 공지사항 links.txt 기반 크롤링
│   │   ├── shuttle_bus.py       # --- 셔틀버스 시간표·변경 공지 수집
│   │   ├── graduation_req.py    # --- 졸업요건 페이지/문서 스크래핑
│   │   └── meals.py             # --- 학식·교직원 식단표 크롤링
│   │
│   ├── retrieval/                       # 검색·인덱싱·프롬프트 로직
│   │   ├── __init__.py
│   │   ├── build_index.py       # --- FAISS/Qdrant + BM25 인덱스 (batch upsert)
│   │   └── rag_pipeline.py      # --- Hybrid Search + 프롬프트 템플릿 정의
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py            # --- 경로·DB·API 키 환경설정 로더
│   │   └── logger.py            # --- loguru 기반 표준 로깅 설정
│   │
│   ├── evaluation/
│   │   ├── __init__.py
│   │   └── evaluate_rag.py      # --- Ragas recall/faithfulness 메트릭 계산
│   │
│   └── __init__.py
├── webui/                              # Flask‑SocketIO 채팅 UI
│   ├── app.py                 # --- 실시간 채팅 웹 서버
│   ├── templates/index.html   # --- 기본 채팅 창 템플릿
│   └── static/                # --- JS/CSS 정적 리소스
│
├── model/
│   └── model.bin               *# --- 임베딩(예: KoE5) 파인튜닝 가중치
│
├── outputs/                             # 실행 중 생성된 결과 및 로그
│   ├── cls_output.json          *# --- 분류기 추론 결과 샘플(log)
│   ├── chat_output.json         *# --- 챗봇 데모 세션 로그
│   └── realtime_output.json     *# --- 실시간 API 인입/응답 기록
│
├── chatbot.sh                   *# --- 전체 파이프라인(크롤러→인덱스→API) 구동 스크립트
├── requirements.txt             *# --- Python 패키지 의존성 목록
└── README.md                    *# --- (현재 문서)



# 📚 파일별 상세 설계 — 역할과 핵심 구성요소(함수·클래스)

이 문서는 **Termproject_{조}** 저장소의 각 항목이 “무엇을, 어떻게” 담당하는지를  
**자연어**로 상세히 기술합니다. 실제 구현 시 함수/클래스 시그니처는 변경될 수 있으나,  
전체 흐름·모듈 경계·의존 관계를 한눈에 파악할 수 있도록 구성했습니다.

---

## 1. `data/`

| 파일(폴더) | 역할 | 내부 내용 |
|------------|------|-----------|
| `test_cls.json` | LLM 0-4 **분류기 단위시험** 데이터 | `{ "question": "...", "label": 2 }` 형태의 JSONL |
| `test_chat.json` | 챗봇 **E2E 시나리오** | `{"user":"...", "expected":"..."}`  |
| `raw/` | **크롤링 원본 스냅샷** 저장소 | `<YYYYMMDD>/academic.html`, `…/meals.csv` 등 |

---

## 2. `src/`

### 2-1. 최상위 스크립트·노트북

| 파일 | 주요 클래스/함수 | 설명 |
|------|-----------------|------|
| **`classifier.ipynb`** | - `train_classifier()`<br>- `evaluate()`<br>- `export_onnx()` | ✅ **노트북**<br>1) 사전학습 Ko-E5 등 임베딩 → 라벨 0-4 분류기 파인튜닝<br>2) `evaluate()`로 검증 F1 출력<br>3) `export_onnx()`로 추론용 ONNX 저장 |
| **`chatbot_ui.py`** | `ChatApp` streamlip을 사용하지 않고 Flask 기반 web ui 구성 | - 세션 스테이트 관리(`st.session_state["history"]`)<br>- FastAPI 백엔드 호출(`/answer`, `/predict`)<br>- 답변·출처・Diff 하이라이트 렌더링 |
| **`realtime_model.py`** | `FastAPI()` 인스턴스<br>`router = APIRouter()`<br>`RAGService` 클래스 | - `/predict` : 0-4 라벨 반환<br>- `/answer` : 라우팅→RAG→답변 JSON 스트림<br>- `RAGService` 내부에서 **HybridRetriever · AnswerGenerator** 호출 |

---

### 2-2. `crawlers/` — 5종 정보 수집 담당

> 모든 크롤러는 **공통 추상 클래스 `BaseCrawler`**(메소드 `fetch()`, `parse()`, `save()`)를 상속합니다.

| 파일 | 주요 클래스/함수 | 설명 |
|------|-----------------|------|
| `academic_calendar.py` | `AcademicCalendarCrawler(BaseCrawler)` | - 학사일정 **HTML 표 + PDF** 다운로드<br>- 월/일/이벤트 파싱 → `data/raw/…/academic.json` |
| `notices.py` | `NoticeCrawler(BaseCrawler)` | - `TODO_dir/cnu_crawler/data/links.txt`에 정의된 학과·대학 **공지 게시판**을 순회<br>- Generic 스크레이퍼로 제목·URL·게시일만 추출해 `data/raw/notices/…/*.csv` 저장 |
| `shuttle_bus.py` | `ShuttleBusCrawler(BaseCrawler)` | - 셔틀 운행표∙변경 공지 크롤링<br>- 시간표 CSV·이미지 OCR 지원 |
| `graduation_req.py` | `GraduationRequirementCrawler(BaseCrawler)` | - 졸업요건 PDF/웹 테이블 스크랩<br>- `compare_versions()`로 연도별 차이 추적 |
| `meals.py` | `MealsCrawler(BaseCrawler)` | - 학식·교직원식단 **주간 표** 파싱<br>- 식당·식사타입별 칼로리/알러지 정보 정규화 |

---

### 2-3. `retrieval/` — 검색·프롬프트 로직

| 파일 | 주요 클래스/함수 | 설명 |
|------|-----------------|------|
| `build_index.py` | `build_bm25()`<br>`build_vector()`<br>`sync_indexes()` | - 공지·학사일정 등을 로드해 **BM25 & FAISS/Qdrant 벡터 인덱스** 생성<br>- `sync_indexes()`에서 최신 파티션 ‘hot-swap’ |
| `rag_pipeline.py` | `HybridRetriever`<br>`PromptBuilder`<br>`AnswerGenerator` | 1. **HybridRetriever**: `search_semantic() + search_bm25()` 후 `recency_rerank()`<br>2. **PromptBuilder**: 컨텍스트·지침 포함 GPT 시스템 프롬프트 생성<br>3. **AnswerGenerator**: OpenAI API 호출, 스트리밍 토큰 처리 |

---

### 2-4. `utils/`

| 파일 | 구성 | 설명 |
|------|------|------|
| `config.py` | `Settings`(Pydantic BaseSettings) | - DB 경로·API 키·인덱스 위치 등 환경 변수 로드 |
| `logger.py` | `init_logger(name:str)` | - `loguru` 래퍼: 시간·레벨·JSON 로그 옵션 |
| `__init__.py` | - | 패키지 네임스페이스 초기화 |

---

### 2-5. `evaluation/`

| 파일 | 주요 함수 | 설명 |
|------|-----------|------|
| `evaluate_rag.py` | `eval_recall_at_k()`<br>`eval_faithfulness()` | - **Ragas** 메트릭 호출 래퍼<br>- 로컬 쿼리셋으로 Retrieval / Generation 품질 수집 |

---

## 3. `model/`

| 파일 | 내용 |
|------|------|
| `model.bin` | 임베딩 모델 가중치 (예: KoE5 → 학습·양자화된 `sentence-transformers` 포맷) |

---

## 4. `outputs/`

| 파일 | 용도 |
|------|------|
| `cls_output.json` | 분류기 데모·배치 추론 결과 로그 |
| `chat_output.json` | Streamlit UI 대화 세션 기록 |
| `realtime_output.json` | FastAPI `/answer` 호출 로그 (요청·응답·latency) |

---

## 5. 루트 스크립트·메타파일

| 파일 | 설명 |
|------|------|
| `chatbot.sh` | ① **모든 크롤러 실행** → ② `build_index.py` 호출 → ③ FastAPI 실행 (uvicorn) |
| `requirements.txt` | Python 패키지 고정 버전 목록 (`fastapi`, `streamlit`, `qdrant-client` …) |
| `README.md` | **프로젝트 개요 및 파일 설명(본 문서)** |

---

### 🔗 모듈 간 의존 흐름

crawlers/* ─► data/raw/ ┐
├── build_index.py ─► vector_store/
classifier.ipynb ─► model/model.bin │
│
FastAPI(realtime_model.py) ◄─ rag_pipeline.py ◄─────┘
Streamlit(chatbot_ui.py) ───┘


- **크롤러**가 원본을 수집해 `data/raw/` 업데이트  
- `build_index.py` 가 주기적으로 벡터/BM25 인덱스를 재생성  
- `realtime_model.py` 는 REST API 층에서 `rag_pipeline`을 호출  
- Flask web UI·CLI·테스트 모두 같은 REST 인터페이스를 소비  

