import streamlit as st
import datetime
import sqlite3
import pandas as pd

DB_NAME = 'fuxing_guardian_v5.db'

# ==========================================
# 🛡️ 系統底層：防禦性本地資料庫與自動計算引擎
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
        st.error(f"🚨 系統啟動失敗：資料庫初始化異常。({e})")

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
    if age_gap > 0:
        base_score -= age_gap * 1
        
    if social_mode: base_score -= 20
    
    base_score += (micro_workouts * 3)
    if water_intake >= water_goal:
        base_score += 5 
        
    return max(0, min(100, int(base_score)))

def load_history():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            df = pd.read_sql_query("SELECT date, actual_age, body_age, visceral_fat, muscle_mass, bmi, resting_hr, blood_pressure, readiness_score, social_mode_active, micro_workouts_done, water_intake_cc FROM health_logs ORDER BY date DESC", conn)
            return df
    except Exception:
        return pd.DataFrame()

st.set_page_config(page_title="復興守護者", page_icon="🛡️", layout="wide")
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
        'actual_age': 54, 'body_age': 69,
        'vf': 25.0, 'muscle': 26.7, 'bmi': 33.8, 'hr': 63, 'bp_sys': 119, 'bp_dia': 79
    }
    
if 'micro_workouts' not in st.session_state: st.session_state.micro_workouts = 0 
if 'water_intake' not in st.session_state: st.session_state.water_intake = 0 

water_goal = 3000 if st.session_state.social_mode else 2000
has_red_flag = check_red_flag(st.session_state.metrics['bp_sys'], st.session_state.metrics['hr'])

if 'readiness_score' not in st.session_state:
    st.session_state.readiness_score = calculate_readiness(
        st.session_state.metrics['vf'], st.session_state.metrics['hr'], st.session_state.metrics['bp_sys'], 
        st.session_state.metrics['body_age'], st.session_state.metrics['actual_age'],
        st.session_state.social_mode, st.session_state.micro_workouts, st.session_state.water_intake, water_goal
    )

# ==========================================
# 🎨 介面層：區長專屬動態儀表板
# ==========================================
st.title("🛡️ 復興守護者")
st.markdown(f"**蘇區長，早安。今天是 {today_str} {'(週末重置日)' if is_weekend else '(市政高壓期)'}**")

if has_red_flag:
    st.error("🚨 **【Tier 4 紅旗警報】** 檢測到心血管壓力過載 (收縮壓或心率異常)。系統已強制切斷主動訓練權限，請啟動靜養安全模式！")

# --- 📥 今日數值輸入區 ---
with st.expander("📥 點此輸入今日最新數值 (同步體脂計/血壓計)", expanded=False):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        new_actual_age = st.number_input("實際年齡", value=st.session_state.metrics['actual_age'], step=1)
        new_vf = st.number_input("內臟脂肪等級", value=st.session_state.metrics['vf'], step=0.5)
        new_bp_sys = st.number_input("收縮壓 (高壓)", value=st.session_state.metrics['bp_sys'], step=1)
    with col_b:
        new_body_age = st.number_input("身體年齡", value=st.session_state.metrics['body_age'], step=1)
        new_muscle = st.number_input("骨骼肌率 (%)", value=st.session_state.metrics['muscle'], step=0.1)
        new_bp_dia = st.number_input("舒張壓 (低壓)", value=st.session_state.metrics['bp_dia'], step=1)
    with col_c:
        new_bmi = st.number_input("BMI", value=st.session_state.metrics['bmi'], step=0.1)
        new_hr = st.number_input("安靜心率 (bpm)", value=st.session_state.metrics['hr'], step=1)
        
    if st.button("🔄 更新今日數值"):
        st.session_state.metrics.update({
            'actual_age': new_actual_age, 'body_age': new_body_age,
            'vf': new_vf, 'muscle': new_muscle, 'bmi': new_bmi, 'hr': new_hr, 'bp_sys': new_bp_sys, 'bp_dia': new_bp_dia
        })
        st.session_state.readiness_score = calculate_readiness(
            new_vf, new_hr, new_bp_sys, new_body_age, new_actual_age, 
            st.session_state.social_mode, st.session_state.micro_workouts, st.session_state.water_intake, water_goal
        )
        st.rerun()

st.divider()

# --- 🔋 綜合狀態儀表板 ---
st.subheader("🔋 今日身體狀態儀表板")
col1, col2, col3 = st.columns(3)
with col1:
    if st.session_state.readiness_score >= 70:
        st.metric("代謝綜合評分", f"{st.session_state.readiness_score}%", "狀態穩定")
    else:
        st.metric("代謝綜合評分", f"{st.session_state.readiness_score}%", "- 肝臟/代謝負載過重", delta_color="inverse")
with col2:
    st.metric("心血管防線 (血壓)", f"{st.session_state.metrics['bp_sys']}/{st.session_state.metrics['bp_dia']}", "高危警報" if has_red_flag else "優良防護中", delta_color="inverse" if has_red_flag else "normal")
with col3:
    age_gap = st.session_state.metrics['body_age'] - st.session_state.metrics['actual_age']
    if age_gap > 0:
        st.metric("代謝老化指標 (身體年齡)", f"{st.session_state.metrics['body_age']} 歲", f"老化 +{age_gap} 歲", delta_color="inverse")
    else:
        st.metric("代謝老化指標 (身體年齡)", f"{st.session_state.metrics['body_age']} 歲", f"年輕 {-age_gap} 歲", delta_color="normal")

st.divider()

# --- 擴充模組整合區 ---
if has_red_flag:
    st.warning("🛏️ **降維打擊/安全模式啟動**：禁止執行任何阻力訓練。請進行 5 分鐘橫膈膜深呼吸。")
elif is_weekend:
    st.subheader("🌲 【週末重置模式啟動】清空一週壓力與胰島素殘留")
    weekend_fasting = st.checkbox("14小時微斷食：今日早餐延後至 10:00，清空胰島素。")
    weekend_walk = st.checkbox("大自然重置：進行 30 分鐘森林漫步，重置迷走神經。")
    if not (weekend_fasting or weekend_walk):
        if st.button("❌ 區長今日因公務沒空重置"):
            st.error("已記錄：今日維持高壓狀態，請多喝水代謝！")
    elif weekend_fasting and weekend_walk:
        st.success("✨ 完美執行重置協議！")
else:
    st.subheader("⏱️ 零碎時間運動")
    available_time = st.radio("區長，您現在有多少空檔？", ["3 分鐘", "10 分鐘", "15 分鐘"], horizontal=True)
    if "3 分鐘" in available_time: st.write("🪑 **辦公椅深蹲 (15下)** + 🧱 **靠牆伏地挺身 (15下)**")
    elif "10 分鐘" in available_time: st.write("🚶‍♂️ **原地高抬腿 (3分鐘)** + 🪜 **階梯微喘 (5分鐘)** + 🫁 **深呼吸 (2分鐘)**")
    else: st.write("⛰️ **微喘步道健行**：維持「微喘」連續步行 15 分鐘。")
    
    if st.button("✅ 完成一次微訓練 (+3分)"):
        st.session_state.micro_workouts += 1
        st.session_state.readiness_score = calculate_readiness(
            st.session_state.metrics['vf'], st.session_state.metrics['hr'], st.session_state.metrics['bp_sys'], 
            st.session_state.metrics['body_age'], st.session_state.metrics['actual_age'],
            st.session_state.social_mode, st.session_state.micro_workouts, st.session_state.water_intake, water_goal
        )
        st.balloons()
        st.rerun()

st.divider()

# --- 💧 動態水杯 ---
st.subheader(f"💧 喝水 (目標: {water_goal} cc)")
progress = min(st.session_state.water_intake / water_goal, 1.0)
st.progress(progress)
st.write(f"目前已飲用：**{st.session_state.water_intake} cc**")

col_w1, col_w2 = st.columns(2)
with col_w1:
    if st.button("➕ 喝一杯水 (250cc)"):
        st.session_state.water_intake += 250
        st.session_state.readiness_score = calculate_readiness(st.session_state.metrics['vf'], st.session_state.metrics['hr'], st.session_state.metrics['bp_sys'], st.session_state.metrics['body_age'], st.session_state.metrics['actual_age'], st.session_state.social_mode, st.session_state.micro_workouts, st.session_state.water_intake, water_goal)
        st.rerun()
with col_w2:
    if st.button("➕ 喝一瓶水 (500cc)"):
        st.session_state.water_intake += 500
        st.session_state.readiness_score = calculate_readiness(st.session_state.metrics['vf'], st.session_state.metrics['hr'], st.session_state.metrics['bp_sys'], st.session_state.metrics['body_age'], st.session_state.metrics['actual_age'], st.session_state.social_mode, st.session_state.micro_workouts, st.session_state.water_intake, water_goal)
        st.rerun()

st.divider()

# --- 🗓️ 應酬防禦與酒精衝擊警告 ---
st.subheader("🗓️ 飲食控管與應酬防禦")
with st.expander("🍽️ 點此查看：今日會議便當/桌菜破解法", expanded=False):
    st.info("💡 核心邏輯：控制進食順序，避免血糖飆升囤積脂肪。")
    st.markdown("1. 先吃青菜 ➔ 2. 再吃肉類 ➔ 3. 白飯最後且減半。")

if st.session_state.social_mode:
    st.error("🚨 酒精衝擊警報：內臟脂肪 (目前: 25) 面臨核彈級風險")
    
    st.markdown("### 🍷 酒精生理影響分析")
    alc_type = st.selectbox("選擇今晚飲用的酒類：", ["🥃 烈酒 (威士忌/高粱)", "🍷 葡萄酒", "🍺 啤酒/調酒 (絕對禁忌)"])
    alc_count = st.number_input("預計飲用杯數：", min_value=1, value=1)
    
    burn_pause = alc_count * (1.5 if "烈酒" in alc_type else 1.0)
    
    st.markdown(f"""
    * 🛑 **燃脂停滯**：您的身體將有 **{burn_pause} 小時** 處於「零燃脂」狀態。這期間您吃下的任何澱粉都會**直接轉化為內臟脂肪**。
    * ⚠️ **代謝老化加劇**：解毒過程將繼續透支器官儲備。
    * ☢️ **內臟脂肪核爆**：{'如果您喝的是啤酒，糖分與酒精的協同作用會讓脂肪囤積效率提高 200%！' if '啤酒' in alc_type else '請嚴守 1:1 水分法則，強迫肝臟降溫。'}
    """)

    if st.button("✅ 應酬平安結束 (啟動 14H 排毒協議)"):
        st.session_state.social_mode = False
        st.session_state.readiness_score = calculate_readiness(st.session_state.metrics['vf'], st.session_state.metrics['hr'], st.session_state.metrics['bp_sys'], st.session_state.metrics['body_age'], st.session_state.metrics['actual_age'], False, st.session_state.micro_workouts, st.session_state.water_intake, 2000)
        st.rerun()
else:
    col_soc1, col_soc2 = st.columns(2)
    with col_soc1:
        if st.button("🍷 臨時追加應酬 (啟動生理損害控管)"):
            st.session_state.social_mode = True
            st.session_state.readiness_score = calculate_readiness(st.session_state.metrics['vf'], st.session_state.metrics['hr'], st.session_state.metrics['bp_sys'], st.session_state.metrics['body_age'], st.session_state.metrics['actual_age'], True, st.session_state.micro_workouts, st.session_state.water_intake, 3000)
            st.rerun()
    with col_soc2:
        if st.button("✅ 今日沒喝酒"):
            st.success("✨ 完美防禦！今日沒喝酒，維持高效率燃脂！")

st.divider()

# --- 💾 存檔紀錄 ---
if st.button("💾 儲存今日完整日誌"):
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
        st.success("✅ 區長，今日完整日誌已成功儲存！")
    except Exception as e:
        st.error(f"寫入失敗：{e}")

# ==========================================
# 📖 歷史紀錄與管理模組 (完整保留並升級防禦)
# ==========================================
st.divider()
st.subheader("📖 歷史健康日誌管理")

tab1, tab2 = st.tabs(["📊 查看歷史紀錄", "✏️ 修改 / 刪除紀錄"])

with tab1:
    history_df = load_history()
    if not history_df.empty:
        display_df = history_df.copy()
        display_df.columns = ['日期', '實際年齡', '身體年齡', '內臟脂肪', '骨骼肌(%)', 'BMI', '安靜心率', '血壓(mmHg)', '綜合評分', '有應酬?', '微訓練(次)', '喝水量(cc)']
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("目前還沒有紀錄喔！請按下方的儲存按鈕來建立第一筆日誌。")

with tab2:
    if not history_df.empty:
        dates_list = history_df['date'].tolist()
        selected_date = st.selectbox("請選擇要修改的日期：", dates_list)
        
        # 🛡️ 加入 with 保護機制讀取該日資料
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT actual_age, body_age, visceral_fat, muscle_mass, bmi, resting_hr, blood_pressure, social_mode_active, micro_workouts_done, water_intake_cc FROM health_logs WHERE date=?", (selected_date,))
            row = c.fetchone()

        if row:
            actual_age, body_age, vf, muscle, bmi, hr, bp, social, workouts, water = row
            try:
                bp_sys, bp_dia = map(int, bp.split('/'))
            except:
                bp_sys, bp_dia = 120, 80

            st.caption(f"正在編輯：**{selected_date}** 的日誌")
            
            with st.container(border=True):
                col_e1, col_e2, col_e3 = st.columns(3)
                with col_e1:
                    e_actual_age = st.number_input("實際年齡", value=int(actual_age), step=1, key="eactualage")
                    e_vf = st.number_input("內臟脂肪", value=float(vf), step=0.5, key="evf")
                    e_bp_sys = st.number_input("收縮壓 (高壓)", value=int(bp_sys), step=1, key="ebpsys")
                    e_water = st.number_input("喝水量 (cc)", value=int(water), step=100, key="ewater")
                with col_e2:
                    e_body_age = st.number_input("身體年齡", value=int(body_age), step=1, key="ebodyage")
                    e_muscle = st.number_input("骨骼肌 (%)", value=float(muscle), step=0.1, key="emuscle")
                    e_bp_dia = st.number_input("舒張壓 (低壓)", value=int(bp_dia), step=1, key="ebpdia")
                    e_workouts = st.number_input("微訓練 (次數)", value=int(workouts), step=1, key="eworkouts")
                with col_e3:
                    e_bmi = st.number_input("BMI", value=float(bmi), step=0.1, key="ebmi")
                    e_hr = st.number_input("安靜心率", value=int(hr), step=1, key="ehr")
                
                e_social = st.checkbox("當天有應酬嗎？", value=bool(social), key="esocial")

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("💾 更新這筆紀錄", type="primary", use_container_width=True):
                        e_bp_str = f"{e_bp_sys}/{e_bp_dia}"
                        e_goal = 3000 if e_social else 2000
                        e_score = calculate_readiness(e_vf, e_hr, e_bp_sys, e_body_age, e_actual_age, e_social, e_workouts, e_water, e_goal)
                        
                        # 🛡️ 加入 with 保護機制寫入更新
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute('''
                                    UPDATE health_logs 
                                    SET actual_age=?, body_age=?, visceral_fat=?, muscle_mass=?, bmi=?, resting_hr=?, blood_pressure=?, readiness_score=?, social_mode_active=?, micro_workouts_done=?, water_intake_cc=?
                                    WHERE date=?
                                ''', (e_actual_age, e_body_age, e_vf, e_muscle, e_bmi, e_hr, e_bp_str, e_score, e_social, e_workouts, e_water, selected_date))
                                conn.commit()
                            st.success(f"✅ {selected_date} 的紀錄已成功更新！")
                            st.rerun()
                        except Exception as e:
                            st.error(f"更新失敗：{e}")
                            
                with col_btn2:
                    if st.button("🗑️ 刪除這筆紀錄", use_container_width=True):
                        # 🛡️ 加入 with 保護機制刪除資料
                        try:
                            with sqlite3.connect(DB_NAME) as conn:
                                c = conn.cursor()
                                c.execute("DELETE FROM health_logs WHERE date=?", (selected_date,))
                                conn.commit()
                            st.warning(f"🗑️ {selected_date} 的紀錄已刪除！")
                            st.rerun()
                        except Exception as e:
                            st.error(f"刪除失敗：{e}")
    else:
        st.write("目前沒有可修改的歷史紀錄。")
