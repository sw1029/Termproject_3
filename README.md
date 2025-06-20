# Termproject_3


## 환경 설정



본 프로젝트는 Linux 환경에서 동작하도록 구성되었습니다. Windows 전용 패키지(pywin32 등)는 제거되어 있으므로 WSL 또는 리눅스 배포판에서 실행하시기 바랍니다.

requirements.txt를 통해 필요 종속성을 설치하시기를 바립니다.

이 프로젝트는 python 3.10.12, torch 2.5.1 환경에서 실행되는 것을 전제로 동작합니다.

## 챗봇 사용 방법

`chatbot.sh` 스크립트를 실행하면 Flask 기반 웹 UI가 구동됩니다. 질문을 전송하면
`question/` 디렉터리에 JSON 파일이 저장되고, `classifier.ipynb`를 수동으로 실행해
분류를 수행하면 예측 결과가 `answer/`에 같은 이름으로 저장됩니다. 웹 UI는 주기적
으로 해당 답변 파일을 확인하여 분류 라벨에 맞는 응답을 화면에 표시합
니다.

question 디렉토리에 저장된 json 파일들은 classifier.ipynb를 전체 실행 시 분류 결과와 챗봇 대답 결과가 둘 다 answer 디렉토리에 저장됩니다.
