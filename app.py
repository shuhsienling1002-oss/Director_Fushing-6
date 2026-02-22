import streamlit as st
import datetime
import sqlite3
import pandas as pd

DB_NAME = 'fuxing_guardian_v5.db'

# ==========================================
# 🛡️ 系統底層：防禦性資料庫與自動計算引擎
# ==========================================
def init_db():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS health_logs (
                    date TEXT PRIMARY KEY,
                    actual_age INTEGER, body_age INTEGER,
                    visceral_fat REAL, muscle_mass REAL, bmi REAL,
                    resting_hr INTEGER, blood_pressure TEXT,
                    readiness_score INTEGER, social_mode_active BOOLEAN,
                    micro_workouts_done INTEGER, water_intake_cc INTEGER
                )
            ''')
            conn.commit()
    except Exception as e:
        st.error("🚨 系統啟動失敗：資料庫初始化異常。已啟動降級模式。")

def check_red_flag(bp_sys, hr):
    """🩺 絕對阻斷原則：紅旗指標檢測"""
    if bp_sys >= 160 or hr >= 100:
        return True
    return False

def calculate_readiness(vf, hr, bp_sys, body_age, actual_age, social_mode, micro_workouts, water_intake, water_goal):
    base_score = 100
    if vf > 10: base_score -= (vf - 10) * 1.5 
    if hr > 65: base_score -= (hr - 65) * 2
    if bp_sys > 130: base_score -= (bp_sys - 130) * 1 
    
    age_gap = body_age - actual_age
    if age_gap > 0: base_score -= age_gap * 1
    if social_mode: base_score -= 20
    
    base_score += (micro_workouts * 3)
    if water_intake >= water_goal: base_score += 5 
        
    return max(0, min(100, int(base_score)))

def load_history():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            query = """
                SELECT date, actual_age, body_age, visceral_fat, muscle_mass, 
                       bmi, resting_hr, blood_pressure, readiness_score, 
                       social_mode_active, micro_workouts_done, water_intake_cc 
                FROM health_logs ORDER BY date DESC
            """
            df = pd.read_sql_query(query, conn)
            return df
    except Exception:
        return pd.DataFrame()

# ==========================================
# 🧠 狀態機與預言機初始化
# ==========================================
st.set_page_config(page_title="復興守護者 v9", page_icon="🛡️", layout="wide")
init_db()

today_str = datetime.date.today().strftime("%Y-%m-%d")
is_weekend = datetime.date.today().weekday() >= 5 

if 'social_mode' not in st.session_state: st.session_state.social_mode = False
if 'metrics' not in st.session_state: 
    st.session_state.metrics = {
        'actual_age': 54, 'body_age': 69, 'vf': 25.0, 'muscle': 26.7, 
        'bmi': 33.8, 'hr': 63, 'bp_sys': 119, 'bp_dia': 79
    }
if 'micro_workouts' not in st.session_state: st.session_state.micro_workouts = 0 
if 'water_intake' not in st.session_state: st.session_state.water_intake = 0 

water_goal = 3000 if st.session_state.social_mode else 2000
has_red_flag = check_red_flag(st.session_state.metrics['bp_sys'], st.session_state.metrics['hr'])

st.session_state.readiness_score = calculate_readiness(
    st.session_state.metrics['vf'], st.session_state.metrics['hr'], st.session_state.metrics['bp_sys'], 
    st.session_state.metrics['body_age'], st.session_state.metrics['actual_age'],
    st.session_state.social_mode, st.session_state.micro_workouts, st.session_state.water_intake, water_goal
)

# ==========================================
# 🎨 介面層：決策校準與視覺交互
# ==========================================
st.title("🛡️ 復興守護者")
st.markdown(f"**早安。今天是 {today_str} {'(週末重置日)' if is_weekend else '(市政高壓期)'}**")

if has_red_flag:
    st.error("🚨 **【Tier 4 紅旗警報】** 檢測到心血管壓力過載 (收縮壓或心率異常)。系統已強制切斷所有主動訓練權限，請立即啟動靜養安全模式！")

# --- 📥 數值輸入區 (隱藏次要資訊，降低認知負擔) ---
with st.expander("📥 更新今日最新數值", expanded=False):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        new_actual_age = st.number_input("實際年齡", value=st.session_state.metrics['actual_age'])
        new_vf = st.number_input("內臟脂肪", value=st.session_state.metrics['vf'], step=0.5)
        new_bp_sys = st.number_input("收縮壓", value=st.session_state.metrics['bp_sys'])
    with col_b:
        new_body_age = st.number_input("身體年齡", value=st.session_state.metrics['body_age'])
        new_muscle = st.number_input("骨骼肌率", value=st.session_state.metrics['muscle'], step=0.1)
        new_bp_dia = st.number_input("舒張壓", value=st.session_state.metrics['bp_dia'])
    with col_c:
        new_bmi = st.number_input("BMI", value=st.session_state.metrics['bmi'], step=0.1)
        new_hr = st.number_input("安靜心率", value=st.session_state.metrics['hr'])
        
    if st.button("🔄 校準並更新數值", use_container_width=True):
        st.session_state.metrics.update({
            'actual_age': new_actual_age, 'body_age': new_body_age, 'vf': new_vf, 
            'muscle': new_muscle, 'bmi': new_bmi, 'hr': new_hr, 'bp_sys': new_bp_sys, 'bp_dia': new_bp_dia
        })
        st.rerun()

st.divider()

# --- 🔋 儀表板 ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("代謝綜合評分", f"{st.session_state.readiness_score}%", "穩定" if st.session_state.readiness_score >= 70 else "- 負載過重", delta_color="inverse" if st.session_state.readiness_score < 70 else "normal")
with col2:
    st.metric("血壓監測", f"{st.session_state.metrics['bp_sys']}/{st.session_state.metrics['bp_dia']}", "高危" if has_red_flag else "正常", delta_color="inverse")
with col3:
    age_gap = st.session_state.metrics['body_age'] - st.session_state.metrics['actual_age']
    st.metric("身體年齡", f"{st.session_state.metrics['body_age']} 歲", f"{'+' if age_gap > 0 else ''}{age_gap} 歲", delta_color="inverse")

st.divider()


# --- 擴充模組整合區 (結合降維退階) ---
if has_red_flag:
    st.warning("🛏️ **安全模式 (Safe Mode) 已啟動**：請執行 5 分鐘橫膈膜深呼吸，禁止任何阻力訓練。")
elif is_weekend:
    st.subheader("🌲 週末重置協議")
    st.checkbox("14小時微斷食：清空胰島素。")
    st.checkbox("大自然重置：30 分鐘漫步。")
else:
    st.subheader("⏱️ 零碎時間微訓練")
    if st.session_state.social_mode:
        st.info("🍷 **應酬降載模式**：檢測到肝臟負載中。建議將訓練降維至「3分鐘辦公椅深蹲」或純粹拉伸。")
        workouts = ["3 分鐘 (降維伸展)"]
    else:
        workouts = ["3 分鐘", "10 分鐘", "15 分鐘"]
        
    available_time = st.radio("目前空檔：", workouts, horizontal=True)
    if st.button("✅ 執行微訓練 (+3分)"):
        st.session_state.micro_workouts += 1
        st.toast("⚡ 神經連結強化！完成一次微訓練。", icon="🚀")
        st.rerun()

st.divider()

# --- 💧 動態水杯 ---
st.subheader(f"💧 喝水 (目標: {water_goal} cc)")
st.progress(min(st.session_state.water_intake / water_goal, 1.0))
col_w1, col_w2 = st.columns(2)
with col_w1:
    if st.button("➕ 喝一杯 (250cc)", use_container_width=True):
        st.session_state.water_intake += 250
        st.rerun()
with col_w2:
    if st.button("➕ 喝一瓶 (500cc)", use_container_width=True):
        st.session_state.water_intake += 500
        st.rerun()

st.divider()

# --- 🗓️ 應酬防禦與酒精衝擊 ---
if st.session_state.social_mode:
    st.error("🚨 **酒精衝擊警報**：燃脂已停滯。請嚴守 1:1 水分法則。")
    if st.button("✅ 應酬結束 (啟動 14H 排毒)"):
        st.session_state.social_mode = False
        st.rerun()
else:
    if st.button("🍷 臨時追加應酬 (啟動防禦)", use_container_width=True):
        st.session_state.social_mode = True
        st.rerun()

st.divider()

# --- 💾 存檔與歷史 ---
if st.button("💾 儲存今日日誌", type="primary", use_container_width=True):
    try:
        bp_str = f"{st.session_state.metrics['bp_sys']}/{st.session_state.metrics['bp_dia']}"
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT OR REPLACE INTO health_logs 
                (date, actual_age, body_age, visceral_fat, muscle_mass, bmi, resting_hr, blood_pressure, readiness_score, social_mode_active, micro_workouts_done, water_intake_cc) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                today_str, st.session_state.metrics['actual_age'], st.session_state.metrics['body_age'], 
                st.session_state.metrics['vf'], st.session_state.metrics['muscle'], 
                st.session_state.metrics['bmi'], st.session_state.metrics['hr'], bp_str,
                st.session_state.readiness_score, st.session_state.social_mode, 
                st.session_state.micro_workouts, st.session_state.water_intake
            ))
            conn.commit()
        st.toast("✅ 日誌已安全寫入資料庫。", icon="💾")
    except Exception as e:
        st.error(f"寫入失敗：{e}")

with st.expander("📖 查看歷史紀錄"):
    history_df = load_history()
    if not history_df.empty:
        st.dataframe(history_df, use_container_width=True, hide_index=True)
    else:
        st.write("尚無歷史紀錄。")
