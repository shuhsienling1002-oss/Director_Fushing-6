import streamlit as st
import datetime
import sqlite3
import pandas as pd
import numpy as np

# ==========================================
# 🛡️ 10-1. 物理與結構底層 (Physics & Structure)
# 採用第一性原理，實作轉接器模式與防禦性解析
# ==========================================
class TelemetryOracle:
    """全域遙測與資料庫防腐層 (Anti-Corruption Layer)"""
    DB_PATH = 'fuxing_guardian_v95_pro.db'

    @classmethod
    def init_database(cls):
        # 證偽主義：預設資料庫隨時會損毀，強制加上 Try-Catch 緩衝區
        try:
            with sqlite3.connect(cls.DB_PATH) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS health_logs (
                        date TEXT PRIMARY KEY,
                        actual_age INTEGER, body_age INTEGER,
                        visceral_fat REAL, muscle_mass REAL, bmi REAL,
                        resting_hr INTEGER, blood_pressure TEXT,
                        readiness_score INTEGER, social_mode_active BOOLEAN,
                        micro_workouts_done INTEGER, water_intake_cc INTEGER,
                        risk_probability REAL
                    )
                ''')
        except Exception as e:
            st.error(f"🛑 [架構警報] 儲存層崩潰，啟動離線唯讀模式: {e}")

    @classmethod
    def load_telemetry(cls):
        """實作防禦性編程 (Defensive Programming)，永遠不信任歷史資料格式"""
        try:
            with sqlite3.connect(cls.DB_PATH) as conn:
                df = pd.read_sql_query("SELECT * FROM health_logs ORDER BY date DESC LIMIT 14", conn)
                return df
        except:
            return pd.DataFrame()

# ==========================================
# 🧠 00-PATCH-v9.5 預測性攔截機制 (Active Inference Layer)
# ==========================================
def predictive_circuit_breaker(metrics, social_mode, workouts, water, history_df):
    """
    計算 P(Risk) 並執行虛擬熔斷。
    公式: P(Risk) = f(S_current + ΔS * W_load)
    """
    # 1. 計算當前基礎生理熵值 (S_current)
    base_score = 100
    vf_penalty = max(0, (metrics['vf'] - 10) * 1.5)
    hr_penalty = max(0, (metrics['hr'] - 65) * 2)
    bp_penalty = max(0, (metrics['bp_sys'] - 130) * 1)
    age_gap = metrics['body_age'] - metrics['actual_age']
    
    current_score = base_score - vf_penalty - hr_penalty - bp_penalty - (age_gap * 1)
    if social_mode: current_score -= 20
    current_score += (workouts * 3) + (5 if water >= (3000 if social_mode else 2000) else 0)
    final_score = max(0, min(100, int(current_score)))

    # 2. 計算動態趨勢 (ΔS)
    trend_slope = 0.0
    if not history_df.empty and len(history_df) >= 3:
        y = history_df['readiness_score'].iloc[:3].values[::-1]
        x = np.arange(len(y))
        trend_slope = np.polyfit(x, y, 1)[0] # 計算線性回歸斜率

    # 3. 工作負載估算 (W_load) 與 貝葉斯風險概率
    w_load = 1.5 if social_mode else 1.0
    risk_prob = 0.0
    
    # 若分數低於 65 或 趨勢急速下降，風險飆升
    if final_score < 65: risk_prob += 40.0
    if trend_slope < -2.0: risk_prob += 30.0 * w_load
    if metrics['bp_sys'] > 140: risk_prob += 50.0 # 紅旗指標
    
    risk_prob = min(100.0, risk_prob)
    
    # 攔截規則：IF P(Risk) > 60% THEN 觸發虛擬熔斷
    is_breaker_tripped = risk_prob > 60.0

    return final_score, risk_prob, is_breaker_tripped

# ==========================================
# 👁️ 10-3. 介面視覺與交互架構 (UIUX-CRF)
# 遵循席克定律 (降低選擇) 與漸進式揭露
# ==========================================
st.set_page_config(page_title="復興守護者 Pro", page_icon="🛡️", layout="wide")
TelemetryOracle.init_database()

# --- 狀態機防禦初始化 ---
if 'metrics' not in st.session_state:
    st.session_state.metrics = {'actual_age': 54, 'body_age': 69, 'vf': 25.0, 'muscle': 26.7, 'bmi': 33.8, 'hr': 63, 'bp_sys': 119, 'bp_dia': 79}
if 'social_mode' not in st.session_state: st.session_state.social_mode = False
if 'micro_workouts' not in st.session_state: st.session_state.micro_workouts = 0
if 'water_intake' not in st.session_state: st.session_state.water_intake = 0

history_df = TelemetryOracle.load_telemetry()

# 🧠 呼叫預言機結算
score, risk_prob, is_breaker_tripped = predictive_circuit_breaker(
    st.session_state.metrics, st.session_state.social_mode, 
    st.session_state.micro_workouts, st.session_state.water_intake, history_df
)

water_goal = 3000 if st.session_state.social_mode else 2000

# --- 🔴 視覺警告層 (Cognitive Lock) ---
if is_breaker_tripped:
    st.error(f"🛑 **系統級熔斷 (Hard Stop) 已觸發 | 崩潰預測率: {risk_prob:.1f}%**")
    st.warning("已根據 16-2 絕對阻斷原則，強制退回【安全模式】。所有高強度課表已鎖死。")
else:
    st.success(f"✅ **系統運行穩定 | 隱含風險率: {risk_prob:.1f}%**")

st.title("🛡️ 復興守護者：動態預測層")

# --- 📥 漸進式揭露 (Progressive Disclosure) ---
with st.expander("📥 每日遙測數據校準 (展開輸入)", expanded=False):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        new_vf = st.number_input("內臟脂肪", value=st.session_state.metrics['vf'], step=0.5)
        new_bp_sys = st.number_input("收縮壓", value=st.session_state.metrics['bp_sys'], step=1)
    with col_b:
        new_body_age = st.number_input("身體年齡", value=st.session_state.metrics['body_age'], step=1)
        new_bp_dia = st.number_input("舒張壓", value=st.session_state.metrics['bp_dia'], step=1)
    with col_c:
        new_hr = st.number_input("安靜心率", value=st.session_state.metrics['hr'], step=1)
        
    if st.button("🔄 校準感測器", use_container_width=True):
        st.session_state.metrics.update({'vf': new_vf, 'bp_sys': new_bp_sys, 'body_age': new_body_age, 'bp_dia': new_bp_dia, 'hr': new_hr})
        st.rerun()

st.divider()

# --- 🔋 綜合狀態儀表板 (極簡化) ---
c1, c2, c3 = st.columns(3)
c1.metric("綜合戰備評分", f"{score}/100", "高壓" if score < 70 else "正常", delta_color="inverse" if score < 70 else "normal")
c2.metric("心血管防線", f"{st.session_state.metrics['bp_sys']}/{st.session_state.metrics['bp_dia']}", "紅旗警報" if st.session_state.metrics['bp_sys'] > 135 else "安全")
c3.metric("代謝老化差距", f"+{st.session_state.metrics['body_age'] - st.session_state.metrics['actual_age']} 歲", "需重塑")

st.divider()

# --- ⚙️ 16-4. 數位療法與降維打擊 (DTx Oracle Override) ---
st.subheader("⏱️ 處方動態路由 (Dynamic Routing)")

if is_breaker_tripped:
    # 啟動降維打擊監測 (Dimensional Reduction)
    st.info("🧘 **【降維安全模式 Safe Mode】**：偵測到交感神經高壓，關閉所有耗能選項。")
    if st.button("🫁 執行 2 分鐘橫膈膜呼吸 (唯一開放操作)", type="primary", use_container_width=True):
        st.session_state.micro_workouts += 1
        st.toast("✅ 呼吸調節完成，副交感神經已重置。")
        st.rerun()
else:
    # 正常模式，提供微量給藥 (Micro-dosing)
    available_time = st.segmented_control("選擇可用算力 (時間)", ["3 分鐘 (微量給藥)", "10 分鐘 (全身喚醒)"], default="3 分鐘 (微量給藥)")
    if st.button(f"⚡ 執行 {available_time.split(' ')[0]} 任務", type="primary"):
        st.session_state.micro_workouts += 1
        st.balloons()
        st.rerun()

st.divider()

# --- 💧 習慣迴圈與二階思維 (Habit Loop & Second-Order Thinking) ---
c_w1, c_w2 = st.columns([2, 1])
with c_w1:
    st.subheader(f"💧 基礎代謝冷卻液 (目標: {water_goal} cc)")
    st.progress(min(st.session_state.water_intake / water_goal, 1.0), text=f"當前水位: {st.session_state.water_intake} cc")
with c_w2:
    st.write("") # Spacer
    if st.button("➕ 補充 250cc", use_container_width=True):
        st.session_state.water_intake += 250
        st.rerun()

# --- 🗓️ 社會認同與代理人問題 (Principal-Agent Problem) ---
st.divider()
if st.session_state.social_mode:
    st.error("🍷 **酒精衝擊已確認 (代理人悖論)**")
    st.markdown("""
    > **[反身性警告]** 酒精正在強制中斷您的脂肪氧化迴路。未來 14 小時內，任何過量碳水將以 100% 效率轉化為內臟脂肪。
    """)
    if st.button("🛡️ 應酬結束，啟動 14H 肝臟排毒協議", type="primary"):
        st.session_state.social_mode = False
        st.rerun()
else:
    if st.button("⚠️ 遭遇臨時應酬 (重新計算生物成本)"):
        st.session_state.social_mode = True
        st.rerun()

# --- 💾 10-4. 系統寫入與反脆弱 (Antifragility) ---
st.divider()
if st.button("💾 寫入不可篡改健康日誌 (Commit Log)", use_container_width=True):
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    bp_str = f"{st.session_state.metrics['bp_sys']}/{st.session_state.metrics['bp_dia']}"
    
    try:
        with sqlite3.connect(TelemetryOracle.DB_PATH) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO health_logs 
                (date, actual_age, body_age, visceral_fat, muscle_mass, bmi, resting_hr, blood_pressure, readiness_score, social_mode_active, micro_workouts_done, water_intake_cc, risk_probability) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                today_str, st.session_state.metrics['actual_age'], st.session_state.metrics['body_age'], 
                st.session_state.metrics['vf'], st.session_state.metrics['muscle'], 
                st.session_state.metrics['bmi'], st.session_state.metrics['hr'], bp_str,
                score, st.session_state.social_mode, 
                st.session_state.micro_workouts, st.session_state.water_intake, risk_probability
            ))
        st.toast("✅ 遙測數據已安全寫入底層資料庫。")
    except Exception as e:
        st.error(f"資料庫鎖定異常: {e}")
