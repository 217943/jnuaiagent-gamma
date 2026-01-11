# 📘 JNU AI Agent Gamma: 성장마루 AI 클리닉 배정 시스템

## 1. 프로젝트 개요
* **목적:** AI 활용 클리닉(서비스) 운영을 위한 상담 접수 및 AI 기반 트리아지(Triage) 시스템
* **핵심 기능:**
    1. 사용자의 상담 요청 접수
    2. AI(GPT-4o)가 난이도(L0~L3) 및 담당자 자동 분류
    3. 관리자(Human)의 최종 검토 및 배정 확정
* **특징:** **Serverless & No-DB Architecture.** Streamlit Cloud와 GitHub Repository(JSON)만으로 운영됨.

## 2. 데이터 명세 (data/requests.json)
데이터는 이 리포지토리의 `data/requests.json` 파일에 저장됩니다.
- `id`: 고유 ID (UUID)
- `timestamp`: 신청 시간
- `user_info`: 신청자 정보 (신분, 소속 등)
- `query`: 문의 내용
- `ai_analysis`: AI 분석 결과 (JSON)
- `status`: 상태 (pending / approved / rejected)
- `final_assignee`: 최종 배정자

## 3. 설치 및 실행
1. 라이브러리 설치: `pip install -r requirements.txt`
2. 로컬 실행: `streamlit run app.py`
3. 배포: Streamlit Cloud에 이 리포지토리 연결

## 4. 환경 변수 설정 (Secrets)
`.streamlit/secrets.toml` 또는 Streamlit Cloud Secrets에 다음 내용 필수:
```toml
OPENAI_API_KEY = "sk-..."
GITHUB_TOKEN = "ghp_..."  # Repo Write 권한이 있는 토큰
REPO_NAME = "your-github-id/jnuaiagent-gamma"
ADMIN_PASSWORD = "admin" # 관리자 접속 비밀번호