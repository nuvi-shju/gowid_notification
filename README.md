# 고위드 법인카드 알림 시스템

Google Sheets의 고위드 법인카드 사용 내역을 읽어와서 각 직원에게 Slack DM으로 알림을 보내는 자동화 시스템입니다. Zapier 인터페이스를 통해 수동으로 실행할 수 있습니다.

## 📋 기능

- **수동 실행**: Zapier 인터페이스의 버튼 클릭으로 수동 실행합니다
- **개인별 알림**: 각 직원에게 개인화된 DM으로 위반 내역을 전송합니다
- **다양한 위반 유형 지원**: 점심식비, 저녁식비, 개인 오사용 등 다양한 위반 내역을 처리합니다
- **테스트 모드**: 실제 Slack 메시지 전송 없이 테스트할 수 있습니다
- **에러 알림**: 처리 중 오류 발생 시 Slack 채널로 알림을 보냅니다

## 🏗️ 아키텍처

- **Flask 웹 애플리케이션**: HTTP 요청을 처리하는 웹 서버
- **Zapier 인터페이스**: 버튼 클릭으로 웹훅을 트리거합니다
- **Google Sheets API**: 고위드 위반 내역 데이터를 읽어옵니다
- **Slack API**: 개인 DM 및 채널 메시지를 전송합니다
- **Google Cloud Run**: 클라우드 환경에서 실행됩니다

## 📊 데이터 구조

### Google Sheets 구조
1. **고위드 위반내역 시트** (`SPREADSHEET_ID`)
   - 월별 시트 (예: `202507`)
   - 컬럼: 소지자, 공제 총액, 직접 입금 금액, 점심 위반금액, 저녁 위반금액, 저녁 위반건수, 개인오사용금액, 기타 위반금액

2. **사용자 매핑 시트** (`USERMAP_SHEET_ID`)
   - 컬럼: 이름, Slack ID

## 🚀 설치 및 실행

### 1. 환경 설정

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
export SLACK_BOT_TOKEN="your_slack_bot_token"
```

### 3. Google Cloud 인증

Google Cloud 프로젝트에서 서비스 계정을 생성하고 `key.json` 파일을 다운로드하여 프로젝트 루트에 저장하세요.

### 4. 실행

#### 로컬 실행
```bash
python main.py
```

#### Flask 서버 실행
```bash
flask run
# 또는
python -m flask run
```

#### Docker 실행
```bash
docker build -t gowid-notification .
docker run -p 8080:8080 -e SLACK_BOT_TOKEN="your_token" gowid-notification
```

## 📝 API 사용법

### 웹훅 URL
```
https://gowid-notification-809088966352.asia-northeast3.run.app
```

### Zapier에서 실행
Zapier 인터페이스의 버튼을 클릭하면 자동으로 웹훅이 호출됩니다.

### 수동 테스트 (curl)
```bash
# 일반 실행
curl -X POST https://gowid-notification-809088966352.asia-northeast3.run.app \
  -H "Content-Type: application/json" \
  -d '{"test": false}'

# 테스트 모드 (실제 Slack 메시지 전송 안됨)
curl -X POST https://gowid-notification-809088966352.asia-northeast3.run.app \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

## 🔧 설정

### 환경 변수
- `SLACK_BOT_TOKEN`: Slack Bot 토큰

### 코드 내 설정
```python
SLACK_ALERT_CHANNEL_ID = "#주서희-자동화"  # 에러 알림 채널
SPREADSHEET_ID = 'your_spreadsheet_id'     # 고위드 위반내역 시트
USERMAP_SHEET_ID = 'your_usermap_id'       # 사용자 매핑 시트
```

## 📱 Slack 메시지 예시

```
*홍길동님*, 2024년 7월 고위드 법인카드 사용 내역 안내드립니다.

💸 급여에서 차감 예정 금액: *50,000원*
- 🥗 점심식비 초과: 30,000원
- 🍽 저녁식비 초과: 20,000원 (2회)
- ⚠️ 기타 위반금액: 0원
- ✋ 개인 오사용(급여 차감): 0원

🏦 개인 오사용(직접 입금): *100,000원*
반드시 개인 오사용(직접 입금) 금액만 입금 부탁드립니다.

입금 계좌: 기업은행 471-067757-04-016 주식회사 누비랩
입금 후 @담당자에게 슬랙으로 알려주세요 🙏
```

## 🛠️ 개발

### 프로젝트 구조
```
gowid_notification/
├── main.py              # 메인 애플리케이션
├── requirements.txt     # Python 의존성
├── Dockerfile          # Docker 설정
├── env.yaml           # 환경 변수 (예시)
├── key.json           # Google Cloud 서비스 계정 키
└── README.md          # 프로젝트 문서
```

### 의존성
- `gspread`: Google Sheets API 클라이언트
- `google-auth`: Google 인증
- `slack_sdk`: Slack API 클라이언트
- `flask`: 웹 프레임워크
- `gunicorn`: WSGI 서버

## 🚨 에러 처리

- Google Sheets 접근 오류 시 Slack 채널로 알림
- Slack 메시지 전송 실패 시 로그 출력
- 사용자 매핑 실패 시 경고 로그
- 전체 프로세스 오류 시 스택 트레이스와 함께 Slack 알림

## 📅 배포

### Google Cloud Run
1. Docker 이미지 빌드
2. Google Container Registry에 푸시
3. Cloud Run에 배포
4. 웹훅 URL: `https://gowid-notification-809088966352.asia-northeast3.run.app`

### Zapier 연동
1. Zapier에서 "Webhooks" 앱 선택
2. "POST" 방식으로 웹훅 설정
3. URL에 `https://gowid-notification-809088966352.asia-northeast3.run.app` 입력
4. 필요시 테스트 모드 파라미터 추가: `{"test": true}`

### 실행 방법
- **일반 실행**: Zapier 버튼 클릭
- **테스트 실행**: Zapier에서 `{"test": true}` 파라미터로 실행

## 📞 지원

문제가 발생하거나 개선 사항이 있으시면 주서희에게 문의해 주세요.

## 📄 라이선스

이 프로젝트는 내부 사용을 위한 것입니다.
