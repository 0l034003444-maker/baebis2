import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. 배비스 전용 고급 네온 앱 아이콘 생성 (SVG 데이터)
BAEBIS_ICON = """data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="%23FF2E55"/><stop offset="100%" stop-color="%230055FF"/></linearGradient></defs><rect width="512" height="512" rx="115" fill="%230B0B12"/><rect x="16" y="16" width="480" height="480" rx="100" fill="none" stroke="url(%23g)" stroke-width="20"/><circle cx="256" cy="210" r="85" fill="none" stroke="%23FF2E55" stroke-width="16"/><text x="256" y="238" font-size="85" text-anchor="middle" fill="%23FFFFFF">🎙️</text><text x="256" y="400" font-size="85" font-family="sans-serif" font-weight="900" text-anchor="middle" fill="%23FFD000">배비스</text></svg>"""

# 페이지 기본 설정 (어플 이름: 배비스, 전용 아이콘 적용)
st.set_page_config(page_title="배비스", page_icon=BAEBIS_ICON, layout="wide")

# 2. 번역 팝업 완전 차단 스크립트 + 모바일 홈 화면 아이콘 강제 지정 + 시안 UI 디자인
st.markdown(f"""
    <style>
    /* 전체 다크 테마 및 상단 여백 최소화 */
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: #0B0B12 !important;
        color: #FFFFFF !important;
    }}
    .block-container {{ padding-top: 1.5rem !important; padding-bottom: 2rem !important; }}
    header {{ visibility: hidden; }}
    
    /* 상단 타이틀 바 */
    .app-header {{
        font-size: 22px; font-weight: 800; color: #FFD000;
        text-align: center; margin-bottom: 10px; letter-spacing: -0.5px;
    }}
    
    /* 시안과 동일한 원형 네온 마이크 UI */
    .mic-wrapper {{
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        margin: 15px 0 20px 0;
    }}
    .neon-circle {{
        width: 150px; height: 150px; border-radius: 50%;
        background: radial-gradient(circle, #1A1A28 60%, #0B0B12 100%);
        border: 5px solid #FF2E55;
        box-shadow: 0 0 25px rgba(255, 46, 85, 0.6), inset 0 0 20px rgba(0, 85, 255, 0.5);
        display: flex; flex-direction: column; align-items: center; justify-content: center;
    }}
    .mic-icon {{ font-size: 46px; margin-bottom: 4px; }}
    .mic-status {{ font-size: 18px; font-weight: bold; color: #FFFFFF; }}
    
    /* 하단 음성 명령어 가이드 바 */
    .guide-bar {{
        background-color: #161622; border-radius: 30px; padding: 12px 18px;
        text-align: center; font-size: 16px; font-weight: bold; color: #E0E0E0;
        border: 1px solid #2A2A3C; margin-bottom: 15px;
    }}
    .guide-bar span {{ margin: 0 8px; }}
    
    /* 검색 결과 카드 디자인 */
    .big-card {{
        background-color: #181824; color: #FFFFFF; padding: 20px;
        border-radius: 16px; margin-bottom: 15px;
        border: 1px solid #2E2E42; border-left: 8px solid #FF2E55;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.4);
    }}
    .card-title {{ font-size: 24px; font-weight: bold; color: #FFD000; margin-bottom: 8px; }}
    .card-sub {{ font-size: 20px; color: #00FFAA; font-weight: bold; margin-bottom: 8px; }}
    .card-text {{ font-size: 20px; line-height: 1.5; color: #EAEAEA; }}
    
    /* 입력창 큼직하게 */
    div[data-testid="stTextInput"] input {{
        font-size: 20px !important; padding: 16px !important;
        background-color: #161622 !important; color: #FFFFFF !important;
        border: 2px solid #FF2E55 !important; border-radius: 12px !important;
    }}
    </style>
""", unsafe_allow_html=True)

# 브라우저 번역 팝업 차단 및 스마트폰 바탕화면 앱 이름/아이콘 강제 등록 스크립트
components.html(f"""
    <script>
    const doc = window.parent.document;
    doc.documentElement.lang = 'ko';
    doc.documentElement.setAttribute('translate', 'no');
    doc.body.classList.add('notranslate');
    
    // 번역 방지 메타 태그 추가
    let meta = doc.createElement('meta');
    meta.name = 'google';
    meta.content = 'notranslate';
    doc.head.appendChild(meta);
    
    // 모바일 홈 화면 추가 시 어플 이름 '배비스' 및 전용 아이콘 고정
    let titleMeta = doc.createElement('meta');
    titleMeta.name = 'apple-mobile-web-app-title';
    titleMeta.content = '배비스';
    doc.head.appendChild(titleMeta);
    
    let appNameMeta = doc.createElement('meta');
    appNameMeta.name = 'application-name';
    appNameMeta.content = '배비스';
    doc.head.appendChild(appNameMeta);
    
    let appleIcon = doc.createElement('link');
    appleIcon.rel = 'apple-touch-icon';
    appleIcon.href = '{BAEBIS_ICON}';
    doc.head.appendChild(appleIcon);
    </script>
""", height=0)

# 3. 음성 출력(TTS) 함수
def speak_text(text):
    js_code = f"""
        <script>
        var msg = new SpeechSynthesisUtterance("{text}");
        msg.lang = 'ko-KR';
        msg.rate = 1.15;
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(msg);
        </script>
    """
    components.html(js_code, height=0)

# 4. 데이터 불러오기 (구글 시트 연동 전에도 에러 없이 작동하도록 자동 백업 지원)
CSV_FILE = "baebis_memory.csv"

def load_data():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = None
        if "gcp_service_account" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
        elif os.path.exists("service_account.json"):
            creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
            
        if creds:
            client = gspread.authorize(creds)
            try:
                sheet = client.open("배비스").sheet1
            except:
                sheet = client.open("배달자비스").sheet1
            return pd.DataFrame(sheet.get_all_records()), sheet
    except Exception:
        pass

    # 구글 시트 연동 전이거나 실패 시 자체 메모리 파일 사용
    if not os.path.exists(CSV_FILE):
        sample_df = pd.DataFrame([
            {"구분": "픽업지", "이름": "백채김치찌개 시화공단점", "주소": "MTV 17로 23", "출입정보": "없음", "특징": "파리바게트 뒤쪽 골목, 더하운드 반달섬2 근처"},
            {"구분": "배달지", "이름": "더하운드 반달섬2", "주소": "성곡동 839-1", "출입정보": "공동현관 #1234*", "특징": "1층 화물용 엘베 타야 빠름"}
        ])
        sample_df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")
    return pd.read_csv(CSV_FILE), None

df, sheet = load_data()

# --- 메인 UI 화면 (시안 반영) ---
st.markdown('<div class="app-header">🛵 배비스 (BAEBIS) - 라이더 음성 비서</div>', unsafe_allow_html=True)

st.markdown("""
    <div class="mic-wrapper">
        <div style="font-size:18px; font-weight:bold; margin-bottom:12px;">지금 바로 말씀하세요!</div>
        <div class="neon-circle">
            <div class="mic-icon">🎙️</div>
            <div class="mic-status">듣는 중...</div>
        </div>
    </div>
    <div class="guide-bar">
        <span>🎙️ <b>기록해줘</b> [이름] [특징]</span> | 
        <span>✏️ <b>수정해줘</b> [이름] [새특징]</span> | 
        <span>❌ <b>삭제해줘</b> [이름]</span>
    </div>
""", unsafe_allow_html=True)

# 음성 명령 입력창 (타이핑 없이 키보드 마이크로 모든 작업 수행)
voice_cmd = st.text_input("🎙️ 음성 명령창 (터치 후 키보드 마이크 버튼으로 말하기)", placeholder="예: '백채김치찌개' 또는 '기록해줘 태평소국밥 비번 1234* 주차장 넓음'", label_visibility="collapsed")

if st.button("🔄 입력창 비우기 / 새로고침", use_container_width=True):
    st.rerun()

if voice_cmd:
    cmd = voice_cmd.strip()
    
    # [1] 음성으로 새 장소 기록하기
    if cmd.startswith("기록") or cmd.startswith("등록") or cmd.startswith("저장"):
        clean = cmd.replace("기록해줘", "").replace("등록해줘", "").replace("저장해줘", "").replace("기록", "").replace("등록", "").replace("저장", "").strip()
        parts = clean.split(" ")
        if len(parts) >= 2:
            name = parts[0]
            memo = " ".join(parts[1:])
            new_row = {"구분": "음성등록", "이름": name, "주소": "음성메모", "출입정보": "특징참조", "특징": memo}
            if sheet:
                sheet.append_row(list(new_row.values()))
            else:
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")
            st.success(f"✅ [기록 완료] '{name}' -> {memo}")
            speak_text(f"{name} 정보를 배비스에 기록했습니다.")
        else:
            st.warning("🎙️ 이렇게 말씀해 보세요: '기록해줘 [가게나 건물명] [비번이나 특징]'")
            speak_text("가게 이름과 특징을 함께 말씀해 주세요.")

    # [2] 음성으로 기존 장소 수정하기
    elif "수정" in cmd or "변경" in cmd:
        clean = cmd.replace("수정해줘", "").replace("변경해줘", "").replace("수정", "").replace("변경", "").strip()
        parts = clean.split(" ")
        if len(parts) >= 2:
            target = parts[0]
            new_memo = " ".join(parts[1:])
            if sheet:
                cell = sheet.find(target)
                if cell:
                    sheet.update_cell(cell.row, 5, new_memo)
                    st.success(f"✏️ [수정 완료] '{target}' -> {new_memo}")
                    speak_text(f"{target} 정보를 수정했습니다.")
                else:
                    st.warning(f"'{target}' 정보를 찾을 수 없습니다.")
            else:
                mask = df['이름'].str.contains(target, na=False)
                if mask.any():
                    df.loc[mask, '특징'] = new_memo
                    df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")
                    st.success(f"✏️ [수정 완료] '{target}' -> {new_memo}")
                    speak_text(f"{target} 정보를 수정했습니다.")
                else:
                    st.warning(f"'{target}' 정보를 찾을 수 없습니다.")

    # [3] 음성으로 장소 삭제하기
    elif "삭제" in cmd or "지워" in cmd:
        target = cmd.replace("삭제해줘", "").replace("지워줘", "").replace("삭제", "").replace("지워", "").strip()
        if target:
            if sheet:
                cells = sheet.findall(target)
                if cells:
                    for cell in reversed(cells):
                        sheet.delete_rows(cell.row)
                    st.success(f"❌ [삭제 완료] '{target}' 정보를 지웠습니다.")
                    speak_text(f"{target} 정보를 삭제했습니다.")
                else:
                    st.warning(f"'{target}' 정보를 찾을 수 없습니다.")
            else:
                mask = df['이름'].str.contains(target, na=False)
                if mask.any():
                    df = df[~mask]
                    df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")
                    st.success(f"❌ [삭제 완료] '{target}' 정보를 지웠습니다.")
                    speak_text(f"{target} 정보를 삭제했습니다.")
                else:
                    st.warning(f"'{target}' 정보를 찾을 수 없습니다.")

    # [4] 기본 음성 검색
    else:
        query = cmd.replace("특징 알려줘", "").replace("알려줘", "").replace("찾아줘", "").replace("검색", "").replace(" ", "")
        mask = df.apply(lambda r: query in str(r['이름']).replace(" ", "") or query in str(r['주소']).replace(" ", "") or query in str(r['특징']).replace(" ", ""), axis=1)
        results = df[mask]
        
        if not results.empty:
            tts_list = []
            for _, row in results.iterrows():
                st.markdown(f"""
                <div class="big-card">
                    <div class="card-title">[{row['구분']}] {row['이름']}</div>
                    <div class="card-sub">🔑 출입/비번: {row['출입정보']}</div>
                    <div class="card-text">📍 <b>주소:</b> {row['주소']}</div>
                    <div class="card-text">💡 <b>특징:</b> {row['특징']}</div>
                </div>
                """, unsafe_allow_html=True)
                tts_list.append(f"{row['이름']}. 출입정보 {row['출입정보']}. 특징은 {row['특징']} 입니다.")
            speak_text(" ".join(tts_list))
        else:
            st.warning(f"'{cmd}'에 대한 기억이 없습니다. '기록해줘 {cmd} [특징]'이라고 말해서 바로 등록해 보세요!")
            speak_text(f"{cmd} 정보가 없습니다.")

with st.expander("📋 배비스 전체 기억 목록 보기"):
    st.dataframe(df, use_container_width=True)