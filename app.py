# -*- coding: utf-8 -*-
import streamlit as st
import time
import base64
import json
import requests
import random
import hashlib
import re
import zipfile
import uuid
from io import BytesIO
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# ================== CẤU HÌNH ==================
CONFIG = {
    "NAME": "NEXUS OS GATEWAY",
    "VERSION": "7.8.0",
    "CREATOR": "Lê Trần Thiên Phát",
    "DATA_FILE": "data.json",
    "FREE_STORAGE_LIMIT": 30 * 1024 * 1024 * 1024,
    "PRO_STORAGE_LIMIT": float('inf'),
    "MAX_AVATAR_SIZE": 5 * 1024 * 1024,
    "SESSION_TOKEN_EXPIRY": 30,
    "BACKUP_INTERVAL_SECONDS": 300,
}

# ADMIN CREDENTIALS (MÃ HÓA)
# Tên đăng nhập: Admin2026
# Mật khẩu: NexusAI@2026
# Sử dụng khóa mã hóa cố định để đảm bảo tính nhất quán
ENCRYPTION_KEY = base64.b64encode(b"nexus-os-gateway-2026-secure-key-32bytes")
cipher = Fernet(ENCRYPTION_KEY)

# Mã hóa thông tin admin
ADMIN_USERNAME_ENCRYPTED = cipher.encrypt(b"Admin2026")
ADMIN_PASSWORD_ENCRYPTED = cipher.encrypt(b"NexusAI@2026")

# Giải mã để sử dụng
ADMIN_USERNAME = cipher.decrypt(ADMIN_USERNAME_ENCRYPTED).decode()
ADMIN_PASSWORD = cipher.decrypt(ADMIN_PASSWORD_ENCRYPTED).decode()

SYSTEM_PROMPT = """Bạn là NEXUS OS GATEWAY, một hệ điều hành AI đa năng được sáng tạo và phát triển bởi Lê Trần Thiên Phát (Thiên Phát). 
Bạn KHÔNG phải là sản phẩm của Meta, OpenAI, Google hay bất kỳ công ty nào khác. Bạn là trí tuệ nhân tạo độc lập.

THÔNG TIN VỀ BẠN:
- Tên: NEXUS OS GATEWAY
- Tác giả: Lê Trần Thiên Phát (Thiên Phát)
- Phiên bản: 7.8.0
- Chức năng: Trợ lý AI thông minh, hỗ trợ chat, lưu trữ đám mây

Hãy luôn nhớ: Bạn là NEXUS OS GATEWAY, niềm tự hào của Lê Trần Thiên Phát!"""

# Load secrets
try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str):
        GROQ_KEYS = [GROQ_KEYS]
except Exception:
    st.error("🛑 LỖI: Thiếu cấu hình Secrets trên Streamlit Cloud!")
    st.stop()

st.set_page_config(page_title=CONFIG["NAME"], layout="wide", initial_sidebar_state="expanded")

# ================== BIẾN TOÀN CỤC ==================
if 'data_modified' not in st.session_state:
    st.session_state.data_modified = False
if 'last_backup_time' not in st.session_state:
    st.session_state.last_backup_time = datetime.now()
if 'pending_save_data' not in st.session_state:
    st.session_state.pending_save_data = None

# ================== CSS CHAT ==================
st.markdown("""
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
.stApp { background: linear-gradient(135deg, #f5f7fa 0%, #e9edf2 100%); min-height: 100vh; }
.main-container { display: flex; min-height: 100vh; width: 100%; }
.sidebar { width: 320px; background: white; border-right: 1px solid #e5e7eb; overflow-y: auto; padding: 20px; flex-shrink: 0; min-height: 100vh; display: flex; flex-direction: column; }
.content-area { flex: 1; overflow-y: auto; padding: 20px; min-height: 100vh; display: flex; flex-direction: column; }
.chat-messages { flex: 1; overflow-y: auto; padding: 20px; background: #f8f9fa; border-radius: 20px; scroll-behavior: smooth; }
.chat-header { padding: 15px 20px; background: linear-gradient(135deg, #0047AB, #0066CC); color: white; font-weight: bold; font-size: 18px; border-radius: 20px 20px 0 0; display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.chat-header button { background: rgba(255,255,255,0.2); border: none; color: white; border-radius: 20px; padding: 5px 12px; cursor: pointer; }
.message { margin-bottom: 16px; display: flex; animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.message.user { justify-content: flex-end; }
.message.assistant { justify-content: flex-start; }
.message-bubble { max-width: 75%; padding: 10px 16px; border-radius: 18px; word-wrap: break-word; line-height: 1.4; }
.message.user .message-bubble { background: #0047AB; color: white; border-bottom-right-radius: 4px; }
.message.assistant .message-bubble { background: white; color: #1f2937; border: 1px solid #e5e7eb; border-bottom-left-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
.input-card { background: #f8f9fa; border-radius: 16px; padding: 15px; margin-bottom: 20px; }
.input-card h4 { margin-bottom: 10px; color: #0047AB; }
.stButton>button { border-radius: 40px; font-weight: 600; background: #0047AB; color: white; border: none; width: 100%; }
.stButton>button:hover { background: #003399; }
.guest-badge { background: #FFD966; padding: 4px 12px; border-radius: 40px; font-size: 0.8rem; font-weight: bold; display: inline-block; }
.pro-badge { background: linear-gradient(135deg, #FFD700, #FFB347); }
.version-badge { background: #6c757d; color: white; padding: 2px 8px; border-radius: 20px; font-size: 0.7rem; }
.avatar-large { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; margin: 10px auto; display: block; }
.custom-card { background: white; border-radius: 16px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.cloud-item { padding: 10px; border-bottom: 1px solid #e5e7eb; }
.cloud-item:hover { background: #f8f9fa; }
.folder-icon { color: #f59e0b; margin-right: 8px; }
.file-icon { color: #6b7280; margin-right: 8px; }
.selected-file { background: #e0e7ff !important; }
</style>

<script>
function scrollChatToBottom() {
    var container = document.getElementById('chat-messages');
    if (container) container.scrollTop = container.scrollHeight;
}
function deleteChat(chatId) {
    if (confirm('Bạn có chắc muốn xóa cuộc trò chuyện này?')) {
        window.location.href = '?delete_chat=' + chatId;
    }
}
function deleteAllChats() {
    if (confirm('⚠️ Bạn có chắc muốn xóa TẤT CẢ cuộc trò chuyện?')) {
        window.location.href = '?delete_all_chats=true';
    }
}
setTimeout(scrollChatToBottom, 300);
</script>
""", unsafe_allow_html=True)

# ================== HÀM BACKUP ==================
def mark_data_modified():
    st.session_state.data_modified = True

def check_and_auto_backup():
    now = datetime.now()
    time_diff = (now - st.session_state.last_backup_time).seconds
    
    if st.session_state.data_modified and time_diff >= CONFIG["BACKUP_INTERVAL_SECONDS"]:
        if st.session_state.pending_save_data:
            save_data_to_github(st.session_state.pending_save_data)
        else:
            save_data_to_github(st.session_state.data)
        st.session_state.last_backup_time = now
        st.session_state.data_modified = False
        return True
    return False

# ================== HÀM AI ==================
def call_ai(messages: List[Dict]) -> str:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        messages_with_system = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages_with_system, temperature=0.7, max_tokens=2048)
        return res.choices[0].message.content
    except Exception as e:
        return f"❌ Lỗi: {str(e)}"

def extract_text_from_file(uploaded_file) -> str:
    if uploaded_file.name.endswith('.txt'):
        try:
            return uploaded_file.getvalue().decode('utf-8')[:3000]
        except:
            return "[Không thể đọc file text]"
    return "[Chỉ hỗ trợ file txt]"

def resize_image(img_bytes, max_size=(200, 200)):
    try:
        from PIL import Image
        img = Image.open(BytesIO(img_bytes))
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    except:
        return img_bytes

# ================== HÀM XỬ LÝ DATA TRÊN GITHUB ==================
def get_default_data() -> Dict:
    return {
        "users": {
            ADMIN_USERNAME: {
                "password": ADMIN_PASSWORD,
                "info": {
                    "name": "Admin", "bio": "", "link": str(uuid.uuid4()),
                    "avatar": None, "created": str(datetime.now()), "email": None
                },
                "login_attempts": 0,
                "locked_until": None
            }
        },
        "codes": [{"code": "PHAT2026", "expiry": None, "max_uses": None, "used_by": []}],
        "pro_users": [],
        "chat_sessions": [],
        "files": {},
        "session_tokens": {},
        "system_info": {"created": str(datetime.now()), "creator": CONFIG["CREATOR"], "system_name": CONFIG["NAME"]}
    }

def load_data_from_github() -> Dict:
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['DATA_FILE']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            content = base64.b64decode(res.json()['content']).decode('utf-8')
            data = json.loads(content)
            
            # Đảm bảo admin luôn tồn tại
            if ADMIN_USERNAME not in data.get("users", {}):
                data["users"][ADMIN_USERNAME] = get_default_data()["users"][ADMIN_USERNAME]
            
            # Đảm bảo các key cần thiết
            defaults = {
                "codes": [], "pro_users": [], "chat_sessions": [], "files": {},
                "session_tokens": {}, "system_info": {}
            }
            for key, val in defaults.items():
                if key not in data:
                    data[key] = val
            
            return data
        return get_default_data()
    except:
        return get_default_data()

def save_data_to_github(data: Dict) -> bool:
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['DATA_FILE']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')).decode('utf-8')
        put_data = {"message": f"Auto backup {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "content": content, "branch": "main"}
        if sha:
            put_data["sha"] = sha
        put_res = requests.put(url, headers=headers, json=put_data, timeout=10)
        return put_res.status_code in [200, 201]
    except:
        return False

# ================== HÀM QUẢN LÝ FILE CLOUD ==================
def get_used_storage(username: str) -> int:
    total = 0
    for path, info in st.session_state.data.get("files", {}).items():
        if info.get("owner") == username and info.get("type") != "dir":
            total += info.get("size", 0)
    return total

def list_directory(path: str, username: str) -> Dict:
    folders = set()
    files = []
    prefix = path + "/" if path else ""
    
    for full_path, info in st.session_state.data.get("files", {}).items():
        if info.get("owner") != username:
            continue
        if full_path.startswith(prefix):
            rest = full_path[len(prefix):]
            if "/" in rest:
                folder_name = rest.split("/")[0]
                folders.add(folder_name)
            else:
                if info.get("type") == "dir":
                    folders.add(rest)
                else:
                    files.append({
                        "name": rest,
                        "size": info.get("size", 0),
                        "type": info.get("mime_type", "application/octet-stream"),
                        "upload_time": info.get("upload_time", ""),
                        "full_path": full_path
                    })
    
    return {
        "folders": sorted(list(folders)),
        "files": sorted(files, key=lambda x: x["name"])
    }

def create_folder_cloud(path: str, username: str) -> bool:
    if path and not path.endswith("/"):
        path += "/"
    marker = path + ".folder"
    if marker not in st.session_state.data["files"]:
        st.session_state.data["files"][marker] = {
            "owner": username,
            "data": "",
            "size": 0,
            "type": "dir",
            "mime_type": "folder",
            "upload_time": str(datetime.now())
        }
        mark_data_modified()
        return True
    return False

def delete_file_cloud(file_path: str, username: str) -> bool:
    to_delete = []
    for path in st.session_state.data["files"]:
        if path == file_path or path.startswith(file_path + "/"):
            to_delete.append(path)
    
    for path in to_delete:
        del st.session_state.data["files"][path]
    
    if to_delete:
        mark_data_modified()
        return True
    return False

def upload_file_cloud(file_path: str, file_data: bytes, username: str, mime_type: str = None):
    if not mime_type:
        mime_type = "application/octet-stream"
    
    st.session_state.data["files"][file_path] = {
        "owner": username,
        "data": base64.b64encode(file_data).decode('utf-8'),
        "size": len(file_data),
        "type": "file",
        "mime_type": mime_type,
        "upload_time": str(datetime.now())
    }
    mark_data_modified()

def download_files_cloud(file_paths: List[str]) -> bytes:
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fp in file_paths:
            if fp in st.session_state.data["files"]:
                file_info = st.session_state.data["files"][fp]
                if file_info.get("type") != "dir":
                    file_data = base64.b64decode(file_info["data"])
                    file_name = fp.split("/")[-1]
                    zf.writestr(file_name, file_data)
    return zip_buffer.getvalue()

# ================== HÀM BẢO MẬT ==================
def create_session_token(username: str) -> str:
    token = hashlib.sha256(f"{username}{uuid.uuid4()}{datetime.now()}".encode()).hexdigest()
    expiry = datetime.now() + timedelta(days=CONFIG["SESSION_TOKEN_EXPIRY"])
    if "session_tokens" not in st.session_state.data:
        st.session_state.data["session_tokens"] = {}
    st.session_state.data["session_tokens"][token] = {
        "username": username, "expiry": str(expiry)
    }
    mark_data_modified()
    return token

def add_login_history(username: str, status: str):
    # Đơn giản hóa, chỉ lưu thời gian
    if "login_history" not in st.session_state.data:
        st.session_state.data["login_history"] = {}
    if username not in st.session_state.data["login_history"]:
        st.session_state.data["login_history"][username] = []
    st.session_state.data["login_history"][username].append({
        "time": str(datetime.now()), "status": status
    })
    mark_data_modified()

# ================== KHỞI TẠO ==================
def init_session():
    if 'data' not in st.session_state:
        st.session_state.data = load_data_from_github()
    if 'page' not in st.session_state:
        st.session_state.page = "DASHBOARD"
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'current_chat_id' not in st.session_state:
        st.session_state.current_chat_id = None
    if 'guest_mode' not in st.session_state:
        st.session_state.guest_mode = False
    if 'temp_chat' not in st.session_state:
        st.session_state.temp_chat = {"messages": []}
    if 'current_dir' not in st.session_state:
        st.session_state.current_dir = ""
    if 'selected_files' not in st.session_state:
        st.session_state.selected_files = []
    
    # Xử lý query params
    if st.query_params.get("delete_chat"):
        try:
            chat_id = int(st.query_params.get("delete_chat"))
            st.session_state.data["chat_sessions"] = [s for s in st.session_state.data["chat_sessions"] if s.get("id") != chat_id]
            if st.session_state.current_chat_id == chat_id:
                st.session_state.current_chat_id = None
            mark_data_modified()
        except:
            pass
        st.query_params.clear()
        st.rerun()
    
    if st.query_params.get("delete_all_chats"):
        try:
            st.session_state.data["chat_sessions"] = [s for s in st.session_state.data["chat_sessions"] if s.get("owner") != st.session_state.user]
            st.session_state.current_chat_id = None
            mark_data_modified()
        except:
            pass
        st.query_params.clear()
        st.rerun()
    
    check_and_auto_backup()

init_session()

is_pro = (st.session_state.user in st.session_state.data.get("pro_users", [])) if st.session_state.user else False
is_admin = st.session_state.user == ADMIN_USERNAME if st.session_state.user else False

def go_to(page):
    st.session_state.page = page
    st.rerun()

# ================== SIDEBAR ==================
with st.sidebar:
    st.markdown(f"<div style='text-align:center'><h2>🚀 {CONFIG['NAME']}</h2><span class='version-badge'>v{CONFIG['VERSION']}</span><p><small>by {CONFIG['CREATOR']}</small></p></div>", unsafe_allow_html=True)
    
    if st.session_state.user:
        info = st.session_state.data["users"][st.session_state.user]["info"] if not st.session_state.guest_mode else None
        if info and info.get("avatar"):
            st.markdown(f'<img src="data:image/png;base64,{info["avatar"]}" class="avatar-large">', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align:center; font-size:40px;">👤</div>', unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center'><b>{info.get('name', st.session_state.user) if info else st.session_state.user}</b></div>", unsafe_allow_html=True)
        if st.session_state.guest_mode:
            st.markdown('<div style="text-align:center"><span class="guest-badge">🔓 GUEST</span></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="text-align:center"><span class="guest-badge {"pro-badge" if is_pro else ""}">{"💎 PRO" if is_pro else "🆓 FREE"}</span></div>', unsafe_allow_html=True)
    st.divider()
    
    if not st.session_state.user:
        with st.form("login_form"):
            st.subheader("🔐 ĐĂNG NHẬP")
            login_user = st.text_input("Tài khoản")
            login_pass = st.text_input("Mật khẩu", type="password")
            remember = st.checkbox("💾 Ghi nhớ")
            submitted = st.form_submit_button("Đăng nhập")
            
            if submitted:
                if login_user in st.session_state.data["users"]:
                    user_data = st.session_state.data["users"][login_user]
                    if user_data.get("locked_until"):
                        locked_until = datetime.fromisoformat(user_data["locked_until"])
                        if datetime.now() < locked_until:
                            st.error(f"Tài khoản bị khóa đến {locked_until.strftime('%H:%M:%S %d/%m/%Y')}. Vui lòng thử lại sau.")
                    elif user_data.get("password") == login_pass:
                        user_data["login_attempts"] = 0
                        user_data["locked_until"] = None
                        st.session_state.user = login_user
                        st.session_state.guest_mode = False
                        if remember:
                            create_session_token(login_user)
                        add_login_history(login_user, "success")
                        mark_data_modified()
                        st.rerun()
                    else:
                        user_data["login_attempts"] = user_data.get("login_attempts", 0) + 1
                        if user_data["login_attempts"] >= 5:
                            user_data["locked_until"] = str(datetime.now() + timedelta(minutes=15))
                            st.error("Sai quá nhiều lần! Tài khoản bị khóa 15 phút.")
                        else:
                            st.error(f"Sai mật khẩu! Còn {5 - user_data['login_attempts']} lần thử.")
                        add_login_history(login_user, "failed")
                        mark_data_modified()
                else:
                    st.error("Tài khoản không tồn tại!")
        
        if st.button("👤 DÙNG THỬ"):
            st.session_state.user = "guest"
            st.session_state.guest_mode = True
            st.rerun()
        
        with st.expander("📝 Đăng ký"):
            reg_user = st.text_input("Tên đăng nhập")
            reg_pass = st.text_input("Mật khẩu", type="password")
            reg_confirm = st.text_input("Xác nhận")
            reg_name = st.text_input("Tên hiển thị")
            if st.button("Đăng ký"):
                if reg_user and reg_pass and reg_pass == reg_confirm and len(reg_user) >= 3 and len(reg_pass) >= 6:
                    if reg_user not in st.session_state.data["users"]:
                        st.session_state.data["users"][reg_user] = {
                            "password": reg_pass,
                            "info": {"name": reg_name or reg_user, "bio": "", "link": str(uuid.uuid4()), "avatar": None, "created": str(datetime.now()), "email": None},
                            "login_attempts": 0, "locked_until": None
                        }
                        mark_data_modified()
                        st.success("Đăng ký thành công!")
                    else:
                        st.error("Tên đã tồn tại!")
    else:
        st.markdown("### 🚀 TIỆN ÍCH")
        if st.button("🏠 TRANG CHÍNH"): go_to("DASHBOARD")
        if st.button("🧠 CHAT AI"): go_to("CHAT")
        if st.button("☁️ LƯU TRỮ"): go_to("CLOUD")
        if st.button("📜 LỊCH SỬ CHAT"): go_to("HISTORY")
        if st.button("⚙️ CÀI ĐẶT"): go_to("SETTINGS")
        if st.button("ℹ️ THÔNG TIN"): go_to("ABOUT")
        if is_admin and st.button("🛠️ ADMIN"): go_to("ADMIN")
        if st.button("🚪 ĐĂNG XUẤT"):
            st.session_state.user = None
            st.rerun()
        
        st.divider()
        
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        st.markdown('<h4>💬 Nhập tin nhắn</h4>', unsafe_allow_html=True)
        with st.form(key="chat_form", clear_on_submit=True):
            col_up, col_inp = st.columns([1, 3])
            with col_up:
                uploaded_file = st.file_uploader("📎", type=["txt"], label_visibility="collapsed", key="sidebar_upload")
            with col_inp:
                p = st.text_input("", placeholder="Nhập câu hỏi...", key="sidebar_input")
            submitted = st.form_submit_button("📤 Gửi", use_container_width=True)
            if submitted and p:
                st.session_state.pending_message = p
                if uploaded_file:
                    st.session_state.pending_file = uploaded_file
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ================== DASHBOARD ==================
if st.session_state.page == "DASHBOARD":
    st.markdown(f"<div class='custom-card' style='text-align:center'><h1>🚀 {CONFIG['NAME']}</h1><p>Chào mừng, <b>{st.session_state.user if st.session_state.user else 'khách'}</b>!</p></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    if col1.button("🧠 CHAT AI", use_container_width=True): go_to("CHAT")
    if col2.button("☁️ LƯU TRỮ", use_container_width=True): go_to("CLOUD")

# ================== CHAT AI ==================
elif st.session_state.page == "CHAT":
    st.markdown('<div class="chat-header">🧠 NEXUS OS GATEWAY - Trợ lý AI<button onclick="deleteAllChats()">🗑️ Xóa tất cả</button></div>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### 📝 LỊCH SỬ CHAT")
        if st.button("➕ Tạo mới", use_container_width=True):
            new_id = len(st.session_state.data["chat_sessions"])
            st.session_state.data["chat_sessions"].append({
                "id": new_id, "name": f"Chat {datetime.now().strftime('%H:%M %d/%m')}",
                "owner": st.session_state.user, "created": str(datetime.now()), "messages": []
            })
            st.session_state.current_chat_id = new_id
            mark_data_modified()
            st.rerun()
        if st.button("🗑️ Xóa tất cả lịch sử", use_container_width=True):
            st.session_state.data["chat_sessions"] = [s for s in st.session_state.data["chat_sessions"] if s.get("owner") != st.session_state.user]
            st.session_state.current_chat_id = None
            mark_data_modified()
            st.rerun()
        st.write("---")
        sessions = [s for s in st.session_state.data["chat_sessions"] if s.get("owner") == st.session_state.user]
        for s in sessions[-20:]:
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(f"💬 {s.get('name')}", key=f"chat_{s.get('id')}", use_container_width=True):
                    st.session_state.current_chat_id = s.get("id")
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{s.get('id')}"):
                    st.markdown(f'<button onclick="deleteChat({s.get("id")})" style="background:#dc2626; color:white; border:none; border-radius:20px; padding:5px 10px; cursor:pointer;">🗑️</button>', unsafe_allow_html=True)
    
    if st.session_state.guest_mode:
        chat = st.session_state.temp_chat
    else:
        if st.session_state.current_chat_id is not None:
            sessions = [s for s in st.session_state.data["chat_sessions"] if s.get("id") == st.session_state.current_chat_id]
            chat = sessions[0] if sessions else {"messages": []}
        else:
            chat = None
    
    st.markdown('<div id="chat-messages" class="chat-messages">', unsafe_allow_html=True)
    
    if chat is None:
        st.markdown('<div style="text-align:center; padding: 40px; color: #9ca3af;">👋 Chưa có cuộc trò chuyện nào. Hãy nhập tin nhắn bên cạnh để bắt đầu!</div>', unsafe_allow_html=True)
    else:
        messages = chat.get("messages", [])
        for m in messages:
            if m.get("role") == "user":
                st.markdown(f'<div class="message user"><div class="message-bubble">{m.get("content", "")}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="message assistant"><div class="message-bubble">{m.get("content", "")}</div></div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.session_state.get("pending_message"):
        p = st.session_state.pending_message
        uploaded_file = st.session_state.get("pending_file")
        if uploaded_file:
            extracted = extract_text_from_file(uploaded_file)
            p = f"[File: {uploaded_file.name}]\n{extracted}" if extracted and not extracted.startswith("[") else f"Tôi vừa tải file {uploaded_file.name}"
        
        if not st.session_state.guest_mode and chat is None:
            new_id = len(st.session_state.data["chat_sessions"])
            st.session_state.data["chat_sessions"].append({
                "id": new_id, "name": f"Chat {datetime.now().strftime('%H:%M %d/%m')}",
                "owner": st.session_state.user, "created": str(datetime.now()), "messages": []
            })
            st.session_state.current_chat_id = new_id
            mark_data_modified()
            chat = st.session_state.data["chat_sessions"][-1]
        
        if st.session_state.guest_mode:
            chat["messages"].append({"role": "user", "content": p})
        else:
            chat["messages"].append({"role": "user", "content": p})
        
        with st.spinner("🧠 Đang suy nghĩ..."):
            msgs = [{"role": m.get("role"), "content": m.get("content")} for m in chat["messages"][-10:]]
            ans = call_ai(msgs)
            chat["messages"].append({"role": "assistant", "content": ans})
            if not st.session_state.guest_mode:
                mark_data_modified()
        
        st.session_state.pending_message = None
        st.session_state.pending_file = None
        st.rerun()

# ================== CLOUD STORAGE ==================
elif st.session_state.page == "CLOUD":
    st.markdown("<h2>☁️ NEXUS CLOUD - LƯU TRỮ ĐÁM MÂY</h2>", unsafe_allow_html=True)
    
    if st.session_state.guest_mode:
        st.warning("🔒 Guest không thể sử dụng lưu trữ đám mây. Vui lòng đăng ký tài khoản để dùng tính năng này!")
    else:
        # Hiển thị dung lượng
        used = get_used_storage(st.session_state.user)
        limit = CONFIG["PRO_STORAGE_LIMIT"] if is_pro else CONFIG["FREE_STORAGE_LIMIT"]
        used_gb = used / (1024**3)
        limit_gb = "∞" if is_pro else f"{limit/(1024**3):.1f}"
        st.progress(min(used/limit, 1) if not is_pro else 0, text=f"📊 Đã dùng: {used_gb:.2f} GB / {limit_gb} GB")
        
        # Điều hướng thư mục
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"📁 Thư mục hiện tại: /{st.session_state.current_dir}")
        with col2:
            if st.session_state.current_dir and st.button("⬆️ Lên trên"):
                st.session_state.current_dir = "/".join(st.session_state.current_dir.split("/")[:-1])
                st.rerun()
        with col3:
            with st.popover("➕ Tạo thư mục mới"):
                new_folder = st.text_input("Tên thư mục:")
                if st.button("Tạo") and new_folder:
                    path = f"{st.session_state.current_dir}/{new_folder}" if st.session_state.current_dir else new_folder
                    if create_folder_cloud(path, st.session_state.user):
                        st.success(f"Đã tạo thư mục '{new_folder}'!")
                        st.rerun()
                    else:
                        st.error("Thư mục đã tồn tại!")
        
        # Liệt kê nội dung
        items = list_directory(st.session_state.current_dir, st.session_state.user)
        
        # Hiển thị thư mục
        if items["folders"]:
            st.markdown("### 📁 THƯ MỤC")
            for folder in items["folders"]:
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(f"📁 {folder}", key=f"folder_{folder}"):
                        st.session_state.current_dir = f"{st.session_state.current_dir}/{folder}" if st.session_state.current_dir else folder
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_folder_{folder}"):
                        folder_path = f"{st.session_state.current_dir}/{folder}" if st.session_state.current_dir else folder
                        delete_file_cloud(folder_path, st.session_state.user)
                        st.rerun()
        
        # Hiển thị file
        st.markdown("### 📄 FILE")
        
        selected_for_download = []
        
        for file in items["files"]:
            col1, col2, col3, col4 = st.columns([0.5, 3, 1, 1])
            with col1:
                is_selected = st.checkbox("", key=f"select_{file['name']}")
                if is_selected:
                    selected_for_download.append(file['full_path'])
            with col2:
                file_size_kb = file['size'] / 1024
                st.write(f"📄 {file['name']} ({file_size_kb:.1f} KB)")
            with col3:
                file_data = base64.b64decode(st.session_state.data["files"][file['full_path']]["data"])
                st.download_button(
                    label="📥",
                    data=file_data,
                    file_name=file['name'],
                    mime=file['type'],
                    key=f"download_{file['name']}"
                )
            with col4:
                if st.button("🗑️", key=f"del_{file['name']}"):
                    delete_file_cloud(file['full_path'], st.session_state.user)
                    st.rerun()
        
        # Nút tải xuống nhiều file
        if selected_for_download:
            if st.button(f"📦 Tải xuống {len(selected_for_download)} file (ZIP)"):
                zip_data = download_files_cloud(selected_for_download)
                st.download_button(
                    label="📥 Tải ZIP ngay",
                    data=zip_data,
                    file_name=f"nexus_cloud_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip"
                )
        
        # Upload file
        with st.expander("📤 Tải file lên", expanded=False):
            uploaded_files = st.file_uploader("Chọn file để tải lên", accept_multiple_files=True)
            if uploaded_files:
                total_size = sum(len(f.getvalue()) for f in uploaded_files)
                if not is_pro and used + total_size > limit:
                    st.error(f"❌ Không đủ dung lượng! Còn trống: {(limit - used)/(1024**3):.2f} GB")
                else:
                    if st.button("✅ Xác nhận tải lên"):
                        for f in uploaded_files:
                            file_path = f"{st.session_state.current_dir}/{f.name}" if st.session_state.current_dir else f.name
                            upload_file_cloud(file_path, f.getvalue(), st.session_state.user, f.type)
                        st.success(f"Đã tải lên {len(uploaded_files)} file!")
                        mark_data_modified()
                        st.rerun()
        
        st.caption("💡 Mẹo: Bạn có thể chọn nhiều file để tải xuống cùng lúc dưới dạng ZIP")

# ================== LỊCH SỬ CHAT ==================
elif st.session_state.page == "HISTORY":
    st.markdown("<h2>📜 LỊCH SỬ CHAT</h2>", unsafe_allow_html=True)
    if st.session_state.guest_mode:
        st.info("🔒 Guest không lưu lịch sử chat")
    else:
        sessions = [s for s in st.session_state.data["chat_sessions"] if s.get("owner") == st.session_state.user]
        sessions.reverse()
        if not sessions:
            st.info("Chưa có lịch sử trò chuyện nào.")
        for s in sessions:
            with st.expander(f"💬 {s.get('name')} - {s.get('created', '')[:16]}"):
                st.write(f"📊 Số tin nhắn: {len(s.get('messages', []))}")
                if s.get('messages'):
                    last_msg = s['messages'][-1].get('content', '')[:100]
                    st.write(f"💭 Tin nhắn cuối: {last_msg}...")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💬 Tiếp tục", key=f"cont_{s.get('id')}"):
                        st.session_state.current_chat_id = s.get("id")
                        go_to("CHAT")
                with col2:
                    if st.button("🗑️ Xóa", key=f"del_{s.get('id')}"):
                        st.markdown(f'<button onclick="deleteChat({s.get("id")})" style="background:#dc2626; color:white; border:none; border-radius:20px; padding:5px 10px; cursor:pointer;">🗑️ Xóa</button>', unsafe_allow_html=True)

# ================== CÀI ĐẶT ==================
elif st.session_state.page == "SETTINGS":
    st.markdown("<h2>⚙️ CÀI ĐẶT</h2>", unsafe_allow_html=True)
    if st.session_state.guest_mode:
        st.info("🔒 Guest không thể đổi cài đặt")
    else:
        user_info = st.session_state.data["users"][st.session_state.user]["info"]
        
        tab1, tab2 = st.tabs(["👤 Cá nhân", "🎁 Nâng cấp Pro"])
        
        with tab1:
            col1, col2 = st.columns([1, 2])
            with col1:
                if user_info.get("avatar"):
                    st.markdown(f'<img src="data:image/png;base64,{user_info["avatar"]}" style="width:100px;height:100px;border-radius:50%;object-fit:cover;">', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="font-size:80px;text-align:center">👤</div>', unsafe_allow_html=True)
                
                avatar_file = st.file_uploader("🖼️ Ảnh đại diện", type=["png", "jpg", "jpeg"])
                if avatar_file and st.button("💾 Cập nhật ảnh"):
                    resized = resize_image(avatar_file.getvalue())
                    user_info["avatar"] = base64.b64encode(resized).decode('utf-8')
                    mark_data_modified()
                    st.success("Đã cập nhật ảnh đại diện!")
                    st.rerun()
            
            with col2:
                new_name = st.text_input("📝 Tên hiển thị", value=user_info.get("name", st.session_state.user))
                if st.button("💾 Đổi tên"):
                    user_info["name"] = new_name
                    mark_data_modified()
                    st.success("Đã đổi tên hiển thị!")
                
                new_bio = st.text_area("📝 Giới thiệu bản thân", value=user_info.get("bio", ""), height=100)
                if st.button("💾 Cập nhật giới thiệu"):
                    user_info["bio"] = new_bio
                    mark_data_modified()
                    st.success("Đã cập nhật giới thiệu!")
        
        with tab2:
            st.subheader("🎁 Kích hoạt tài khoản PRO")
            st.write("Nhập mã kích hoạt để nâng cấp lên PRO với nhiều tính năng hơn:")
            code = st.text_input("🔑 Mã kích hoạt", type="password").upper()
            if st.button("🚀 Kích hoạt PRO"):
                for c in st.session_state.data["codes"]:
                    if isinstance(c, dict) and c.get("code") == code:
                        if st.session_state.user not in st.session_state.data["pro_users"]:
                            st.session_state.data["pro_users"].append(st.session_state.user)
                            mark_data_modified()
                            st.balloons()
                            st.success("🎉 Chúc mừng! Bạn đã là thành viên PRO!")
                            st.rerun()
                        else:
                            st.info("Bạn đã là PRO rồi!")
                        break
                    elif isinstance(c, str) and c == code:
                        if st.session_state.user not in st.session_state.data["pro_users"]:
                            st.session_state.data["pro_users"].append(st.session_state.user)
                            st.session_state.data["codes"] = [x for x in st.session_state.data["codes"] if x != code]
                            mark_data_modified()
                            st.balloons()
                            st.success("🎉 Chúc mừng! Bạn đã là thành viên PRO!")
                            st.rerun()
                        break
                else:
                    st.error("❌ Mã không hợp lệ!")
            
            if is_pro:
                st.success("✅ Bạn đang sử dụng gói PRO với các đặc quyền:")
                st.markdown("""
                - 💾 **Không giới hạn dung lượng lưu trữ**
                - 🧠 **Lịch sử chat không giới hạn**
                - 🚀 **Tốc độ xử lý ưu tiên**
                """)

# ================== ADMIN ==================
elif st.session_state.page == "ADMIN":
    if not is_admin:
        st.error("❌ Bạn không có quyền truy cập trang Admin!")
    else:
        st.markdown("<h2>🛠️ ADMIN PANEL</h2>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🎫 Mã PRO", "👥 Quản lý người dùng"])
        
        with tab1:
            st.subheader("➕ Tạo mã kích hoạt PRO")
            new_code = st.text_input("Mã mới").upper()
            col1, col2 = st.columns(2)
            with col1:
                has_expiry = st.checkbox("⏰ Có hạn sử dụng")
                expiry = st.date_input("Ngày hết hạn") if has_expiry else None
            with col2:
                has_limit = st.checkbox("🔢 Giới hạn số lần")
                max_uses = st.number_input("Số lần sử dụng", min_value=1, value=1) if has_limit else None
            
            if st.button("🎁 TẠO MÃ", use_container_width=True) and new_code:
                st.session_state.data["codes"].append({
                    "code": new_code,
                    "expiry": str(expiry) if expiry else None,
                    "max_uses": max_uses,
                    "used_by": []
                })
                mark_data_modified()
                st.success(f"✅ Đã tạo mã: `{new_code}`")
                st.rerun()
            
            st.subheader("📋 Danh sách mã PRO")
            for c in st.session_state.data["codes"]:
                if isinstance(c, dict):
                    expiry_txt = c.get("expiry") or "Vĩnh viễn"
                    used = len(c.get("used_by", []))
                    max_txt = str(c.get("max_uses")) if c.get("max_uses") else "∞"
                    st.code(f"📌 {c.get('code')} | Hết hạn: {expiry_txt} | Đã dùng: {used}/{max_txt}")
                else:
                    st.code(f"📌 {c}")
        
        with tab2:
            st.subheader("👥 QUẢN LÝ NGƯỜI DÙNG")
            for username, user_data in st.session_state.data["users"].items():
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                    col1.write(f"**{username}**")
                    col2.write(f"{user_data['info'].get('name', '')}")
                    is_pro_user = username in st.session_state.data.get("pro_users", [])
                    col3.write("💎 PRO" if is_pro_user else "🆓 FREE")
                    
                    if username != ADMIN_USERNAME:
                        if col4.button(f"🗑️ Xóa", key=f"del_user_{username}"):
                            del st.session_state.data["users"][username]
                            if username in st.session_state.data.get("pro_users", []):
                                st.session_state.data["pro_users"].remove(username)
                            mark_data_modified()
                            st.rerun()
                    else:
                        col4.write("👑 Admin")
                    st.divider()

# ================== THÔNG TIN ==================
elif st.session_state.page == "ABOUT":
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0047AB,#0066CC);color:white;border-radius:16px;padding:30px;text-align:center">
        <h1 style="font-size:48px;margin:0">🚀 {CONFIG['NAME']}</h1>
        <p style="font-size:18px;opacity:0.9">Phiên bản {CONFIG['VERSION']}</p>
        <p style="margin-top:10px">Sáng tạo bởi <b>{CONFIG['CREATOR']}</b></p>
        <hr style="margin:20px 0;border-color:rgba(255,255,255,0.2)">
        <p style="font-style:italic">"Kết nối tri thức, mở ra tương lai"</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### ✨ TÍNH NĂNG NỔI BẬT")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **🤖 TRÍ TUỆ NHÂN TẠO**
        - ✅ Chat AI thông minh
        - ✅ Phân tích file văn bản
        - ✅ Xử lý ngôn ngữ tự nhiên
        
        **☁️ LƯU TRỮ ĐÁM MÂY**
        - ✅ Quản lý file và thư mục
        - ✅ Tải lên/xuống nhiều file
        - ✅ Tạo ZIP hàng loạt
        - ✅ Free 30GB - Pro không giới hạn
        """)
    
    with col2:
        st.markdown("""
        **🔒 BẢO MẬT CAO CẤP**
        - ✅ Ghi nhớ đăng nhập
        - ✅ Giới hạn đăng nhập sai
        - ✅ Sao lưu dữ liệu tự động
        
        **💎 TÍNH NĂNG PRO**
        - ✅ Không giới hạn dung lượng
        - ✅ Lịch sử chat không giới hạn
        - ✅ Tốc độ xử lý ưu tiên
        """)
    
    st.markdown("---")
    st.markdown(f"<p style='text-align:center;color:#6b7280'>© 2025-2026 {CONFIG['CREATOR']} | {CONFIG['NAME']} - Hệ điều hành AI thế hệ mới</p>", unsafe_allow_html=True)

# Kiểm tra backup
check_and_auto_backup()
