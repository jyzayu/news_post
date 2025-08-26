### YTN 뉴스 자동화

PyQt5 데스크톱 앱으로 YTN "많이 본 뉴스"를 크롤링하여 Firestore에 저장하고, 크롤링한 기사를 자동으로 네이버 블로그에 포스팅하는 시스템입니다. 또한 개발자가 사용 가능한 FastAPI 서버를 포함합니다.

- 파일 탐색기에서 YTNNewsApp.exe 더블 클릭하여 실행 가능합니다.
<img width="958" height="646" alt="image" src="https://github.com/user-attachments/assets/67878091-f7e8-40c2-a8cd-fdd57448c548" />



<img width="1198" height="832" alt="image" src="https://github.com/user-attachments/assets/a528f1af-8ed0-4f0b-9b05-afdf1898ba74" />


- YTN 크롤링 버튼을 클릭하면 테이블에서  Title 혹은 URL 동일한 것을 제외하고  뉴스 10개를 가져옵니다.

- 네이버 블로그 포스팅 버튼을 클릭하면 크롤링 한 뉴스 정보를 가지고 세 개씩 포스팅을 진행합니다. 포스팅이 완료되면 포스팅 대상에서 제외됩니다.

- 테이블에서 처리하고 싶은 뉴스 한 줄을 클릭한 후에 Read, Update, Delete 버튼을 클릭하면 작업이 가능합니다. Create를 클릭하여 뉴스를 직접 입력할 수 있습니다.



### 구성 요소
- desktop (PyQt5): 크롤링, Firestore CRUD, 네이버 블로그 포스팅, 실시간 로그
- server (FastAPI): cloud run, Firestore 기반 REST CRUD API
- config : 환경 변수 및 Firebase Admin 인증 키 템플릿
- Docs: 배포 가이드 및 스크린샷


###  Server API

- cloud run으로 배포된 API 사용합니다.
- API문서 확인

- **Base URL**: https://ytn-news-api-187404241319.asia-northeast3.run.app
- **Content-Type**: application/json; charset=utf-8

#### Health
- **GET** `/health`
  - 200:
    ```
    { "status": "ok" }
    ```

#### 목록 조회
- **GET** `/news`
  - 설명: 최신 생성 순으로 최대 200개 문서를 반환합니다.
  - 200 (예시):
    ```
    [
      {
        "id": "abc123",
        "title": "...",
        "content": "...",
        "published_at": "2024-08-12T09:30:00+09:00",
        "reporter_name": "...",
        "reporter_email": "...",
        "category": "...",
        "source_url": "https://...",
        "blog_url": "https://...",
        "status": "new",
        "created_at": "2024-08-12T00:00:00Z",
        "updated_at": "2024-08-12T00:00:00Z"
      }
    ]
    ```
  - curl:
    ```bash
    curl -s "https://ytn-news-api-187404241319.asia-northeast3.run.app/news"
    ```

#### 생성
- **POST** `/news`
  - 설명: 부분 필드만 포함해도 됩니다. 누락 필드는 서버가 기본값을 채웁니다.
  - 요청 본문 (예시):
    ```json
    {
      "title": "제목",
      "content": "본문",
      "published_at": "2024-08-12T09:30:00+09:00",
      "reporter_name": "홍길동",
      "reporter_email": "reporter@ytn.co.kr",
      "category": "정치",
      "source_url": "https://www.ytn.co.kr/...",
      "blog_url": "https://blog.naver.com/...",
      "status": "new"
    }
    ```
  - 200 (예시): 위 목록 아이템과 동일한 `NewsOut` 스키마로 생성된 문서를 반환합니다.
  - curl:
    ```bash
    curl -s -X POST \
      -H "Content-Type: application/json" \
      -d '{
        "title":"제목",
        "content":"본문",
        "source_url":"https://www.ytn.co.kr/..."
      }' \
      "https://ytn-news-api-187404241319.asia-northeast3.run.app/news"
    ```

#### 단건 조회
- **GET** `/news/{id}`
  - 404: 존재하지 않으면 `{ "detail": "Not found" }`
  - 200: `NewsOut`

#### 수정 (부분 업데이트)
- **PUT** `/news/{id}`
  - 설명: 제공한 필드만 병합 업데이트됩니다.
  - 요청 본문: `NewsCreate`와 동일 구조의 부분 필드
  - 404: 존재하지 않으면 `{ "detail": "Not found" }`
  - 200: 갱신된 `NewsOut`

#### 삭제
- **DELETE** `/news/{id}`
  - 200: `{ "status": "deleted" }`

#### 데이터 모델 요약
- **NewsCreate/Update** (요청): 모든 필드는 선택적
  - `title`, `content`, `published_at`, `reporter_name`, `reporter_email`, `category`, `source_url`, `blog_url`, `status`
- **NewsOut** (응답): 위 필드 + `id`, `created_at`, `updated_at`
  - `created_at`, `updated_at`은 RFC3339 datetime 문자열





### Quick Start (Desktop)
- exe 실행 

1) Create `config/serviceAccountKey.json` from your Firebase Admin key
2) Copy `config/.env.example` to `config/.env` and fill values
3) Install deps: `pip install -r desktop/requirements.txt`
4) Install Playwright browsers: `python -m playwright install --with-deps chromium`
5) Run: `python -m desktop.main`

### Quick Start (Server)
- cloud run으로 배포된 API 사용  API문서 확인

1) Ensure `config/serviceAccountKey.json` exists
2) Copy `.env.example` to `.env` and fill `FIREBASE_PROJECT_ID`
3) Install deps: `pip install -r server/requirements.txt`
4) Run locally: `uvicorn server.main:app --reload`

### Server API

### Build EXE
Use PyInstaller from within `desktop/`:
```
.\.venv\Scripts\pyinstaller --noconfirm --clean --onefile --windowed --name YTNNewsApp --add-data "config;config" --add-data "C:\projects\news_post\ytn-news-automation\.venv\Lib\site-packages\playwright\driver\package\.local-browsers;playwright\driver\package\.local-browsers" desktop\main.py
```
The file `YTN_News_Automation.exe` will be created in `dist/`. Move it to repo root for submission.

See `docs/deployment.md` for Cloud Run deployment.


image.png
