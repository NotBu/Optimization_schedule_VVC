import streamlit as st
import pandas as pd
import re
from datetime import time

# Cấu hình trang
st.set_page_config(page_title="Tool xếp lịch tập VVC", layout="wide")

# --- CSS CAO CẤP ---
st.markdown("""
<style>
    .task-card {
        background-color: white; padding: 12px 20px; border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-left: 5px solid #6366f1;
        margin-bottom: 8px; transition: all 0.3s ease; color: #1f2937;
        font-family: 'Segoe UI', sans-serif;
    }
    .task-card:hover { box-shadow: 0 5px 15px rgba(0,0,0,0.1); transform: translateY(-2px); }
    @keyframes subtle-pulse {
        0% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.4); border-left-color: #6366f1; }
        70% { box-shadow: 0 0 0 10px rgba(99, 102, 241, 0); border-left-color: #10b981; }
        100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0); border-left-color: #6366f1; }
    }
    .moved-card { animation: subtle-pulse 1s ease-out; background-color: #f8fafc; }
    div[data-testid="stHorizontalBlock"] button {
        background-color: transparent; border: 1px solid #e5e7eb; color: #6b7280;
        border-radius: 6px; transition: all 0.2s; height: 2.8rem;
    }
    div[data-testid="stHorizontalBlock"] button:hover {
        border-color: #6366f1; color: #6366f1; background-color: #eef2ff;
    }
    div[data-testid="stHorizontalBlock"] button:hover p:contains("✕") { color: #ef4444 !important; }
    .task-title { font-weight: 600; font-size: 1.05rem; }
    .task-meta { color: #6b7280; font-size: 0.85rem; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

if 'tasks' not in st.session_state: st.session_state['tasks'] = []
if 'last_moved_idx' not in st.session_state: st.session_state['last_moved_idx'] = -1

st.title("📅 Tool xếp lịch tập VVC")
st.markdown("---")

# 1. UPLOAD
st.sidebar.header("📥 Dữ liệu nguồn")
uploaded_file = st.sidebar.file_uploader("Thả file CSV vào đây", type=['csv'])

# --- TỪ ĐIỂN VIỆT HÓA ---
WEEKDAY_MAP = {
    "Monday": "Thứ 2", "Tuesday": "Thứ 3", "Wednesday": "Thứ 4",
    "Thursday": "Thứ 5", "Friday": "Thứ 6", "Saturday": "Thứ 7", "Sunday": "CN"
}

def translate_days(text):
    txt = str(text)
    for eng, vie in WEEKDAY_MAP.items():
        if eng in txt: txt = txt.replace(eng, vie)
    return txt

# --- HÀM XỬ LÝ ---
def parse_hour_value(time_str):
    ts = str(time_str).upper().strip()
    hour = 0; minute = 0
    if "AM" in ts or "PM" in ts:
        is_pm = "PM" in ts
        nums = re.findall(r'\d+', ts)
        if nums:
            hour = int(nums[0])
            if len(nums) > 1: minute = int(nums[1])
            if is_pm and hour < 12: hour += 12
            if not is_pm and hour == 12: hour = 0
    else:
        parts = ts.split()
        time_part = parts[-1] if parts else ""
        if ":" in time_part:
            try: h, m = map(int, time_part.split(":")[:2]); hour = h; minute = m
            except: pass
        else:
            nums = re.findall(r'\d+', ts)
            if nums: hour = int(nums[-1])
    return hour + minute/60.0

def load_data(file):
    df = pd.read_csv(file)
    time_col = df.columns[0]
    people_cols = df.columns[1:]
    
    df_people = df[people_cols].fillna(0).apply(pd.to_numeric, errors='coerce').fillna(0)
    df['Time'] = df[time_col]
    df['HourVal'] = df['Time'].apply(parse_hour_value)
    
    def extract_strict_date(t_str):
        s = str(t_str).strip()
        match = re.search(r'^(.*?\d{1,2}/\d{1,2})', s)
        if match: return match.group(1).strip()
        return re.sub(r'\s+(\d{1,2}:\d{2}.*|\d{1,2}\s*[AP]M)$', '', s, flags=re.IGNORECASE).strip()

    df['DateOnly'] = df['Time'].apply(extract_strict_date)
    return df, df_people, list(people_cols)

def move_task(index, direction):
    tasks = st.session_state['tasks']
    new_idx = index
    if direction == 'up' and index > 0:
        tasks[index], tasks[index-1] = tasks[index-1], tasks[index]
        new_idx = index - 1
    elif direction == 'down' and index < len(tasks) - 1:
        tasks[index], tasks[index+1] = tasks[index+1], tasks[index]
        new_idx = index + 1
    st.session_state['last_moved_idx'] = new_idx

if uploaded_file is not None:
    try:
        df, df_people, all_members = load_data(uploaded_file)
        unique_dates_raw = df['DateOnly'].unique().tolist()
        unique_dates_display = [translate_days(d) for d in unique_dates_raw]
        date_map = dict(zip(unique_dates_display, unique_dates_raw))
        
        st.sidebar.success(f"✅ Đã tải: {len(unique_dates_raw)} ngày | {len(all_members)} người.")

        # ==========================================
        # 🛠️ ADMIN TOOLS (ĐÃ KHÔI PHỤC)
        # ==========================================
        with st.expander("🛠️ Admin Tools (Xuất dữ liệu tổng hợp)", expanded=False):
            st.info("Bấm nút bên dưới để tải file Excel chứa toàn bộ dữ liệu. Dùng để đối chiếu thủ công.")
            
            # Logic tạo file Master
            if st.button("⚡ Tạo Master File"):
                df_admin = pd.DataFrame()
                # Việt hóa cột thời gian luôn cho đẹp
                df_admin['Thời gian'] = df['Time'].apply(translate_days)
                
                # Phân loại Sáng/Chiều sơ bộ
                df_admin['Buổi'] = df['HourVal'].apply(lambda h: "Sáng" if h < 12 else "Chiều")
                
                # Đếm tổng người
                df_admin['Tổng rảnh'] = df_people.sum(axis=1)
                
                # Nối tên người (Thay hàm TEXTJOIN)
                def get_names(row):
                    return ", ".join(row.index[row == 1].tolist())
                df_admin['Danh sách tên'] = df_people.apply(get_names, axis=1)
                
                # Xuất file
                csv_admin = df_admin.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 Tải xuống Master_Data.csv",
                    data=csv_admin,
                    file_name="Master_Data_Admin.csv",
                    mime="text/csv"
                )

        # --- CẤU HÌNH ---
        st.header("⚙️ Cấu hình")
        c1, c2 = st.columns([1, 2])
        with c1:
            selected_date_display = st.selectbox("Chọn Ngày:", unique_dates_display)
            selected_date_raw = date_map[selected_date_display]
        with c2:
            time_mode = st.radio("Khung giờ:", ["Cả ngày", "Sáng (<12h)", "Chiều (>12h)", "Custom"], horizontal=True)

        start_val, end_val = 0.0, 24.0
        if time_mode == "Sáng (<12h)": start_val, end_val = 6.0, 12.0
        elif time_mode == "Chiều (>12h)": start_val, end_val = 12.0, 23.0
        elif time_mode == "Custom":
            tc1, tc2 = st.columns(2)
            with tc1: t_start = st.time_input("Từ:", value=time(13, 30))
            with tc2: t_end = st.time_input("Đến:", value=time(21, 0))
            start_val = t_start.hour + t_start.minute/60.0
            end_val = t_end.hour + t_end.minute/60.0

        mask = (df['DateOnly'] == selected_date_raw) & (df['HourVal'] >= start_val) & (df['HourVal'] < end_val)
        df_filtered = df.loc[mask].reset_index(drop=True)
        df_people_filtered = df_people.loc[mask].reset_index(drop=True)
        
        if df_filtered.empty:
            st.warning("⚠️ Không có giờ trống!")
        else:
            st.success(f"Sẵn sàng xếp lịch ({len(df_filtered)} slots)")

        st.markdown("---")

        # --- DANH SÁCH BÀI TẬP ---
        st.header("📋 Danh sách Ưu tiên")
        with st.container():
            ic1, ic2, ic3, ic4 = st.columns([3, 3, 2, 1.5])
            with ic1: t_name = st.text_input("Tên bài", placeholder="VD: Trà và cà phê", label_visibility="collapsed")
            with ic2: 
                use_all = st.checkbox("All Member")
                t_mem = all_members if use_all else st.multiselect("Thành viên", all_members, label_visibility="collapsed", placeholder="Chọn người...")
            with ic3: t_dur = st.selectbox("Thời lượng", [45, 60, 90, 120], index=1, label_visibility="collapsed")
            with ic4: 
                if st.button("➕ Thêm", type="primary", use_container_width=True):
                    if t_name and t_mem:
                        st.session_state['tasks'].append({"name": t_name, "members": t_mem, "duration": t_dur})
                        st.session_state['last_moved_idx'] = len(st.session_state['tasks']) - 1
                        st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        if st.session_state['tasks']:
            for i, t in enumerate(st.session_state['tasks']):
                col_card, col_up, col_down, col_del = st.columns([7, 0.6, 0.6, 0.6])
                with col_card:
                    css_class = "task-card"
                    if i == st.session_state['last_moved_idx']: css_class += " moved-card"
                    st.markdown(f"""
                    <div class="{css_class}">
                        <div class="task-title">#{i+1}. {t['name']}</div>
                        <div class="task-meta">⏱️ {t['duration']} phút • 👥 {len(t['members'])} thành viên</div>
                    </div>""", unsafe_allow_html=True)
                with col_up:
                    if i > 0 and st.button("▲", key=f"u{i}"): move_task(i, 'up'); st.rerun()
                with col_down:
                    if i < len(st.session_state['tasks']) - 1 and st.button("▼", key=f"d{i}"): move_task(i, 'down'); st.rerun()
                with col_del:
                    if st.button("✕", key=f"del{i}"): st.session_state['tasks'].pop(i); st.session_state['last_moved_idx'] = -1; st.rerun()
            
            st.markdown("---")
            
            c_run, c_clear = st.columns([2, 8])
            run_algo = False
            with c_run:
                if st.button("🚀 CHẠY XẾP LỊCH", type="primary", use_container_width=True): run_algo = True
            with c_clear:
                if st.button("🗑️ Xóa hết"): st.session_state['tasks'] = []; st.rerun()
            
            if run_algo:
                if df_filtered.empty: st.error("Lỗi: Không có dữ liệu giờ!"); st.stop()
                occupied = [False] * len(df_filtered)
                sch = []
                for task in st.session_state['tasks']:
                    slots = int(task['duration'] / 15)
                    curr_mems = task['members']
                    best_sc, best_idx, best_ppl = -1, -1, []
                    for i in range(len(df_filtered) - slots + 1):
                        if any(occupied[i:i+slots]): continue
                        block = df_people_filtered.iloc[i:i+slots][curr_mems]
                        counts = block.sum(axis=0)
                        full_ppl = counts[counts == slots].index.tolist()
                        bonus = 0
                        if i>0 and occupied[i-1]: bonus = 0.5
                        if (i+slots)<len(occupied) and occupied[i+slots]: bonus = 0.5
                        score = len(full_ppl) + bonus
                        if score > best_sc: best_sc = score; best_idx = i; best_ppl = full_ppl
                    
                    if best_idx != -1:
                        for k in range(best_idx, best_idx+slots): occupied[k] = True
                        t_s = df_filtered.loc[best_idx, 'Time']
                        t_e = df_filtered.loc[best_idx+slots, 'Time'] if (best_idx+slots)<len(df_filtered) else "Hết"
                        miss = list(set(curr_mems) - set(best_ppl))
                        sch.append({"Thứ tự": f"#{st.session_state['tasks'].index(task)+1}", "Bài": task['name'], "Thời gian": f"{t_s} - {t_e}", "Sĩ số": f"{len(best_ppl)}/{len(curr_mems)}", "Vắng": ", ".join(miss) if miss else "-"})
                    else:
                        sch.append({"Thứ tự": "-", "Bài": task['name'], "Thời gian": "❌ Kẹt", "Sĩ số": "0", "Vắng": "-"})
                
                res = pd.DataFrame(sch).sort_values(by="Thời gian")
                res['Thời gian'] = res['Thời gian'].apply(translate_days)
                
                st.success(f"Đã xếp xong lịch cho ngày: {translate_days(selected_date_raw)}")
                st.dataframe(res, hide_index=True, use_container_width=True)
                
                csv = res.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Tải CSV (Tiếng Việt)", csv, "Lich_Tap_Final.csv", "text/csv")

    except Exception as e: st.error(f"Lỗi: {e}")
