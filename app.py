import streamlit as st
import datetime
import sqlite3
import pandas as pd

DB_NAME = 'fuxing_guardian_v95.db'

# ==========================================
# 🛡️ 系統底層：防禦性資料庫與自動計算引擎
# ==========================================
def init_db():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS health_logs (
                    date TEXT PRIMARY KEY, actual_age INTEGER, body_age INTEGER,
                    visceral_fat REAL, muscle_mass REAL, bmi REAL,
                    resting_hr INTEGER, blood_pressure TEXT, readiness_score INTEGER, 
                    social_mode_active BOOLEAN, micro_workouts_done INTEGER, water_intake_cc INTEGER
                )
            ''')
            conn.commit()
    except Exception as e:
        st.error(f"🚨 系統啟動失敗：資料庫初始化異常。({e})")

def check_red_flag(bp_sys, hr):
    """🩺 絕對阻斷：實體紅旗指標檢測"""
    return bp_sys >= 160 or hr >= 100

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

# 🔮 [v9.5 擴充] 預測性攔截模型 (Predictive Risk)
def calculate_predictive_risk(current_readiness, hr, w_load):
    """
    計算公式：P(Risk > L3) = f(S_current + ΔS * W_load)
    """
    # 當前生理耗損度 (100 - 準備度)
    s_current = 100 - current_readiness
    # 心率壓力乘數
    delta_s = 1.0 + max(0, (hr - 65) * 0.05)
    # 工作負載乘數 (W_load: 0~12 小時高壓)
    load_multiplier = 1.0 + (w_load * 0.1)
    
    p_risk = (s_current * delta_s) * load_multiplier
    return max(0, min(100, int(p_risk)))

def load_history():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            return pd.read_sql_query("SELECT * FROM health_logs ORDER BY date DESC", conn)
    except Exception:
        return pd.DataFrame()

st.set_page_config(page_title="復興守護者 v9.5", page_icon="🛡️", layout="wide")
init_db()

today_date = datetime.date.today()
today_str = today_date.strftime("%Y-%m-%d")
is_weekend = today_date.weekday() >= 5 

# ==========================================
# 🧠 狀態機與預言機初始化 
# ==========================================
if 'social_mode' not in st.session_state: st.session_state.social_mode = False
if 'metrics' not in st.session_state: 
    st.session_state.metrics = {
        'actual_age': 54, 'body_age': 69, 'vf': 25.0, 'muscle': 26.7, 
        'bmi': 33.8, 'hr': 63, 'bp_sys': 119, 'bp_dia': 79
    }
if 'micro_workouts' not in st.session_state: st.session_state.micro_workouts = 0 
if 'water_intake' not in st.session_state: st.session_state.water_intake = 0 
if 'w_load' not in st.session_state: st.session_state.w_load = 0 if is_weekend else 6

water_goal = 3000 if st.session_state.social_mode else 2000
has_red_flag = check_red_flag(st.session_state.metrics['bp_sys'], st.session_state.metrics['hr'])

st.session_state.readiness_score = calculate_readiness(
    st.session_state.metrics['vf'], st.session_state.metrics['hr'], st.session_state.metrics['bp_sys'], 
    st.session_state.metrics['body_age'], st.session_state.metrics['actual_age'],
    st.session_state.social_mode, st.session_state.micro_workouts, st.session_state.water_intake, water_goal
)

# 執行 v9.5 預測性攔截推算
predictive_risk = calculate_predictive_risk(st.session_state.readiness_score, st.session_state.metrics['hr'], st.session_state.w_load)
is_pre_fatigued = predictive_risk > 60

# ==========================================
# 🎨 介面層：Meta-Agent 動態調度
# ==========================================
st.title("🛡️ 復興守護者 (v9.5 預測引擎啟動)")
st.markdown(f"**蘇區長，早安。今天是 {today_str}**")

# 🔴 最高層級阻斷：實體紅旗
if has_red_flag:
    st.error("🚨 **【Tier 4 實體紅旗警報】** 檢測到心血管壓力過載。系統強制切斷權限，請啟動靜養安全模式！")

# 🟠 次高層級阻斷：虛擬熔斷 (v9.5 補丁)
elif is_pre_fatigued:
    st.warning(f"⚠️ **【虛擬熔斷 (Virtual Circuit Breaker) 啟動】**\n\n預測風險值達 **{predictive_risk}%**。系統推論：您的生理狀態 ($S_{current}$) 加上後續高壓 ($W_{load}$)，將在短時間內觸發疲勞臨界點 (PRE-FATIGUE)。**Meta-Agent 已強制凍結高強度訓練權限。**")

# --- 📥 動態負載與數值輸入 ---
with st.expander("📥 點此更新今日生理數值與預計負載", expanded=False):
    st.caption("🔮 **主動推論輸入變數 ($W_{load}$)**")
    new_w_load = st.slider("今日預計會議/高壓公務時數", min_value=0, max_value=12, value=st.session_state.w_load)
    st.divider()
    
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
        
    if st.button("🔄 更新數值與預測模型", use_container_width=True):
        st.session_state.w_load = new_w_load
        st.session_state.metrics.update({
            'actual_age': new_actual_age, 'body_age': new_body_age, 'vf': new_vf, 
            'muscle': new_muscle, 'bmi': new_bmi, 'hr': new_hr, 'bp_sys': new_bp_sys, 'bp_dia': new_bp_dia
        })
        st.rerun()

st.divider()

# --- 🔋 儀表板 ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("當前準備度", f"{st.session_state.readiness_score}%", "穩定" if st.session_state.readiness_score >= 70 else "耗損", delta_color="inverse" if st.session_state.readiness_score < 70 else "normal")
with col2:
    st.metric("🔮 預測崩潰風險", f"{predictive_risk}%", "危險" if is_pre_fatigued else "安全範圍", delta_color="inverse")
with col3:
    st.metric("心血管防線", f"{st.session_state.metrics['bp_sys']}/{st.session_state.metrics['bp_dia']}", "高危" if has_red_flag else "正常", delta_color="inverse" if has_red_flag else "normal")
with col4:
    age_gap = st.session_state.metrics['body_age'] - st.session_state.metrics['actual_age']
    st.metric("代謝老化", f"{st.session_state.metrics['body_age']} 歲", f"{'+' if age_gap > 0 else ''}{age_gap} 歲", delta_color="inverse")

st.divider()

# --- 🏃‍♂️ Meta-Agent 任務調度中心 ---
st.subheader("⏱️ 任務調度中心 (Meta-Agent Orchestration)")

if has_red_flag:
    st.error("🛑 **[100% 算力轉移]** 實體安全模式：請平躺並尋求醫療建議，禁止任何操作。")
elif is_pre_fatigued:
    st.info("🧘 **[資源重分配]** 預疲勞攔截：高強度訓練已鎖定。強制執行 3 分鐘箱式呼吸 (Box Breathing) 降載自律神經。")
    if st.button("✅ 完成降載呼吸 (+1分)"):
        st.session_state.micro_workouts += 1
        st.rerun()
else:
    # 綠燈狀態：開放所有權限
    workouts = ["3 分鐘 (辦公椅深蹲)", "10 分鐘 (階梯微喘)", "15 分鐘 (步道健行)"]
    if st.session_state.social_mode:
        st.info("🍷 **應酬降載模式**：請選擇低強度動作。")
        workouts = ["3 分鐘 (純拉伸)"]
        
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
with st.expander("🍽️ 會議便當/桌菜破解法", expanded=False):
    st.info("💡 控制進食順序，避免血糖飆升囤積脂肪。")
    st.markdown("1. 先吃青菜 ➔ 2. 再吃肉類 ➔ 3. 白飯最後且減半。")

if st.session_state.social_mode:
    st.error("🚨 **酒精衝擊警報**：燃脂已停滯。請嚴守 1:1 水分法則。")
    if st.button("✅ 應酬結束 (啟動排毒)"):
        st.session_state.social_mode = False
        st.rerun()
else:
    if st.button("🍷 追加應酬 (啟動防禦)", use_container_width=True):
        st.session_state.social_mode = True
        st.rerun()

st.divider()

# --- 💾 存檔與歷史 (含防禦機制) ---
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

with st.expander("📖 查看 / 修改歷史紀錄"):
    tab1, tab2 = st.tabs(["📊 歷史列表", "🗑️ 管理"])
    history_df = load_history()
    
    with tab1:
        if not history_df.empty:
            st.dataframe(history_df, use_container_width=True, hide_index=True)
        else:
            st.write("尚無歷史紀錄。")
            
    with tab2:
        if not history_df.empty:
            selected_date = st.selectbox("選擇要刪除的日期：", history_df['date'].tolist())
            if st.button("🗑️ 刪除這筆紀錄", type="primary"):
                try:
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("DELETE FROM health_logs WHERE date=?", (selected_date,))
                        conn.commit()
                    st.warning(f"已刪除 {selected_date} 紀錄")
                    st.rerun()
                except Exception as e:
                    st.error(f"刪除失敗：{e}")
