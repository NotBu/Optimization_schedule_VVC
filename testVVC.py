import streamlit as st
import pandas as pd
import re
import time
from datetime import time as dt_time

# ==========================================
# 1. CẤU HÌNH & CHANGELOG
# ==========================================
CURRENT_VERSION = "V2.1.1"

CHANGELOG = {
    "V2.2.1": [
        " FIX lỗi: Tool đọc nhầm ngày (04 Jan) thành giờ (04:00).",
        " Cập nhật bộ đọc dữ liệu: Chỉ nhận diện giờ khi có dấu hai chấm (VD: 9:53)."
    ]
}

st.set_page_config(page_title=f"Tool xếp lịch tập VVC", layout="wide")

if 'seen_version' not in st.session_state: st.session_state['seen_version'] = None
if st.session_state['seen_version'] != CURRENT_VERSION:
    time.sleep(2.5)
    st.toast(f"Đã fix lỗi lệch giờ ở bản {CURRENT_VERSION}!")
    st.toast(f" Xem nội dung cập nhật ở phần 'Cập nhật' thanh bên ")
    time.sleep(2.0)
    st.session_state['seen_version'] = CURRENT_VERSION

# --- CSS DARK MODE ---
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

# ==========================================
# 2. HÀM XỬ LÝ (QUAN TRỌNG: ĐÃ SỬA LỖI)
# ==========================================
WEEKDAY_MAP = {"Monday": "Thứ 2", "Tuesday": "Thứ 3", "Wednesday": "Thứ 4", "Thursday": "Thứ 5", "Friday": "Thứ 6", "Saturday": "Thứ 7", "Sunday": "CN"}

def translate_days(text):
    txt = str(text)
    for eng, vie in WEEKDAY_MAP.items(): 
        if eng in txt: txt = txt.replace(eng, vie)
    return txt

def format_pretty_time(start_str, end_str):
    if str(end_str) == "Hết": return f"{start_str} - Hết"
    
    def extract_hm_ampm(s):
        s = str(s).upper()
        # Regex này đảm bảo chỉ lấy đúng cụm giờ:phút
        match = re.search(r'(\d{1,2}):(\d{2})', s)
        ampm_match = re.search(r'(AM|PM)', s)
        hm = ""; ampm = ""
        if match: hm = f"{int(match.group(1))}h{match.group(2)}"
        if ampm_match: ampm = ampm_match.group(1)
        return hm, ampm

    s_hm, s_ampm = extract_hm_ampm(start_str)
    e_hm, e_ampm = extract_hm_ampm(end_str)
    
    time_range = ""
    if s_ampm and e_ampm:
        if s_ampm == e_ampm: time_range = f"{s_hm} - {e_hm} {e_ampm}"
        else: time_range = f"{s_hm} {s_ampm} - {e_hm} {e_ampm}"
    else: time_range = f"{s_hm} - {e_hm}"
    return time_range

# --- 🛠️ HÀM NÀY ĐÃ ĐƯỢC SỬA ĐỂ KHÔNG BẮT NHẦM NGÀY ---
def parse_hour_value(time_str):
    ts = str(time_str).upper().strip()
    hour = 0; minute = 0
    
    # Code CŨ: re.findall(r'\d+', ts) -> Bắt nhầm số "04" trong ngày "04 Jan"
    # Code MỚI: Chỉ bắt số nếu nó nằm trong định dạng HH:MM
    match = re.search(r'(\d{1,2}):(\d{2})', ts)
    
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        
        # Xử lý AM/PM
        is_pm = "PM" in ts
        if is_pm and hour < 12: hour += 12
        if not is_pm and hour == 12: hour = 0
    else:
        # Fallback (Phòng hờ)
        return 0.0
        
    return hour + minute/60.0

def load_data(file):
    df = pd.read_csv(file)
    time_col = df.columns[0]; people_cols = df.columns[1:]
    df_people = df[people_cols].fillna(0).apply(pd.to_numeric, errors='coerce').fillna(0)
    df['Time'] = df[time_col]
    df['HourVal'] = df['Time'].apply(parse_hour_value)
    
    # Sửa luôn cái hàm lấy ngày để nó cắt chuỗi thông minh hơn
    def extract_strict_date(t_str):
        s = str(t_str).strip()
        # Cắt chuỗi tại chỗ có giờ (VD: 05:30) và lấy phần phía trước
        parts = re.split(r'\d{1,2}:\d{2}', s)
        if parts:
            return parts[0].strip() # Trả về "Sun 04 Jan 2026"
        return s
        
    df['DateOnly'] = df['Time'].apply(extract_strict_date)
    return df, df_people, list(people_cols)

def sort_tasks():
    st.session_state['tasks'] = sorted(st.session_state['tasks'], key=lambda x: x['prio_val'])

def analyze_task_on_specific_day(task, day_raw, df_day, df_ppl_day, occupied_mask, global_start, global_end):
    slots_needed = int(task['duration'] / 15)
    curr_mems = task['members']
    v_start = global_start 
    v_end = global_end
    if task['use_custom']: v_end = min(global_end, task['c_end'])
    
    options = []
    
    for i in range(len(df_day) - slots_needed + 1):
        s_time = df_day.loc[i, 'HourVal']
        e_time = df_day.loc[min(i+slots_needed, len(df_day)-1), 'HourVal']
        if i+slots_needed >= len(df_day): e_time = 24.0
        
        if s_time < v_start or e_time > v_end: continue
        if any(occupied_mask[i:i+slots_needed]): continue
        
        block = df_ppl_day.iloc[i:i+slots_needed][curr_mems]
        counts = block.sum(axis=0)
        full_ppl = counts[counts == slots_needed].index.tolist()
        score = len(full_ppl)
        
        options.append({
            'date': day_raw,
            'index': i,
            'score': score,
            'attendees': full_ppl,
            'start_time': df_day.loc[i, 'Time'],
            'end_time': df_day.loc[min(i+slots_needed, len(df_day)-1), 'Time']
        })
    return options

# ==========================================
# 3. GIAO DIỆN CHÍNH
# ==========================================
st.sidebar.title(f"{CURRENT_VERSION}")
with st.sidebar.expander("Cập nhật"):
    for ver, notes in CHANGELOG.items():
        st.write(f"**{ver}**"); 
        for n in notes: st.caption(f"- {n}")
        st.divider()
st.sidebar.header("📥 Dữ liệu nguồn")
uploaded_file = st.sidebar.file_uploader("Thả file CSV vào đây", type=['csv'])

st.title(f"Tool xếp lịch VVC")
st.markdown("---")

if uploaded_file is not None:
    try:
        df, df_people, all_members = load_data(uploaded_file)
        unique_dates_raw = df['DateOnly'].unique().tolist()
        unique_dates_display = [translate_days(d) for d in unique_dates_raw]
        date_map = dict(zip(unique_dates_display, unique_dates_raw))
        
        st.sidebar.success(f"Đã tải: {len(unique_dates_raw)} ngày.")
        
        st.header("Cấu hình Tuần Tập")
        c1, c2 = st.columns([1.5, 2])
        with c1:
            selected_days_display = st.multiselect("Chọn những ngày có thể tập:", unique_dates_display, default=unique_dates_display[:1])
            selected_days_raw = [date_map[d] for d in selected_days_display]
        with c2:
            t_mode = st.radio("Giới hạn chung:", ["Cả ngày", "Sáng (<12h)", "Chiều (>12h)", "Tự nhập (Global)"], horizontal=True)

        global_start, global_end = 0.0, 24.0
        if t_mode == "Sáng (<12h)": global_start, global_end = 6.0, 12.0
        elif t_mode == "Chiều (>12h)": global_start, global_end = 12.0, 23.0
        elif t_mode == "Tự nhập (Global)":
            tc1, tc2 = st.columns(2)
            with tc1: g_s = st.time_input("Từ:", value=dt_time(13, 30))
            with tc2: g_e = st.time_input("Đến:", value=dt_time(21, 0))
            global_start = g_s.hour + g_s.minute/60.0; global_end = g_e.hour + g_e.minute/60.0

        if not selected_days_raw: st.warning("Vui lòng chọn ít nhất 1 ngày!"); st.stop()
        st.markdown("---")

        st.header("Thêm Bài Tập & Tần Suất")
        with st.container():
            r1c1, r1c2 = st.columns([1, 1])
            with r1c1: t_name = st.text_input("Tên bài", placeholder="VD: Trà và cà phê")
            with r1c2: 
                use_all = st.checkbox("Chọn tất cả")
                t_mem = all_members if use_all else st.multiselect("Thành viên", all_members, placeholder="Chọn người...")
            
            r2c1, r2c2, r2c3 = st.columns([1, 1, 1])
            with r2c1: t_dur = st.selectbox("Thời lượng", [45, 60, 90, 120, 150], index=1)
            with r2c2: 
                try: max_freq = len(selected_days_raw) 
                except: max_freq = 1
                t_freq = st.number_input(f"Số buổi/tuần (Max {max_freq})", min_value=1, max_value=max_freq, value=1)
            with r2c3: 
                prio_options = {" Tối ưu nhất": 1, "Cơ bản": 2, "Xếp cuối": 3}
                t_prio_label = st.selectbox("Ưu tiên", list(prio_options.keys()), index=1)
                t_prio_val = prio_options[t_prio_label]

            with st.expander("Đặt giờ kết thúc bài tập", expanded=False):
                use_custom_time = st.checkbox("Đặt giờ kết thúc bắt buộc")
                ct_end = 24.0
                if use_custom_time:
                    t_e = st.time_input("Phải xong TRƯỚC:", value=dt_time(17, 0))
                    ct_end = t_e.hour + t_e.minute/60.0
            
            if st.button(" THÊM BÀI", type="primary", use_container_width=True):
                if t_name and t_mem:
                    st.session_state['tasks'].append({
                        "name": t_name, "members": t_mem, "duration": t_dur,
                        "prio_label": t_prio_label, "prio_val": t_prio_val,
                        "freq": t_freq, "use_custom": use_custom_time, "c_start": 0.0, "c_end": ct_end
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
                    freq_badge = f"<span class='badge' style='background-color: #4b5563;'>{t['freq']} buổi/tuần</span>"
                    time_tag = ""
                    if t['use_custom']:
                        h_e = int(t['c_end']); m_e = int((t['c_end']-h_e)*60)
                        time_tag = f"<span class='time-limit-tag'>🏁 Trước {h_e:02}:{m_e:02}</span>"
                    st.markdown(f"""<div class="task-card {prio_class}"><span class="badge {bg_class}">{short_label}</span>{freq_badge}<span class="task-title"> {t['name']}</span> {time_tag}<div class="task-meta">⏱️ {t['duration']} phút • 👥 {len(t['members'])} thành viên</div></div>""", unsafe_allow_html=True)
                with c_del:
                    st.write(""); 
                    if st.button("✕", key=f"d{i}"): st.session_state['tasks'].pop(i); st.rerun()

            st.markdown("---")
            
            if st.button("CHẠY THUẬT TOÁN ", type="primary", use_container_width=True):
                occupied_map = {}
                df_day_map = {}
                df_ppl_map = {}
                
                for day in selected_days_raw:
                    mask = df['DateOnly'] == day
                    d_df = df.loc[mask].reset_index(drop=True)
                    p_df = df_people.loc[mask].reset_index(drop=True)
                    if not d_df.empty:
                        df_day_map[day] = d_df
                        df_ppl_map[day] = p_df
                        occupied_map[day] = [False] * len(d_df)
                
                final_schedule = []
                vip_tasks = [t for t in st.session_state['tasks'] if t['prio_val'] == 1]
                std_tasks = [t for t in st.session_state['tasks'] if t['prio_val'] == 2]
                last_tasks = [t for t in st.session_state['tasks'] if t['prio_val'] == 3]
                
                def schedule_single_task(task_obj, is_scarcity_mode=False):
                    all_possible_slots = []
                    for day in selected_days_raw:
                        if day not in df_day_map: continue
                        opts = analyze_task_on_specific_day(task_obj, day, df_day_map[day], df_ppl_map[day], occupied_map[day], global_start, global_end)
                        all_possible_slots.extend(opts)
                    
                    if is_scarcity_mode: return all_possible_slots
                    
                    all_possible_slots.sort(key=lambda x: x['score'], reverse=True)
                    sessions_needed = task_obj['freq']; sessions_booked = 0
                    booked_days = set()
                    
                    # Pass 1
                    for opt in all_possible_slots:
                        if sessions_booked >= sessions_needed: break
                        idx = opt['index']; day = opt['date']; slots = int(task_obj['duration']/15)
                        if any(occupied_map[day][idx:idx+slots]): continue
                        if day in booked_days: continue
                        
                        for k in range(idx, idx+slots): occupied_map[day][k] = True
                        miss = list(set(task_obj['members']) - set(opt['attendees']))
                        p_time = format_pretty_time(opt['start_time'], opt['end_time'])
                        p_name = "VIP" if task_obj['prio_val']==1 else ("STD" if task_obj['prio_val']==2 else "LAST")
                        final_schedule.append({"Ngày": translate_days(day), "Loại": p_name, "Bài": task_obj['name'], "Thời gian": p_time, "Sĩ số": f"{opt['score']}/{len(task_obj['members'])}", "Vắng": ", ".join(miss) if miss else "-", "sort_key": f"{day} {opt['start_time']}"})
                        booked_days.add(day); sessions_booked += 1
                        
                    # Pass 2
                    if sessions_booked < sessions_needed:
                        for opt in all_possible_slots:
                            if sessions_booked >= sessions_needed: break
                            idx = opt['index']; day = opt['date']; slots = int(task_obj['duration']/15)
                            if any(occupied_map[day][idx:idx+slots]): continue
                            
                            for k in range(idx, idx+slots): occupied_map[day][k] = True
                            miss = list(set(task_obj['members']) - set(opt['attendees']))
                            p_time = format_pretty_time(opt['start_time'], opt['end_time'])
                            p_name = "VIP" if task_obj['prio_val']==1 else ("STD" if task_obj['prio_val']==2 else "LAST")
                            final_schedule.append({"Ngày": translate_days(day), "Loại": p_name, "Bài": task_obj['name'], "Thời gian": p_time, "Sĩ số": f"{opt['score']}/{len(task_obj['members'])}", "Vắng": ", ".join(miss) if miss else "-", "sort_key": f"{day} {opt['start_time']}"})
                            sessions_booked += 1
                            
                    if sessions_booked < sessions_needed:
                        for _ in range(sessions_needed - sessions_booked):
                            p_name = "VIP" if task_obj['prio_val']==1 else ("STD" if task_obj['prio_val']==2 else "LAST")
                            final_schedule.append({"Ngày": "-", "Loại": p_name, "Bài": task_obj['name'], "Thời gian": "❌ Thiếu slot", "Sĩ số": "0", "Vắng": "-", "sort_key": "ZZZ"})

                for t in vip_tasks: schedule_single_task(t)
                
                while std_tasks:
                    candidates = []
                    for task in std_tasks:
                        opts = schedule_single_task(task, is_scarcity_mode=True)
                        if not opts: candidates.append({'task': task, 'score': -1, 'flexibility': 9999, 'opts': []}); continue
                        max_score = max(o['score'] for o in opts)
                        best_opts = [o for o in opts if o['score'] == max_score]
                        flexibility = len(best_opts)
                        candidates.append({'task': task, 'score': max_score, 'flexibility': flexibility, 'opts': best_opts})
                    
                    candidates.sort(key=lambda x: (x['score'], -x['flexibility'], len(x['task']['members'])), reverse=True)
                    if not candidates: break
                    winner = candidates[0]; task = winner['task']
                    schedule_single_task(task, is_scarcity_mode=False)
                    std_tasks.remove(task)

                for t in last_tasks: schedule_single_task(t)
                
                res = pd.DataFrame(final_schedule).sort_values(by="sort_key").drop(columns=["sort_key"])
                st.dataframe(res, hide_index=True, use_container_width=True)
                st.download_button("📥 Tải Lịch Tuần (CSV)", res.to_csv(index=False).encode('utf-8-sig'), "Lich_Tuan.csv", "text/csv")

    except Exception as e: st.error(f"Lỗi: {e}")
