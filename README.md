# Termproject_3


## 환경 설정

Python 3.10.12 환경을 기준으로 동작합니다. `pyenv` 사용 시 아래 명령으로 프로젝트 디렉터리에서 해당 버전을 활성화하세요.

```bash
pyenv install 3.10.12       # 최초 한 번만 실행
pyenv local 3.10.12
```

본 프로젝트는 Linux 환경에서 동작하도록 구성되었습니다. Windows 전용 패키지(pywin32 등)는 제거되어 있으므로 WSL 또는 리눅스 배포판에서 실행하시기 바랍니다.

필수 파이썬 패키지와 Torch는 `src/classifier.ipynb`의 첫 번째 셀을 실행하면 자동으로 설치됩니다.
