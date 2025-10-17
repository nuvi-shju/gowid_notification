import os
import traceback
import logging
import datetime
import gspread
from google.auth import default
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# ==== 슬랙 알림 채널 ====
SLACK_ALERT_CHANNEL_ID = "#주서희-자동화"

# ==== 설정 ====
SPREADSHEET_ID = '1eVcUubguFBPvXn5jUQDoRIbGPyk1NycgDP9txj1iIFo'  # 고위드 위반내역
USERMAP_SHEET_ID = '1IwdHNEywDtFyvBzh-bHBcnHiNF1aGb3aoL0fDFgYLlo'  # 사용자 매핑 시트
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# ==== 인증 ====
credentials, _ = default(scopes=SCOPES)
gc = gspread.authorize(credentials)
slack_token = os.environ.get('SLACK_BOT_TOKEN')
slack_client = WebClient(token=slack_token)

# ==== Slack 사용자 매핑 ====
def load_user_map():
    sh = gc.open_by_key(USERMAP_SHEET_ID)
    ws = sh.sheet1
    data = ws.get_all_records()
    return {row['이름']: row['Slack ID'] for row in data}

# ==== Slack DM 발송 ====
def send_slack_dm(user_id, message, channel=False):
    try:
        if channel:
            slack_client.chat_postMessage(channel=user_id, text=message)
            print(f"[✓] 채널 메시지 전송 완료: {user_id}")
        else:
            slack_client.chat_postMessage(channel=user_id, text=message)
            print(f"[✓] DM 전송 완료: {user_id}")
    except SlackApiError as e:
        print(f"[X] Slack 메시지 전송 실패 ({user_id}): {e.response['error']}")

# ==== 메인 ====
def main(payload={}):
    try:
        print("[로그] 고위드 알림 처리 시작합니다.")
        is_test = payload.get('test') in ['true', True, 'True']
        print(f"[로그] 테스트 모드 여부: {is_test}")

        if is_test:
            print("[TEST MODE] Slack 메시지는 전송되지 않습니다.")
            return "✅ 테스트 성공 (Slack 메시지 전송 안 됨)"

        print(f"DEBUG: SLACK_BOT_TOKEN = {slack_token}")
        # 1. 날짜 계산
        today = datetime.datetime.now().replace(day=1) - datetime.timedelta(days=1)
        ym = today.strftime('%Y%m')  # e.g., '202507'
        print(f"[로그] 이번에 처리할 대상 월은 {ym} 입니다.")

        # 2. 슬랙 사용자 맵 불러오기
        user_map = load_user_map()
        print(f"[로그] 사용자 매핑 데이터 {len(user_map)}명 로드 완료")

        # 3. 위반내역 시트 열기
        try:
            sh = gc.open_by_key(SPREADSHEET_ID)
            ws = sh.worksheet(ym)
            print(f"[로그] 스프레드시트 '{ym}' 시트 열기 성공")
        except:
            msg = f"[!] {ym} 시트 없음"
            print(msg)
            send_slack_dm(SLACK_ALERT_CHANNEL_ID, msg, channel=True)
            return msg

        data = ws.get_all_records()  # 리스트[dict]
        print(f"[로그] 총 {len(data)}개의 위반내역 데이터 로드 완료")

        for row in data:
            name = row.get('소지자')
            total_deduction = row.get('공제 총액', 0)
            direct_payment = row.get('직접 입금 금액', 0)
            # Extract violation fields
            lunch_violation = row.get('점심 위반금액', 0)
            dinner_violation = row.get('저녁 위반금액', 0)
            dinner_count = row.get('저녁 위반건수', 0)
            misuse_violation = row.get('개인오사용금액', 0)
            other_violation = row.get('기타 위반금액', 0)

            if not name:
                print("[로그] 이름 정보 없음, 해당 행 건너뜀")
                continue
            print(f"[로그] {name} 데이터 처리 중...")

            if (total_deduction is None or total_deduction == 0) and (direct_payment is None or direct_payment == 0):
                print(f"[로그] {name} 공제 총액 및 직접 입금 금액 모두 0, 건너뜀")
                continue

            msg = f"*{name}님*, {ym[:4]}년 {int(ym[4:])}월 고위드 법인카드 사용 내역 안내드립니다.\n\n"
            if total_deduction:
                msg += f"💸 급여에서 차감 예정 금액: *{total_deduction:,}원*\n"
                msg += f"- 🥗 점심식비 초과: {lunch_violation:,}원\n"
                msg += f"- 🍽 저녁식비 초과: {dinner_violation:,}원 ({dinner_count}회)\n"
                msg += f"- ⚠️ 기타 위반금액: {other_violation:,}원\n"
                msg += f"- ✋ 개인 오사용(급여 차감): {misuse_violation:,}원\n\n"
            if direct_payment:
                msg += f"🏦 개인 오사용(직접 입금): *{direct_payment:,}원*\n"
                msg += "반드시 개인 오사용(직접 입금) 금액만 입금 부탁드립니다.\n\n"
                msg += "입금 계좌: 기업은행 471-067757-04-016 주식회사 누비랩\n"
                msg += "입금 후 *<@U09541PAMN1>*에게 슬랙으로 알려주세요 🙏"

            slack_id = user_map.get(name)
            if slack_id:
                send_slack_dm(slack_id, msg)
                print(f"[로그] {name}님께 Slack DM 전송 완료")
            else:
                print(f"[경고] Slack ID를 찾지 못했습니다: {name}")
        # Slack 알림 채널에 완료 메시지 전송
        send_slack_dm(SLACK_ALERT_CHANNEL_ID, f"{ym} Slack 알림 전송 완료 ✅", channel=True)
        print("[로그] 모든 알림 전송 완료")
        return 'Slack 알림 전송 완료'
    except Exception as e:
        error_message = traceback.format_exc()
        print(error_message)
        send_slack_dm(SLACK_ALERT_CHANNEL_ID, error_message, channel=True)
        return f"오류 발생: {str(e)}"


# Flask entrypoint for Cloud Run HTTP requests
from flask import Flask, request

app = Flask(__name__)

@app.route("/", methods=["POST", "GET"])
def entrypoint():
    if request.is_json:
        payload = request.get_json(silent=True) or {}
    else:
        payload = request.form.to_dict()
    return main(payload)

if __name__ == "__main__":
    main({"test": False})