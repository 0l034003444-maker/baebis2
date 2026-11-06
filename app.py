import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. 갤럭시 폴드5 맞춤형 페이지 설정
st.set_page_config(page_title="배비스", page_icon="🛵", layout="wide")

# 장갑 끼고도 누르기 편한 큼직한 UI 및 다크/고대비 카드 스타일
st.markdown("""
    <style>
    .big-card {
        background-color: #1E1E2E;
        color: #FFFFFF;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        border-left: 8px solid #FF4B4B;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
    }
    .card-title { font-size: 26px; font-weight: bold; color: #FFD700; margin-bottom: 8px; }
    .card-sub { font-size: 20px; color: #00FFAA; font-weight: bold; margin-bottom: 8px; }
    .card-text { font-size: 22px; line-height: 1.5; color: #FFFFFF; }
    div[data-testid="stTextInput"] input { font-size: 22px !important; padding: 15px !important; }
    </style>
""", unsafe_allow_html=True)

# 2. 스마트폰/헬멧 블루투스 음성 출력(TTS) 함수 (자바스크립트 내장 API 활용)
def speak_text(text):
    js_code = f"""
        <script>
        var msg = new SpeechSynthesisUtterance("{text}");
        msg.lang = 'ko-KR';
        msg.rate = 1.1; // 배달 중 빠르게 듣기 위해 1.1배속 설정
        window.speechSynthesis.cancel(); // 이전 음성 취소 후 즉시 재생
        window.speechSynthesis.speak(msg);
        </script>
    """
    components.html(js_code, height=0)

# 3. 데이터 불러오기 (구글 시트 연동 또는 로컬 CSV 백업)
CSV_FILE = "delivery_memory.csv"

def load_data():
    # 구글 시트 API 키(service_account.json)가 같은 폴더에 있으면 구글 시트 연동
    if os.path.exists("service_account.json"):
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("배달자비스").sheet1 # 구글 시트 파일명: '배달자비스'
        data = sheet.get_all_records()
        return pd.DataFrame(data), sheet
    else:
        # API 키가 아직 없을 때 바로 테스트할 수 있도록 로컬 파일 생성 및 로드
        if not os.path.exists(CSV_FILE):
            sample_data = pd.DataFrame([
                {"구분": "픽업지", "이름": "백채김치찌개 시화공단점", "주소": "MTV 17로 23 107호", "출입정보": "없음", "특징": "파리바게트 뒤쪽 골목, 더하운드 반달섬2 근처"},
                {"구분": "배달지", "이름": "더하운드 반달섬2", "주소": "성곡동 839-1", "출입정보": "공동현관 #1234*", "특징": "화물용 엘베 타야 빠름, 1층 입구 우측"}
            ])
            sample_data.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")
        return pd.read_csv(CSV_FILE), None

def save_new_row(new_row, df, sheet):
    if sheet:
        sheet.append_row(list(new_row.values()))
    else:
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")

df, sheet = load_data()

# --- 메인 화면 구성 ---
st.title("🛵 배달 비서 배비스")

tab1, tab2, tab3 = st.tabs(["🎙️ 즉시 검색", "➕ 새 장소 기억하기", "📋 전체 목록"])

with tab1:
    st.caption("입력창을 누르고 갤럭시 키보드의 [🎙️마이크] 버튼으로 가게명이나 건물명을 말하세요.")
    
    # 검색어 입력 (음성 자판 연동에 최적화)
    query = st.text_input("어디를 찾으시나요?", placeholder="예: 백채김치찌개, 반달섬, 파리바게트...")
    
    col_opt1, col_opt2 = st.columns([1, 1])
    with col_opt1:
        tts_enabled = st.checkbox("🔊 검색 결과 음성으로 자동 읽어주기", value=True)
    with col_opt2:
        if st.button("🔄 검색창 비우기", use_container_width=True):
            st.rerun()

    if query:
        # 공백을 제거하고 이름, 주소, 특징 모든 열에서 유연하게 검색
        clean_query = query.replace(" ", "")
        mask = df.apply(lambda row: clean_query in str(row['이름']).replace(" ", "") 
                                 or clean_query in str(row['주소']).replace(" ", "") 
                                 or clean_query in str(row['특징']).replace(" ", ""), axis=1)
        results = df[mask]

        if not results.empty:
            tts_sentences = []
            for _, row in results.iterrows():
                st.markdown(f"""
                <div class="big-card">
                    <div class="card-title">[{row['구분']}] {row['이름']}</div>
                    <div class="card-sub">🔑 출입/비번: {row['출입정보']}</div>
                    <div class="card-text">📍 <b>주소:</b> {row['주소']}</div>
                    <div class="card-text">💡 <b>특징:</b> {row['특징']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # 음성 안내용 문장 생성
                tts_sentences.append(f"{row['이름']}. 출입정보는 {row['출입정보']}. 특징은 {row['특징']} 입니다.")
            
            if tts_enabled:
                speak_text(" ".join(tts_sentences))
        else:
            st.warning(f"'{query}'에 대한 기억이 없습니다. [새 장소 기억하기] 탭에서 추가해 주세요.")
            if tts_enabled:
                speak_text(f"{query}에 대한 정보가 없습니다.")

with tab2:
    st.subheader("현장에서 새 정보 바로 기록")
    with st.form("add_form", clear_on_submit=True):
        category = st.radio("구분", ["픽업지(가게)", "배달지(건물/아파트)"], horizontal=True)
        name = st.text_input("가게명 또는 건물명 (필수)")
        door_code = st.text_input("공동현관 비밀번호 / 출입 팁", placeholder="예: 종 누르고 2580*, 경비실 호출")
        address = st.text_input("주소 또는 위치 단서", placeholder="예: 성곡동 123, OO사거리 코너")
        memo = st.text_area("기억할 특징 (입구 위치, 주차, 엘리베이터 등)", placeholder="예: 정문 막혀있음, 뒷골목 1층 쪽문 진입")
        
        submitted = st.form_submit_button("💾 자비스에 기억시키기", use_container_width=True)
        if submitted and name:
            new_data = {
                "구분": "픽업지" if "픽업지" in category else "배달지",
                "이름": name,
                "주소": address if address else "미입력",
                "출입정보": door_code if door_code else "없음",
                "특징": memo if memo else "없음"
            }
            save_new_row(new_data, df, sheet)
            st.success(f"✅ '{name}' 정보가 저장되었습니다!")
            speak_text(f"{name} 정보를 기억했습니다.")
            st.rerun()

with tab3:
    st.dataframe(df, use_container_width=True)