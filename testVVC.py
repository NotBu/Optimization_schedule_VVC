import streamlit as st
import pandas as pd

# Cấu hình trang
st.set_page_config(page_title="Xếp Lịch Tập Final", layout="wide")

# Khởi tạo Session State
if 'tasks' not in st.session_state:
    st.session_state['tasks'] = []

st.title("📅 Tool Xếp Lịch Tập")
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

        # 2. KHU VỰC THÊM BÀI TẬP
        st.header("2. Thêm Tiết mục")
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            task_name = st.text_input("Tên bài (VD: Trà và cà phê, Chốn sa mạc)", key="input_name")
        
        with col2:
            # Checkbox chọn tất cả
            use_all = st.checkbox("Chọn tất cả thành viên")
            if use_all:
                selected_members = all_members
                st.write(f"Đã chọn: Tất cả ({len(all_members)} người)")
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
                st.rerun() # Refresh lại để hiện danh sách mới ngay

        # HIỂN THỊ DANH SÁCH BÀI (CÓ NÚT XÓA)
        if st.session_state['tasks']:
            st.subheader("📋 Danh sách cần xếp:")
            st.markdown("---")
            
            # Vòng lặp hiển thị từng bài
            for i, task in enumerate(st.session_state['tasks']):
                c1, c2 = st.columns([5, 1]) # Chia cột: Cột tin to, Cột nút xóa nhỏ
                
                with c1:
                    st.write(f"**{i+1}. {task['name']}** - ⏱️ {task['duration']}p - 👥 {len(task['members'])} người")
                    with st.expander("Xem chi tiết thành viên"):
                        st.write(", ".join(task['members']))
                
                with c2:
                    # Nút xóa từng bài
                    if st.button("❌ Xóa", key=f"delete_{i}"):
                        st.session_state['tasks'].pop(i) # Xóa khỏi list
                        st.rerun() # Load lại trang ngay lập tức
            
            st.markdown("---")
            if st.button("🗑️ Xóa tất cả làm lại từ đầu"):
                st.session_state['tasks'] = []
                st.rerun()

            st.markdown("---")

            # 3. CẤU HÌNH XẾP LỊCH
            st.header("3. Xếp Lịch & Tối Ưu")
            
            session_option = st.radio(
                "🎯 Xếp lịch theo:",
                ("Tự động (Ưu tiên đông nhất)", "Chỉ xếp Sáng", "Chỉ xếp Chiều", "Cả ngày"),
                horizontal=True
            )

            if st.button("🚀 BẮT ĐẦU XẾP LỊCH"):
                
                # --- LỌC DỮ LIỆU ---
                df_process = df.copy()
                df_people_process = df_people.copy()
                target_session = ""
                
                if session_option == "Chỉ xếp Sáng": target_session = "Sáng"
                elif session_option == "Chỉ xếp Chiều": target_session = "Chiều"
                elif session_option == "Tự động (Ưu tiên đông nhất)":
                    involved = set()
                    for t in st.session_state['tasks']: involved.update(t['members'])
                    involved = list(involved)
                    if not involved: involved = all_members
                    score_sang = df_people_process.loc[df['Session'] == "Sáng", involved].sum().sum()
                    score_chieu = df_people_process.loc[df['Session'] == "Chiều", involved].sum().sum()
                    target_session = "Sáng" if score_sang > score_chieu else "Chiều"
                    st.info(f"💡 Đã chọn buổi: **{target_session.upper()}** (Sáng: {score_sang} vs Chiều: {score_chieu})")

                if target_session:
                    mask = df['Session'] == target_session
                    df_process = df.loc[mask].reset_index(drop=True)
                    df_people_process = df_people.loc[mask].reset_index(drop=True)
                
                if df_process.empty:
                    st.error("Không có dữ liệu cho buổi đã chọn!")
                    st.stop()

                # --- THUẬT TOÁN XẾP LỊCH ---
                occupied_slots = [False] * len(df_process)
                final_schedule = []
                sorted_tasks = sorted(st.session_state['tasks'], key=lambda x: (len(x['members']), x['duration']), reverse=True)
                
                for task in sorted_tasks:
                    slots_needed = int(task['duration'] / 15)
                    members = task['members']
                    
                    best_score = -1
                    best_start_index = -1
                    best_attendees = []
                    
                    # QUÉT TÌM GIỜ
                    for i in range(len(df_process) - slots_needed + 1):
                        if any(occupied_slots[i : i + slots_needed]): continue
                        
                        block_data = df_people_process.iloc[i : i + slots_needed][members]
                        
                        # Ai đi được full slot
                        attendee_counts = block_data.sum(axis=0)
                        fully_available_people = attendee_counts[attendee_counts == slots_needed].index.tolist()
                        
                        num_attendees = len(fully_available_people)
                        
                        # Bonus dồn lịch
                        bonus = 0
                        if i > 0 and occupied_slots[i-1]: bonus = 0.5
                        if (i + slots_needed) < len(occupied_slots) and occupied_slots[i + slots_needed]: bonus = 0.5
                        
                        current_score = num_attendees + bonus
                        
                        if current_score > best_score:
                            best_score = current_score
                            best_start_index = i
                            best_attendees = fully_available_people
                            
                    # LƯU KẾT QUẢ
                    if best_start_index != -1:
                        for k in range(best_start_index, best_start_index + slots_needed):
                            occupied_slots[k] = True
                            
                        start_time = df_process.loc[best_start_index, 'Time']
                        end_time = df_process.loc[best_start_index + slots_needed, 'Time'] if (best_start_index + slots_needed) < len(df_process) else "Hết"
                        
                        missing_people = list(set(members) - set(best_attendees))
                        
                        final_schedule.append({
                            "Bài tập": task['name'],
                            "Thời gian": f"{start_time} - {end_time}",
                            "Số người": f"{len(best_attendees)}/{len(members)}",
                            "Đi được": ", ".join(best_attendees),
                            "Vắng": ", ".join(missing_people) if missing_people else "Đủ 100%"
                        })
                    else:
                        final_schedule.append({
                            "Bài tập": task['name'],
                            "Thời gian": "❌ Kẹt lịch",
                            "Số người": "0",
                            "Đi được": "-",
                            "Vắng": "Toàn bộ"
                        })

                # HIỂN THỊ
                result_df = pd.DataFrame(final_schedule)
                result_df = result_df.sort_values(by="Thời gian")
                
                st.table(result_df)
                
                csv = result_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Tải Lịch Về Excel", csv, "Lich_Tap_Final_V4.csv", "text/csv")

    except Exception as e:
        st.error(f"Lỗi: {e}")