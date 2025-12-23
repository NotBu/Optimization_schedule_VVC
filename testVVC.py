import streamlit as st
import pandas as pd
import re
from datetime import time

# Cấu hình trang
st.set_page_config(page_title="Tool xếp lịch VVC", layout="wide")

# --- CSS DARK MODE (GIỮ NGUYÊN) ---
st.markdown("""
<style>
    .task-card {
        padding: 12px 20px; border-radius: 8px; margin-bottom: 8px; 
        background-color: #262730 !important; border: 1px solid #41424C;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); font-family: 'Segoe UI', sans-serif;
    }
    .prio-1 { border-left: 6px solid #ef4444; } 
    .prio-2 { border-left: 6px solid #3b82f6; } 
    .prio-3 { border-left: 6px solid #9ca3af; } 
    .badge {
        display: inline-block; padding: 2px 8px; border-radius: 12px;
        font-size: 0.75rem; font-weight: bold; color: white !important; 
        margin-right: 8px; vertical-align: middle;
    }
    .bg-1 { background-color: #ef4444; }
    .bg-2 { background-color: #3b82f6; }
    .bg-3 { background-color: #6b7280; }
    .task-title { 
        font-weight: 700 !important; font-size: 1.1rem !important; 
        color: #ffffff !important; vertical-align: middle;
    }
    .task-meta { 
        color: #d1d5db !important; font-size: 0.9rem !important; margin-top: 6px;
    }
    .time-limit-tag {
        font-size: 0.8rem; color: #fbbf24 !important; background-color: #451a03 !important;
        padding: 2px 8px; border-radius: 4px; border: 1px solid #b45309;
        margin-left: 8px; font-weight: 600; vertical-align: middle; display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

if 'tasks' not in st.session_state: st.session_state['tasks'] = []

st.title("📅 Tool xếp lịch VVC")
st.markdown("---")

# 1. UPLOAD
st.sidebar.header("📥 Dữ liệu nguồn")
uploaded_file = st.sidebar.file_uploader("Thả file CSV vào đây", type=['csv'])

# --- HÀM XỬ LÝ ---
WEEKDAY_MAP = {"Monday": "Thứ 2", "Tuesday": "Thứ 3", "Wednesday": "Thứ 4", "Thursday": "Thứ 5", "Friday": "Thứ 6", "Saturday": "Thứ 7", "Sunday": "CN"}
def translate_days(text):
    txt = str(text)
    for eng, vie in WEEKDAY_MAP.items(): 
        if eng in txt: txt = txt.replace(eng, vie)
    return txt

def parse_hour_value(time_str):
    ts = str(time_str).upper().strip()
    hour = 0; minute = 0
    if "AM" in ts or "PM" in ts:
        is_pm = "PM" in ts
        nums = re.findall(r'\d+', ts)
        if nums:
            hour = int(nums[0]); 
            if len(nums)>1: minute = int(nums[1])
            if is_pm and hour<12: hour+=12
            if not is_pm and hour==12: hour=0
    else:
        parts = ts.split(); time_part = parts[-1] if parts else ""
        if ":" in time_part:
            try: h, m = map(int, time_part.split(":")[:2]); hour=h; minute=m
            except: pass
        else:
            nums = re.findall(r'\d+', ts); 
            if nums: hour = int(nums[-1])
    return hour + minute/60.0

def load_data(file):
    df = pd.read_csv(file)
    time_col = df.columns[0]; people_cols = df.columns[1:]
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

def sort_tasks():
    st.session_state['tasks'] = sorted(st.session_state['tasks'], key=lambda x: x['prio_val'])

# Hàm tìm ngày đông nhất
def find_best_day(df, df_people):
    dates = df['DateOnly'].unique()
    best_d = None
    max_concurrent = -1
    
    for d in dates:
        mask = df['DateOnly'] == d
        # Tính tổng số người rảnh tại mỗi khung giờ trong ngày đó
        counts = df_people.loc[mask].sum(axis=1)
        if not counts.empty:
            peak = counts.max() # Đỉnh điểm của ngày đó
            if peak > max_concurrent:
                max_concurrent = peak
                best_d = d
    return best_d, int(max_concurrent)

# Hàm phân tích slot cho thuật toán V21
def analyze_task_options(task, df_day, df_ppl_day, occupied, global_start, global_end):
    slots_needed = int(task['duration'] / 15)
    curr_mems = task['members']
    
    v_start = global_start
    v_end = global_end
    if task['use_custom']:
        v_start = max(global_start, task['c_start'])
        v_end = min(global_end, task['c_end'])
    
    valid_options = []
    
    for i in range(len(df_day) - slots_needed + 1):
        s_time = df_day.loc[i, 'HourVal']
        e_time = df_day.loc[min(i+slots_needed, len(df_day)-1), 'HourVal']
        if i+slots_needed >= len(df_day): e_time = 24.0
        
        if s_time < v_start or e_time > v_end: continue
        if any(occupied[i:i+slots_needed]): continue
        
        block = df_ppl_day.iloc[i:i+slots_needed][curr_mems]
        counts = block.sum(axis=0)
        full_ppl = counts[counts == slots_needed].index.tolist()
        score = len(full_ppl)
        
        valid_options.append({'index': i, 'score': score, 'attendees': full_ppl})
            
    return valid_options

if uploaded_file is not None:
    try:
        df, df_people, all_members = load_data(uploaded_file)
        unique_dates_raw = df['DateOnly'].unique().tolist()
        unique_dates_display = [translate_days(d) for d in unique_dates_raw]
        date_map = dict(zip(unique_dates_display, unique_dates_raw))
        
        st.sidebar.success(f"✅ Đã tải: {len(unique_dates_raw)} ngày | {len(all_members)} người.")

        with st.expander("🛠️ Admin Tools", expanded=False):
            if st.button("⚡ Tạo Master File"):
                df_admin = pd.DataFrame()
                df_admin['Thời gian'] = df['Time'].apply(translate_days)
                df_admin['Tổng rảnh'] = df_people.sum(axis=1)
                df_admin['Danh sách tên'] = df_people.apply(lambda r: ", ".join(r.index[r==1].tolist()), axis=1)
                st.download_button("📥 Tải Master Data", df_admin.to_csv(index=False).encode('utf-8-sig'), "Master_Data.csv", "text/csv")

        # ==========================================
        # ⚙️ CẤU HÌNH CHUNG (CÓ TÍNH NĂNG MỚI)
        # ==========================================
        st.header("⚙️ Cấu hình Chung")
        
        # Tìm ngày đông nhất trước để hiển thị info
        best_day_raw, best_day_peak = find_best_day(df, df_people)
        
        c1, c2 = st.columns([1.5, 2])
        with c1:
            # Chọn chế độ ngày
            day_mode = st.radio("Chế độ chọn ngày:", ["🎯 Thủ công", "🏆 Tự động (Ngày đông nhất)"], horizontal=True)
            
            if day_mode == "🎯 Thủ công":
                sel_date_display = st.selectbox("Chọn Ngày:", unique_dates_display)
                sel_date_raw = date_map[sel_date_display]
            else:
                # Chế độ tự động
                if best_day_raw:
                    st.success(f"✅ Đã chọn: **{translate_days(best_day_raw)}**")
                    st.caption(f"Lý do: Ngày này có khung giờ đạt đỉnh **{best_day_peak}** người rảnh.")
                    sel_date_raw = best_day_raw
                else:
                    st.error("Không tìm thấy ngày nào!")
                    sel_date_raw = unique_dates_raw[0]

        with c2:
            t_mode = st.radio("Giới hạn chung:", ["Cả ngày", "Sáng (<12h)", "Chiều (>12h)", "🔧 Tự nhập (Global)"], horizontal=True)

        global_start, global_end = 0.0, 24.0
        if t_mode == "Sáng (<12h)": global_start, global_end = 6.0, 12.0
        elif t_mode == "Chiều (>12h)": global_start, global_end = 12.0, 23.0
        elif t_mode == "🔧 Tự nhập (Global)":
            tc1, tc2 = st.columns(2)
            with tc1: g_s = st.time_input("Toàn bộ lịch từ:", value=time(13, 30))
            with tc2: g_e = st.time_input("Đến:", value=time(21, 0))
            global_start = g_s.hour + g_s.minute/60.0
            global_end = g_e.hour + g_e.minute/60.0

        mask_day = df['DateOnly'] == sel_date_raw
        df_day = df.loc[mask_day].reset_index(drop=True)
        df_ppl_day = df_people.loc[mask_day].reset_index(drop=True)
        
        if df_day.empty: st.warning("⚠️ Ngày này không có dữ liệu!"); st.stop()
        st.markdown("---")

        # NHẬP LIỆU
        st.header("📋 Thêm Bài Tập")
        with st.container():
            r1c1, r1c2 = st.columns([1, 1])
            with r1c1: t_name = st.text_input("Tên bài", placeholder="VD: Múa Quạt")
            with r1c2: 
                use_all = st.checkbox("Chọn tất cả")
                t_mem = all_members if use_all else st.multiselect("Thành viên", all_members, placeholder="Chọn người...")
            
            r2c1, r2c2 = st.columns([1, 1])
            with r2c1: t_dur = st.selectbox("Thời lượng", [45, 60, 90, 120, 150], index=1)
            with r2c2: 
                prio_options = {"🔥 VIP (Ưu tiên 1)": 1, "💎 Tiêu chuẩn (Ưu tiên 2)": 2, "🐢 Chốt sổ (Ưu tiên 3)": 3}
                t_prio_label = st.selectbox("Mức độ ưu tiên", list(prio_options.keys()), index=1)
                t_prio_val = prio_options[t_prio_label]

            with st.expander("⏳ Giới hạn giờ riêng (Nếu cần)", expanded=False):
                use_custom_time = st.checkbox("Bật giới hạn riêng")
                ct_start, ct_end = 0.0, 24.0
                if use_custom_time:
                    tc1, tc2 = st.columns(2)
                    with tc1: t_s = st.time_input("Chỉ bắt đầu từ:", value=time(14, 0))
                    with tc2: t_e = st.time_input("Phải xong trước:", value=time(17, 0))
                    ct_start = t_s.hour + t_s.minute/60.0
                    ct_end = t_e.hour + t_e.minute/60.0
            
            if st.button("➕ THÊM BÀI", type="primary", use_container_width=True):
                if t_name and t_mem:
                    st.session_state['tasks'].append({
                        "name": t_name, "members": t_mem, "duration": t_dur,
                        "prio_label": t_prio_label, "prio_val": t_prio_val,
                        "use_custom": use_custom_time, "c_start": ct_start, "c_end": ct_end
                    })
                    sort_tasks()
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        if st.session_state['tasks']:
            for i, t in enumerate(st.session_state['tasks']):
                c_card, c_del = st.columns([9, 0.5])
                with c_card:
                    prio_class = f"prio-{t['prio_val']}"
                    bg_class = f"bg-{t['prio_val']}"
                    short_label = "VIP" if t['prio_val']==1 else ("STD" if t['prio_val']==2 else "LAST")
                    time_tag = ""
                    if t['use_custom']:
                        h_s = int(t['c_start']); m_s = int((t['c_start']-h_s)*60)
                        h_e = int(t['c_end']); m_e = int((t['c_end']-h_e)*60)
                        time_tag = f"<span class='time-limit-tag'>⏰ {h_s:02}:{m_s:02} - {h_e:02}:{m_e:02}</span>"
                    st.markdown(f"""<div class="task-card {prio_class}"><span class="badge {bg_class}">{short_label}</span><span class="task-title"> {t['name']}</span> {time_tag}<div class="task-meta">⏱️ {t['duration']} phút • 👥 {len(t['members'])} thành viên</div></div>""", unsafe_allow_html=True)
                with c_del:
                    st.write(""); 
                    if st.button("✕", key=f"d{i}"): st.session_state['tasks'].pop(i); st.rerun()

            st.markdown("---")
            
            if st.button("🚀 CHẠY XẾP LỊCH", type="primary", use_container_width=True):
                occupied = [False] * len(df_day)
                final_schedule_list = []
                
                vip_tasks = [t for t in st.session_state['tasks'] if t['prio_val'] == 1]
                std_tasks = [t for t in st.session_state['tasks'] if t['prio_val'] == 2]
                last_tasks = [t for t in st.session_state['tasks'] if t['prio_val'] == 3]

                # 1. VIP
                for task in vip_tasks:
                    opts = analyze_task_options(task, df_day, df_ppl_day, occupied, global_start, global_end)
                    if opts:
                        best_opt = max(opts, key=lambda x: x['score'])
                        idx = best_opt['index']
                        slots = int(task['duration']/15)
                        for k in range(idx, idx+slots): occupied[k] = True
                        t_s = df_day.loc[idx, 'Time']; t_e = df_day.loc[idx+slots, 'Time'] if (idx+slots)<len(df_day) else "Hết"
                        miss = list(set(task['members']) - set(best_opt['attendees']))
                        final_schedule_list.append({"Loại": "VIP", "Bài": task['name'], "Thời gian": f"{t_s} - {t_e}", "Sĩ số": f"{best_opt['score']}/{len(task['members'])}", "Vắng": ", ".join(miss) if miss else "-", "sort_time": t_s})
                    else:
                        final_schedule_list.append({"Loại": "VIP", "Bài": task['name'], "Thời gian": "❌ Kẹt/Sai giờ", "Sĩ số": "0", "Vắng": "-", "sort_time": "Z"})

                # 2. STD (SCARCITY)
                while std_tasks:
                    candidates = []
                    for task in std_tasks:
                        options = analyze_task_options(task, df_day, df_ppl_day, occupied, global_start, global_end)
                        if not options: continue
                        max_score_possible = max(o['score'] for o in options)
                        best_options = [o for o in options if o['score'] == max_score_possible]
                        flexibility = len(best_options)
                        chosen_opt = best_options[0]
                        candidates.append({'task': task, 'score': max_score_possible, 'flexibility': flexibility, 'opt': chosen_opt})
                    
                    if not candidates:
                        for t in std_tasks: final_schedule_list.append({"Loại": "STD", "Bài": t['name'], "Thời gian": "❌ Kẹt/Sai giờ", "Sĩ số": "0", "Vắng": "-", "sort_time": "Z"})
                        break
                    
                    candidates.sort(key=lambda x: (x['score'], -x['flexibility'], len(x['task']['members'])), reverse=True)
                    winner = candidates[0]
                    task = winner['task']; idx = winner['opt']['index']; slots = int(task['duration']/15)
                    for k in range(idx, idx+slots): occupied[k] = True
                    t_s = df_day.loc[idx, 'Time']; t_e = df_day.loc[idx+slots, 'Time'] if (idx+slots)<len(df_day) else "Hết"
                    miss = list(set(task['members']) - set(winner['opt']['attendees']))
                    final_schedule_list.append({"Loại": "STD", "Bài": task['name'], "Thời gian": f"{t_s} - {t_e}", "Sĩ số": f"{winner['score']}/{len(task['members'])}", "Vắng": ", ".join(miss) if miss else "-", "sort_time": t_s})
                    std_tasks.remove(task)

                # 3. LAST
                for task in last_tasks:
                    opts = analyze_task_options(task, df_day, df_ppl_day, occupied, global_start, global_end)
                    if opts:
                        best_opt = max(opts, key=lambda x: x['score'])
                        idx = best_opt['index']; slots = int(task['duration']/15)
                        for k in range(idx, idx+slots): occupied[k] = True
                        t_s = df_day.loc[idx, 'Time']; t_e = df_day.loc[idx+slots, 'Time'] if (idx+slots)<len(df_day) else "Hết"
                        miss = list(set(task['members']) - set(best_opt['attendees']))
                        final_schedule_list.append({"Loại": "LAST", "Bài": task['name'], "Thời gian": f"{t_s} - {t_e}", "Sĩ số": f"{best_opt['score']}/{len(task['members'])}", "Vắng": ", ".join(miss) if miss else "-", "sort_time": t_s})
                    else:
                        final_schedule_list.append({"Loại": "LAST", "Bài": task['name'], "Thời gian": "❌ Kẹt/Sai giờ", "Sĩ số": "0", "Vắng": "-", "sort_time": "Z"})
                
                res = pd.DataFrame(final_schedule_list).sort_values(by="sort_time").drop(columns=["sort_time"])
                res['Thời gian'] = res['Thời gian'].apply(translate_days)
                st.dataframe(res, hide_index=True, use_container_width=True)
                st.download_button("📥 Tải CSV", res.to_csv(index=False).encode('utf-8-sig'), "Lich_Final.csv", "text/csv")

    except Exception as e: st.error(f"Lỗi: {e}")
