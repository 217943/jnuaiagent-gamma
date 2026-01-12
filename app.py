import streamlit as st
import google.generativeai as genai
import json
import uuid
import pandas as pd
from datetime import datetime
import utils

# --- [설정 및 상수 정의] ---
st.set_page_config(page_title="교육혁신본부 AI 클리닉", layout="wide")

# 튜터/컨설턴트 명단 (가상 ID 부여)
TUTORS = [f"튜터-{i:02d} (학생)" for i in range(1, 11)]  # 튜터-01 ~ 튜터-10
CONSULTANTS = [f"컨설턴트-{i:02d} (전문)" for i in range(1, 11)] # 컨설턴트-01 ~ 컨설턴트-10

# Gemini 설정
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel(
        'models/gemini-2.5-flash',
        generation_config={"response_mime_type": "application/json"}
    )
except Exception as e:
    st.error(f"API 키 설정 오류: {e}")

# --- [메인 앱 로직] ---
st.sidebar.title("🎓 교육혁신본부 AI 클리닉")
st.sidebar.markdown("---")
app_mode = st.sidebar.radio("메뉴 선택", ["상담 신청하기", "관리자 대시보드"])

# ==========================================
# 1. 상담 신청 페이지 (User)
# ==========================================
if app_mode == "상담 신청하기":
    st.title("📝 AI 활용 클리닉 상담 신청")
    st.markdown("AI 활용 관련 문의를 남겨주세요. AI 에이전트가 분석 후 적임자에게 배정해 드립니다.")
    
    with st.form("request_form"):
        col1, col2 = st.columns(2)
        role = col1.selectbox("신분", ["교수", "직원", "학생", "조교/연구원"])
        dept = col2.text_input("소속", placeholder="예: 교육학과")
        query = st.text_area("상담 요청 내용", height=150, 
                             placeholder="예: 논문 데이터 분석에 사용할 프롬프트를 짜고 싶습니다.")
        
        submitted = st.form_submit_button("🚀 상담 신청하기")
        
        if submitted and query:
            with st.spinner("Gemini 2.5가 내용을 분석 중입니다..."):
                # 프롬프트: 카테고리(튜터vs컨설턴트)만 추천받음
                prompt = f"""
                당신은 대학 AI 클리닉 분류 담당자입니다. 
                아래 내용을 분석하여 JSON으로 응답하세요.
                
                [입력] 신분: {role}, 문의: {query}
                
                [기준]
                - L0~L1 (기초): assignee_group = "TUTOR"
                - L2~L3 (심화): assignee_group = "CONSULTANT"
                
                [출력 JSON]
                {{
                    "summary": "1줄 요약",
                    "difficulty": "L0/L1/L2/L3",
                    "assignee_group": "TUTOR 또는 CONSULTANT",
                    "reason": "판단 이유",
                    "privacy_risk": "개인정보 포함 여부(있음/없음)"
                }}
                """
                try:
                    response = model.generate_content(prompt)
                    ai_result = json.loads(response.text)
                    
                    new_request = {
                        "id": str(uuid.uuid4()),
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "user_info": {"role": role, "dept": dept},
                        "query": query,
                        "ai_analysis": ai_result,
                        "status": "pending",
                        "final_assignee": None # 아직 배정 안됨
                    }
                    
                    current_data = utils.load_data()
                    current_data.append(new_request)
                    utils.save_data(current_data, f"New request from {role}")
                    
                    st.success("✅ 신청 완료! 담당자가 곧 배정됩니다.")
                    with st.expander("내 문의 분석 결과"):
                        st.json(ai_result)
                        
                except Exception as e:
                    st.error(f"오류 발생: {e}")

# ==========================================
# 2. 관리자 대시보드 (Admin)
# ==========================================
elif app_mode == "관리자 대시보드":
    st.title("👨‍💻 관리자 및 배정 시스템")
    
    password = st.sidebar.text_input("관리자 비밀번호", type="password")
    if password == st.secrets["ADMIN_PASSWORD"]:
        
        # 데이터 로드
        if st.button("🔄 데이터 새로고침"):
            st.rerun()
        raw_data = utils.load_data()
        
        # 탭 분리: 할 일(Pending) vs 한 일(History)
        tab1, tab2 = st.tabs(["🔥 미처리 대기", "✅ 처리 완료 내역"])
        
        # --- [Tab 1] 미처리 대기 목록 ---
        with tab1:
            pending_list = [d for d in raw_data if d['status'] == 'pending']
            st.metric("처리 대기", f"{len(pending_list)}건")
            
            if not pending_list:
                st.info("현재 대기 중인 상담 건이 없습니다. (휴식 시간! ☕)")
            
            for req in pending_list:
                with st.container(border=True):
                    c1, c2 = st.columns([7, 3])
                    
                    # AI 분석 정보
                    with c1:
                        diff = req['ai_analysis']['difficulty']
                        role = req['user_info']['role']
                        dept = req['user_info']['dept']
                        color = "blue" if diff in ["L0", "L1"] else "red"
                        
                        st.markdown(f"#### :{color}[{diff}] {role} ({dept})")
                        st.write(f"**문의:** {req['query']}")
                        st.caption(f"🤖 AI 의견: {req['ai_analysis']['reason']}")
                        
                        if req['ai_analysis'].get('privacy_risk') == "있음":
                            st.error("🚨 개인정보 포함 주의")

                    # 배정 컨트롤러
                    with c2:
                        st.write("**담당자 배정**")
                        
                        # AI 추천에 따라 드롭다운 목록 자동 변경
                        ai_group = req['ai_analysis'].get('assignee_group', 'TUTOR')
                        if ai_group == 'CONSULTANT':
                            options = CONSULTANTS + TUTORS # 컨설턴트 우선 표시
                            idx = 0
                        else:
                            options = TUTORS + CONSULTANTS # 튜터 우선 표시
                            idx = 0
                            
                        # 구체적인 ID 선택 (예: 튜터-03)
                        selected_person = st.selectbox(
                            f"추천: {ai_group}", 
                            options, 
                            key=f"sel_{req['id']}"
                        )
                        
                        if st.button("승인 및 배정", key=f"btn_{req['id']}", type="primary"):
                            # 상태 업데이트
                            for d in raw_data:
                                if d['id'] == req['id']:
                                    d['status'] = 'approved'
                                    d['final_assignee'] = selected_person
                                    d['approved_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    break
                            
                            utils.save_data(raw_data, f"Assigned {req['id']} to {selected_person}")
                            st.toast(f"{selected_person}에게 배정 완료!")
                            st.rerun()

        # --- [Tab 2] 처리 완료 내역 (대시보드) ---
        with tab2:
            approved_list = [d for d in raw_data if d['status'] == 'approved']
            st.metric("누적 처리 완료", f"{len(approved_list)}건")
            
            if approved_list:
                # 데이터프레임 변환 (보기 좋게 가공)
                df = pd.DataFrame(approved_list)
                
                # 필요한 컬럼만 추출 및 이름 변경
                display_df = pd.DataFrame({
                    "신청일시": df['timestamp'],
                    "신분": df['user_info'].apply(lambda x: x['role']),
                    "소속": df['user_info'].apply(lambda x: x['dept']),
                    "난이도": df['ai_analysis'].apply(lambda x: x['difficulty']),
                    "문의요약": df['ai_analysis'].apply(lambda x: x.get('summary', '-')),
                    "담당자": df['final_assignee'],
                    "처리일시": df.get('approved_at', '-')
                })
                
                # 필터링 기능
                st.markdown("### 📊 상담 내역 검색")
                search_assignee = st.multiselect("담당자별 필터", options=(TUTORS + CONSULTANTS))
                
                if search_assignee:
                    display_df = display_df[display_df['담당자'].isin(search_assignee)]
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # 간단한 통계 차트 (선택사항)
                if not display_df.empty:
                    st.markdown("### 📈 배정 현황")
                    count_chart = display_df['담당자'].value_counts()
                    st.bar_chart(count_chart)
            else:
                st.info("아직 처리 완료된 내역이 없습니다.")

    elif password:
        st.error("비밀번호가 틀렸습니다.")