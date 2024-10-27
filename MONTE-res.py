import streamlit as st
import pandas as pd
from datetime import datetime, time
import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect('reservations.db')
cursor = conn.cursor()

# 테이블 생성
cursor.execute('''
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    time TEXT UNIQUE,
    name TEXT,
    phone TEXT
)
''')
conn.commit()

# 마지막 리셋 날짜를 저장하는 테이블
cursor.execute('''
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY,
    last_reset DATE
)
''')
conn.commit()

def add_reservation(time, name, phone):
    cursor.execute("INSERT INTO reservations (time, name, phone) VALUES (?, ?, ?)", (time, name, phone))
    conn.commit()

def get_reservations():
    cursor.execute("SELECT time, name, phone FROM reservations")
    return cursor.fetchall()

def delete_reservation(time):
    cursor.execute("DELETE FROM reservations WHERE time = ?", (time,))
    conn.commit()

def check_and_reset_reservations():
    # 마지막 리셋 날짜 가져오기
    cursor.execute("SELECT last_reset FROM settings WHERE id = 1")
    row = cursor.fetchone()

    # 현재 날짜
    today = datetime.now().date()

    if row is None:
        # 초기 상태, 첫 리셋
        cursor.execute("INSERT INTO settings (id, last_reset) VALUES (1, ?)", (today,))
        conn.commit()
    else:
        last_reset = row[0]
        last_reset_date = datetime.strptime(last_reset, "%Y-%m-%d").date()  # 문자열을 date 객체로 변환

        # 하루가 지났는지 확인
        if today > last_reset_date:
            cursor.execute("DELETE FROM reservations")  # 예약 삭제
            cursor.execute("UPDATE settings SET last_reset = ?", (today,))
            conn.commit()
            st.session_state.reserved_times = []  # 세션 상태 초기화
            st.success("모든 예약이 초기화되었습니다.")

# 페이지 설정
st.set_page_config(page_title="MONTE 예약 시스템", page_icon="/Users/leewsung/Streamlit-Res_sys/monte_icon1.png")

# 예약 초기화 체크
check_and_reset_reservations()

# 현재 날짜 표시
now = datetime.now()
today = now.date()

# 시간대 생성 (오전 11시부터 오후 5시까지 1시간 단위)
time_slots = [time(hour=h) for h in range(11, 18)]
time_slots_str = [f"{time_slot.strftime('%H:%M')}" for time_slot in time_slots]

# 비밀번호 설정
PASSWORD = "smedu-8049"

# 사이드바 선택기
st.sidebar.title("메뉴")
page = st.sidebar.radio("페이지 선택", ["예약하기", "일정 관리"])

# 예약 상태를 세션 상태에 저장
if "reserved_times" not in st.session_state:
    st.session_state.reserved_times = []

if page == "예약하기":
    # 예약하기 페이지
    st.title("🐶 MONTE 셀프 목욕 예약 🛀")
    st.text("* 일반셀프목욕 15,000원/1시간 ")
    st.text("* 몬테 매장 이용고객 5,000원/1시간")
    st.text("애견셀프목욕의 최대 이용시간은 1시간입니다.")
    st.subheader(f"오늘의 날짜: {today}")
    
    user_name = st.text_input("반려견의 견종과 이름을 기재해주세요! (ex.푸들/가을이)")
    user_phone = st.text_input("전화번호를 입력해주세요!")

    st.warning("🔔 전화번호는 오로지 예약 문자 발송 목적으로만 사용됩니다.")
    
    st.subheader("예약 가능 시간대 : ")

    # 버튼을 가로로 배치하기 위해 열 생성
    cols = st.columns(len(time_slots_str))

    # 데이터베이스에서 예약 확인
    reservations = get_reservations()
    reserved_times = [res[0] for res in reservations]

    # 동일한 이름과 전화번호를 가진 예약 확인
    duplicate_reservation = any(res[1] == user_name and res[2] == user_phone for res in reservations)

    for i, time_str in enumerate(time_slots_str):
        if time_str in reserved_times or time_str in st.session_state.reserved_times:
            with cols[i]:
                st.button(f"[{time_str}]", disabled=True, key=f"disabled_{time_str}")  # 불가능한 시간
        else:
            with cols[i]:
                if st.button(f"[{time_str}]", key=f"available_{time_str}_{i}"):  # 가능한 시간
                    if user_name and user_phone:
                        if duplicate_reservation:
                            st.warning("같은 이름과 전화번호로 이미 예약이 있습니다.")
                        else:
                            add_reservation(time_str, user_name, user_phone)  # DB에 예약 추가
                            st.session_state.reserved_times.append(time_str)  # 예약 시간 추가
                            st.success(f"{user_name}님이 {time_str}로 예약이 완료되었습니다!")
                    else:
                        st.warning("이름과 전화번호를 입력해 주세요.")

elif page == "일정 관리":
    # 일정 관리 페이지
    st.title("일정 관리 시스템")
    password = st.text_input("비밀번호를 입력하세요:", type="password")

    if st.button("확인"):
        if password == PASSWORD:
            st.session_state.is_authenticated = True
        else:
            st.error("비밀번호가 틀렸습니다.")

    if st.session_state.get("is_authenticated", False):
        # 데이터베이스에서 예약 목록 조회
        reservations = get_reservations()

        # 예약 목록 표시
        st.subheader("현재 예약된 일정")
        if reservations:
            for time_str, name, phone in reservations:
                st.write(f"{time_str}: {name} ({phone})")
            
            # 특정 시간대 예약 삭제 기능
            st.subheader("예약 삭제")
            time_to_delete = st.selectbox("삭제할 예약 시간을 선택하세요:", [res[0] for res in reservations])
            if st.button("예약 삭제"):
                delete_reservation(time_to_delete)
                st.session_state.reserved_times.remove(time_to_delete)  # 예약 시간 세션 상태에서 제거
                st.success(f"{time_to_delete} 예약이 삭제되었습니다.")
        else:
            st.write("현재 예약된 일정이 없습니다.")

        # 예약 목록 차트 생성
        availability = {time_str: "가능" for time_str in time_slots_str}
        for reserved in [res[0] for res in reservations]:
            availability[reserved] = "불가능"

        # DataFrame 생성
        df = pd.DataFrame(list(availability.items()), columns=["시간", "상태"])
        df['상태'] = df['상태'].map({"가능": 1, "불가능": 0})

        # 차트 표시
        st.bar_chart(df.set_index("시간")['상태'])

        # 리셋 버튼
        if st.button("리셋"):
            cursor.execute("DELETE FROM reservations")  # DB에서 모든 예약 삭제
            conn.commit()
            st.session_state.is_authenticated = False  # 인증 상태 초기화
            st.session_state.reserved_times = []  # 예약 시간 초기화
            st.success("모든 예약이 초기화되었습니다.")

        # 나가기 버튼
        if st.button("나가기"):
            st.session_state.is_authenticated = False  # 인증 상태 초기화
            st.success("예약하기 페이지로 이동합니다.")

    else:
        st.info("비밀번호를 입력하여 일정 관리 시스템에 접근하세요.")

# 앱 종료 시 연결 닫기
conn.close()
