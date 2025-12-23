import streamlit as st
import pandas as pd

# Cấu hình trang
st.set_page_config(page_title="Xếp Lịch Tập Final", layout="wide")

# Khởi tạo Session State
if 'tasks' not in st.session_state:
    st.session_state['tasks'] = []

st.title("📅 Tool Xếp Lịch")
st.markdown("---")

# 1. UPLOAD FILE
st.sidebar.header("1. Nhập dữ liệu")
uploaded_file = st.sidebar.file_uploader("Upload file CSV when2meet", type=['csv'])

# HÀM XỬ LÝ DỮ LIỆU
def load_data(file):
    df = pd.read_csv(file)
    time_col = df.columns[0]
    people_cols = df.columns[1:]
    # Chuẩn hóa 1/0
    df_people = df[people_cols].fillna(0).apply(pd.to_numeric, errors='coerce').fillna(0)
    df['Time'] = df[time_col]
    
    # Phân loại Sáng/Chiều
    def classify_session(time_str):
        ts = str(time_str).upper()
        if "AM" in ts: return "Sáng"
        if "PM" in ts: 
            if "12 PM" in ts: return "Chiều"
            return "Chiều"
        try:
            for part in ts.split():
                if ":" in part:
                    hour = int(part.split(":")[0])
                    if hour < 12: return "Sáng"
                    else: return "Chiều"
        except: pass
        return "Không xác định"

    df['Session'] = df['Time'].apply(classify_session)
    return df, df_people, list(people_cols)

if uploaded_file is not None:
    try:
        df, df_people, all_members = load_data(uploaded_file)
        st.sidebar.success(f"Đã tải! {len(all_members)} thành viên.")

        # --- TÍNH NĂNG MỚI: ADMIN TOOLS ---
        st.header("🛠️ Công cụ lấy file excel")
        st.info("Bấm nút dưới đây để tải file Excel tổng hợp tất cả dữ liệu.")
        
        # Xử lý tạo file Admin
        if st.button("📥 Tải File Dữ Liệu Tổng Hợp (Master File)"):
            # Tạo dataframe mới
            df_admin = pd.DataFrame()
            df_admin['Thời gian'] = df['Time']
            df_admin['Buổi'] = df['Session']
            
            # Đếm tổng người rảnh
            df_admin['Tổng người rảnh'] = df_people.sum(axis=1)
            
            # Liệt kê tên (Hàm này thay cho TEXTJOIN trong Excel)
            def get_names_str(row):
                # Lấy tên cột mà giá trị là 1
                return ", ".join(row.index[row == 1].tolist())
            
            df_admin['Danh sách người rảnh'] = df_people.apply(get_names_str, axis=1)
            
            # Convert sang CSV
            csv_admin = df_admin.to_csv(index=False).encode('utf-8-sig')
            
            st.download_button(
                label="⬇️ Click để tải Master File về máy",
                data=csv_admin,
                file_name="Master_Data_Admin.csv",
                mime="text/csv"
            )
        
        st.markdown("---")

        # 2. KHU VỰC THÊM BÀI TẬP (GIỮ NGUYÊN)
        st.header("2. Xếp Lịch Tập (Dành cho các bài cụ thể)")
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            task_name = st.text_input("Tên bài (VD: Trà và cà phê, Chốn sa mạc)", key="input_name")
        with col2:
            use_all = st.checkbox("✅ Chọn tất cả thành viên")
            if use_all:
                selected_members = all_members
            else:
                selected_members = st.multiselect("Thành viên tham gia:", all_members, key="input_members")
        with col3:
            duration = st.selectbox("Thời lượng:", [45, 60, 90, 120, 150], index=1, key="input_duration")

        if st.button("➕ Thêm vào danh sách"):
            if task_name and selected_members:
                st.session_state['tasks'].append({
                    "name": task_name,
                    "members": selected_members,
                    "duration": duration
                })
                st.success(f"Đã thêm: {task_name}")
                st.rerun()

        # DANH SÁCH BÀI & NÚT XÓA
        if st.session_state['tasks']:
            st.subheader("📋 Danh sách cần xếp:")
            st.markdown("---")
            for i, task in enumerate(st.session_state['tasks']):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.write(f"**{i+1}. {task['name']}** - ⏱️ {task['duration']}p - 👥 {len(task['members'])} người")
                    with st.expander("Chi tiết"):
                        st.write(", ".join(task['members']))
                with c2:
                    if st.button("❌ Xóa", key=f"del_{i}"):
                        st.session_state['tasks'].pop(i)
                        st.rerun()
            
            if st.button("🗑️ Xóa tất cả"):
                st.session_state['tasks'] = []
                st.rerun()

            st.markdown("---")

            # 3. CẤU HÌNH XẾP LỊCH
            st.header("3. Xếp Lịch")
            session_option = st.radio("🎯 Chế độ gom buổi:", ("Tự động", "Sáng", "Chiều", "Cả ngày"), horizontal=True)

            if st.button("🚀 XẾP LỊCH NGAY"):
                # (Logic xếp lịch giữ nguyên như V4)
                df_process = df.copy()
                df_people_process = df_people.copy()
                target_session = ""
                
                if session_option == "Sáng": target_session = "Sáng"
                elif session_option == "Chiều": target_session = "Chiều"
                elif session_option == "Tự động":
                    involved = set()
                    for t in st.session_state['tasks']: involved.update(t['members'])
                    involved = list(involved) if involved else all_members
                    score_sang = df_people_process.loc[df['Session'] == "Sáng", involved].sum().sum()
                    score_chieu = df_people_process.loc[df['Session'] == "Chiều", involved].sum().sum()
                    target_session = "Sáng" if score_sang > score_chieu else "Chiều"
                    st.info(f"💡 Đã chọn: **{target_session.upper()}**")

                if target_session:
                    mask = df['Session'] == target_session
                    df_process = df.loc[mask].reset_index(drop=True)
                    df_people_process = df_people.loc[mask].reset_index(drop=True)
                
                if df_process.empty:
                    st.error("Lỗi: Không có dữ liệu buổi này!")
                    st.stop()

                occupied_slots = [False] * len(df_process)
                final_schedule = []
                sorted_tasks = sorted(st.session_state['tasks'], key=lambda x: (len(x['members']), x['duration']), reverse=True)
                
                for task in sorted_tasks:
                    slots_needed = int(task['duration'] / 15)
                    members = task['members']
                    best_score = -1
                    best_start_index = -1
                    best_attendees = []
                    
                    for i in range(len(df_process) - slots_needed + 1):
                        if any(occupied_slots[i : i + slots_needed]): continue
                        
                        block_data = df_people_process.iloc[i : i + slots_needed][members]
                        attendee_counts = block_data.sum(axis=0)
                        fully_available_people = attendee_counts[attendee_counts == slots_needed].index.tolist()
                        
                        bonus = 0
                        if i > 0 and occupied_slots[i-1]: bonus = 0.5
                        if (i + slots_needed) < len(occupied_slots) and occupied_slots[i + slots_needed]: bonus = 0.5
                        
                        current_score = len(fully_available_people) + bonus
                        
                        if current_score > best_score:
                            best_score = current_score
                            best_start_index = i
                            best_attendees = fully_available_people
                            
                    if best_start_index != -1:
                        for k in range(best_start_index, best_start_index + slots_needed):
                            occupied_slots[k] = True
                        start_time = df_process.loc[best_start_index, 'Time']
                        end_time = df_process.loc[best_start_index + slots_needed, 'Time'] if (best_start_index + slots_needed) < len(df_process) else "Hết"
                        missing = list(set(members) - set(best_attendees))
                        
                        final_schedule.append({
                            "Bài tập": task['name'],
                            "Thời gian": f"{start_time} - {end_time}",
                            "Số lượng": f"{len(best_attendees)}/{len(members)}",
                            "Đi được": ", ".join(best_attendees),
                            "Vắng": ", ".join(missing) if missing else "Đủ"
                        })
                    else:
                        final_schedule.append({"Bài tập": task['name'], "Thời gian": "Kẹt lịch", "Số lượng": "0", "Đi được": "-", "Vắng": "-"})

                result_df = pd.DataFrame(final_schedule).sort_values(by="Thời gian")
                st.table(result_df)
                csv = result_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Tải Lịch Chi Tiết", csv, "Lich_Tap_Final.csv", "text/csv")

    except Exception as e:
        st.error(f"Lỗi: {e}")
