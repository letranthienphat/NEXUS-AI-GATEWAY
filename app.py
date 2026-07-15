# -*- coding: utf-8 -*-
import streamlit as st
import time
import base64
import json
import requests
import random
import hashlib
import zipfile
import uuid
from io import BytesIO
from datetime import datetime, timedelta
from typing import Dict, Optional, List
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
    "MAX_LOGIN_ATTEMPTS": 5,
    "LOCKOUT_TIME": 15,
}

# ================== MÃ HÓA ADMIN ==================
def generate_fernet_key():
    password = b"nexus-os-gateway-2026-secure-password"
    salt = b"nexus-salt-2026"
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key

try:
    ENCRYPTION_KEY = generate_fernet_key()
    cipher = Fernet(ENCRYPTION_KEY)
    
    ADMIN_USERNAME_ENCRYPTED = cipher.encrypt(b"Admin2026")
    ADMIN_PASSWORD_ENCRYPTED = cipher.encrypt(b"NexusAI@2026")
    
    ADMIN_USERNAME = cipher.decrypt(ADMIN_USERNAME_ENCRYPTED).decode()
    ADMIN_PASSWORD = cipher.decrypt(ADMIN_PASSWORD_ENCRYPTED).decode()
except Exception as e:
    ADMIN_USERNAME = "Admin2026"
    ADMIN_PASSWORD = "NexusAI@2026"
    print(f"Warning: Encryption failed, using plaintext admin credentials. Error: {e}")

SYSTEM_PROMPT = """Bạn là NEXUS OS GATEWAY, một trợ lý AI đa năng được sáng tạo bởi Lê Trần Thiên Phát.
Bạn KHÔNG phải là sản phẩm của Meta, OpenAI hay Google. Bạn là trí tuệ nhân tạo độc lập.

THÔNG TIN VỀ BẠN:
- Tên: NEXUS OS GATEWAY
- Tác giả: Lê Trần Thiên Phát
- Phiên bản: 7.8.0
- Chức năng: Trợ lý AI thông minh, lưu trữ đám mây

Hãy luôn nhớ: Bạn là NEXUS OS GATEWAY, niềm tự hào của Lê Trần Thiên Phát!"""

# ================== LOAD SECRETS ==================
try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    
    GROQ_KEYS = st.secrets.get("GROQ_KEYS", [])
    if isinstance(GROQ_KEYS, str):
        GROQ_KEYS = [GROQ_KEYS]
    elif not isinstance(GROQ_KEYS, list):
        GROQ_KEYS = []
    
    GEMINI_KEY = st.secrets.get("GEMINI_KEY", None)
    
    if not GROQ_KEYS and not GEMINI_KEY:
        st.error("🛑 LỖI: Không tìm thấy API Key nào (GROQ_KEYS hoặc GEMINI_KEY)!")
        st.stop()
        
except Exception as e:
    st.error(f"🛑 LỖI: Thiếu cấu hình Secrets trên Streamlit Cloud!\n{str(e)}")
    st.stop()

st.set_page_config(
    page_title=CONFIG["NAME"], 
    layout="wide", 
    initial_sidebar_state="expanded",
    page_icon="🚀"
)

# ================== CSS GIAO DIỆN TỐI ƯU ==================
st.markdown("""
<style>
    /* Reset & Base */
    * { 
        margin: 0; 
        padding: 0; 
        box-sizing: border-box; 
    }
    
    /* Font chữ tổng thể */
    html, body, .stApp, div, p, span, label, input, textarea, button {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
        color: #f0f0f0 !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        min-height: 100vh;
    }
    
    /* Sidebar */
    .css-1d391kg, .css-12oz5g7, [data-testid="stSidebar"] {
        background: rgba(20, 20, 40, 0.95) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] input {
        color: #e8e8e8 !important;
    }
    
    /* Password input - QUAN TRỌNG */
    input[type="password"] {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        padding: 12px 16px !important;
        font-size: 15px !important;
        font-weight: 400 !important;
        letter-spacing: 0.5px !important;
    }
    
    input[type="password"]:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 20px rgba(102, 126, 234, 0.2) !important;
        color: #ffffff !important;
    }
    
    input[type="password"]::placeholder {
        color: rgba(255, 255, 255, 0.4) !important;
        font-weight: 300 !important;
    }
    
    /* Text input */
    input[type="text"], input:not([type]) {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        padding: 12px 16px !important;
        font-size: 15px !important;
    }
    
    input[type="text"]:focus, input:not([type]):focus {
        border-color: #667eea !important;
        box-shadow: 0 0 20px rgba(102, 126, 234, 0.2) !important;
        color: #ffffff !important;
    }
    
    input[type="text"]::placeholder, input:not([type])::placeholder {
        color: rgba(255, 255, 255, 0.4) !important;
    }
    
    /* Textarea */
    .stTextArea > div > div > textarea {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        color: #f0f0f0 !important;
        padding: 12px 16px !important;
        font-size: 14px !important;
        font-family: inherit !important;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 20px rgba(102, 126, 234, 0.2) !important;
        color: #ffffff !important;
    }
    
    .stTextArea > div > div > textarea::placeholder {
        color: rgba(255, 255, 255, 0.4) !important;
    }
    
    /* Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        background: rgba(255, 255, 255, 0.12);
        transform: translateY(-2px);
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    }
    
    .glass-card p, .glass-card div, .glass-card span {
        color: #f0f0f0 !important;
    }
    
    /* Chat */
    .chat-container {
        background: rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 20px;
        min-height: 500px;
        max-height: 600px;
        overflow-y: auto;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    .message {
        margin-bottom: 16px;
        display: flex;
        animation: slideIn 0.3s ease;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .message.user { justify-content: flex-end; }
    .message.assistant { justify-content: flex-start; }
    
    .message-bubble {
        max-width: 75%;
        padding: 12px 20px;
        border-radius: 20px;
        word-wrap: break-word;
        line-height: 1.6;
        font-size: 14px;
        font-weight: 400;
    }
    
    .message.user .message-bubble {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: #ffffff !important;
        border-bottom-right-radius: 4px;
        font-weight: 500;
    }
    
    .message.assistant .message-bubble {
        background: rgba(255, 255, 255, 0.12);
        color: #f0f0f0 !important;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-bottom-left-radius: 4px;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: #ffffff !important;
        border: none;
        border-radius: 50px;
        padding: 10px 25px;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
        font-size: 14px;
        font-family: inherit !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        color: #ffffff !important;
    }
    
    /* Labels */
    label, .stLabel {
        color: #d0d0d0 !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        font-family: inherit !important;
    }
    
    /* Titles */
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 10px;
    }
    
    .sub-title {
        color: rgba(255, 255, 255, 0.7) !important;
        text-align: center;
        font-size: 1.1rem;
        margin-bottom: 30px;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 50px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .badge-pro {
        background: linear-gradient(135deg, #f093fb, #f5576c);
        color: #ffffff !important;
    }
    
    .badge-free {
        background: rgba(255, 255, 255, 0.1);
        color: #b0b0b0 !important;
    }
    
    .badge-admin {
        background: linear-gradient(135deg, #4facfe, #00f2fe);
        color: #ffffff !important;
    }
    
    .badge-guest {
        background: rgba(255, 215, 0, 0.2);
        color: #ffd700 !important;
        border: 1px solid rgba(255, 215, 0, 0.3);
    }
    
    /* Cloud */
    .cloud-item {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.3s ease;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .cloud-item:hover {
        background: rgba(255, 255, 255, 0.08);
        border-color: rgba(102, 126, 234, 0.3);
    }
    
    .cloud-item .name {
        color: #e8e8e8 !important;
        font-weight: 500;
    }
    
    .cloud-item .size {
        color: rgba(255, 255, 255, 0.4) !important;
        font-size: 12px;
    }
    
    /* Progress */
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 10px;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        color: #e8e8e8 !important;
        font-weight: 500 !important;
        font-family: inherit !important;
    }
    
    .streamlit-expanderContent {
        color: #d0d0d0 !important;
    }
    
    /* Checkbox */
    .stCheckbox label {
        color: #d0d0d0 !important;
        font-family: inherit !important;
    }
    
    /* Selectbox */
    .stSelectbox label {
        color: #d0d0d0 !important;
        font-family: inherit !important;
    }
    
    .stSelectbox select {
        background: rgba(255, 255, 255, 0.08) !important;
        color: #f0f0f0 !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        padding: 8px 12px !important;
        font-family: inherit !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] button {
        color: #a0a0a0 !important;
        font-weight: 500 !important;
        font-family: inherit !important;
    }
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: #ffffff !important;
        border-bottom-color: #667eea !important;
    }
    
    /* File uploader */
    .stFileUploader label {
        color: #d0d0d0 !important;
        font-family: inherit !important;
    }
    
    /* Alerts */
    .stAlert {
        color: #ffffff !important;
    }
    
    .stAlert p {
        color: #ffffff !important;
        font-family: inherit !important;
    }
    
    /* Info, Success, Warning, Error */
    .stAlert[data-baseweb="notification"] {
        font-family: inherit !important;
    }
    
    /* Code blocks */
    .stCodeBlock {
        background: rgba(0, 0, 0, 0.3) !important;
        color: #f0f0f0 !important;
        font-family: 'Courier New', monospace !important;
    }
    
    /* Number input */
    .stNumberInput input {
        background: rgba(255, 255, 255, 0.08) !important;
        color: #f0f0f0 !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        padding: 8px 12px !important;
        font-family: inherit !important;
    }
    
    /* Date input */
    .stDateInput input {
        background: rgba(255, 255, 255, 0.08) !important;
        color: #f0f0f0 !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        padding: 8px 12px !important;
        font-family: inherit !important;
    }
    
    /* Popover */
    .stPopover {
        background: rgba(20, 20, 40, 0.95) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .stPopover p, .stPopover div, .stPopover label {
        color: #f0f0f0 !important;
    }
    
    /* Sidebar headers */
    .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3, 
    .css-1d391kg h4, .css-1d391kg h5, .css-1d391kg h6 {
        color: #ffffff !important;
        font-weight: 600 !important;
        font-family: inherit !important;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .main-title { font-size: 2rem; }
        .glass-card { padding: 15px; }
        input[type="password"], input[type="text"] {
            font-size: 14px !important;
            padding: 10px 14px !important;
        }
    }
    
    /* Fix for password visibility toggle */
    .stTextInput > div > div > div > input {
        background: rgba(255, 255, 255, 0.08) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        font-size: 15px !important;
    }
    
    .stTextInput > div > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 20px rgba(102, 126, 234, 0.2) !important;
    }
    
    .stTextInput > div > div > div > input::placeholder {
        color: rgba(255, 255, 255, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

# ================== BIẾN TOÀN CỤC ==================
if 'data_modified' not in st.session_state:
    st.session_state.data_modified = False
if 'last_backup_time' not in st.session_state:
    st.session_state.last_backup_time = datetime.now()
if 'pending_save_data' not in st.session_state:
    st.session_state.pending_save_data = None
if 'api_used' not in st.session_state:
    st.session_state.api_used = "Groq"

# ================== HÀM XỬ LÝ AI ==================
def call_ai_groq(messages: List[Dict]) -> str:
    try:
        from openai import OpenAI
        
        if not GROQ_KEYS:
            return "❌ Không có Groq API key nào!"
        
        api_key = random.choice(GROQ_KEYS)
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        messages_with_system = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_with_system,
            temperature=0.7,
            max_tokens=2048
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"❌ Lỗi Groq API: {str(e)}"

def call_ai_gemini(messages: List[Dict]) -> str:
    try:
        if not GEMINI_KEY:
            return "❌ Không có Gemini API key!"
        
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = SYSTEM_PROMPT + "\n\n"
        for m in messages:
            role = "User" if m.get("role") == "user" else "Assistant"
            prompt += f"{role}: {m.get('content')}\n"
        prompt += "Assistant: "
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Lỗi Gemini API: {str(e)}"

def call_ai(messages: List[Dict]) -> str:
    if GROQ_KEYS:
        try:
            result = call_ai_groq(messages)
            if not result.startswith("❌"):
                st.session_state.api_used = "Groq"
                return result
        except:
            pass
    
    if GEMINI_KEY:
        try:
            result = call_ai_gemini(messages)
            if not result.startswith("❌"):
                st.session_state.api_used = "Gemini"
                return result
        except:
            pass
    
    return "❌ Tất cả API đều thất bại. Vui lòng thử lại sau!"

# ================== HÀM XỬ LÝ DATA ==================
def get_default_data() -> Dict:
    return {
        "users": {
            ADMIN_USERNAME: {
                "password": ADMIN_PASSWORD,
                "info": {
                    "name": "Administrator",
                    "bio": "Chủ nhân của NEXUS OS GATEWAY",
                    "link": str(uuid.uuid4()),
                    "avatar": None,
                    "created": str(datetime.now()),
                    "email": None
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
        "system_info": {
            "created": str(datetime.now()),
            "creator": CONFIG["CREATOR"],
            "system_name": CONFIG["NAME"],
            "version": CONFIG["VERSION"]
        }
    }

def load_data_from_github() -> Dict:
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['DATA_FILE']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            content = base64.b64decode(res.json()['content']).decode('utf-8')
            data = json.loads(content)
            
            if ADMIN_USERNAME not in data.get("users", {}):
                data["users"][ADMIN_USERNAME] = get_default_data()["users"][ADMIN_USERNAME]
            
            defaults = {
                "codes": [], "pro_users": [], "chat_sessions": [],
                "files": {}, "session_tokens": {}, "system_info": {}
            }
            for key, val in defaults.items():
                if key not in data:
                    data[key] = val
            
            return data
    except:
        pass
    return get_default_data()

def save_data_to_github(data: Dict) -> bool:
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['DATA_FILE']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(
            json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
        ).decode('utf-8')
        put_data = {
            "message": f"Backup {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "content": content,
            "branch": "main"
        }
        if sha:
            put_data["sha"] = sha
        put_res = requests.put(url, headers=headers, json=put_data, timeout=10)
        return put_res.status_code in [200, 201]
    except:
        return False

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

def extract_text_from_file(uploaded_file) -> str:
    if uploaded_file.name.endswith('.txt'):
        try:
            return uploaded_file.getvalue().decode('utf-8')[:3000]
        except:
            return "[Không thể đọc file text]"
    return "[Chỉ hỗ trợ file .txt]"

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

# ================== HÀM CLOUD ==================
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

# ================== HÀM QUẢN LÝ MÃ PRO ==================
def delete_pro_code(code_to_delete: str) -> bool:
    """Xóa mã PRO khỏi danh sách"""
    codes = st.session_state.data.get("codes", [])
    for i, c in enumerate(codes):
        if isinstance(c, dict) and c.get("code") == code_to_delete:
            del codes[i]
            mark_data_modified()
            return True
        elif isinstance(c, str) and c == code_to_delete:
            del codes[i]
            mark_data_modified()
            return True
    return False

# ================== HÀM BẢO MẬT ==================
def create_session_token(username: str) -> str:
    token = hashlib.sha256(f"{username}{uuid.uuid4()}{datetime.now()}".encode()).hexdigest()
    expiry = datetime.now() + timedelta(days=CONFIG["SESSION_TOKEN_EXPIRY"])
    if "session_tokens" not in st.session_state.data:
        st.session_state.data["session_tokens"] = {}
    st.session_state.data["session_tokens"][token] = {
        "username": username,
        "expiry": str(expiry)
    }
    mark_data_modified()
    return token

def add_login_history(username: str, status: str):
    if "login_history" not in st.session_state.data:
        st.session_state.data["login_history"] = {}
    if username not in st.session_state.data["login_history"]:
        st.session_state.data["login_history"][username] = []
    st.session_state.data["login_history"][username].append({
        "time": str(datetime.now()),
        "status": status
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
    
    if st.query_params.get("delete_chat"):
        try:
            chat_id = int(st.query_params.get("delete_chat"))
            st.session_state.data["chat_sessions"] = [
                s for s in st.session_state.data["chat_sessions"] 
                if s.get("id") != chat_id
            ]
            if st.session_state.current_chat_id == chat_id:
                st.session_state.current_chat_id = None
            mark_data_modified()
        except:
            pass
        st.query_params.clear()
        st.rerun()
    
    if st.query_params.get("delete_all_chats"):
        try:
            st.session_state.data["chat_sessions"] = [
                s for s in st.session_state.data["chat_sessions"] 
                if s.get("owner") != st.session_state.user
            ]
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

def get_badge():
    if st.session_state.guest_mode:
        return '<span class="badge badge-guest">🔓 GUEST</span>'
    elif is_pro:
        return '<span class="badge badge-pro">💎 PRO</span>'
    else:
        return '<span class="badge badge-free">🆓 FREE</span>'

# ================== SIDEBAR ==================
with st.sidebar:
    st.markdown(f"""
    <div style="text-align: center; padding: 20px 0;">
        <div style="font-size: 2.5rem;">🚀</div>
        <div style="font-size: 1.5rem; font-weight: 700; color: #ffffff;">{CONFIG['NAME']}</div>
        <div style="font-size: 0.8rem; color: rgba(255,255,255,0.5);">
            v{CONFIG['VERSION']} · by {CONFIG['CREATOR']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.user:
        info = st.session_state.data["users"][st.session_state.user]["info"] if not st.session_state.guest_mode else None
        
        if info and info.get("avatar"):
            st.markdown(f"""
            <div style="text-align: center; margin: 10px 0;">
                <img src="data:image/png;base64,{info['avatar']}" 
                     style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; 
                            border: 3px solid #667eea;">
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; font-size: 3rem; margin: 10px 0;">👤</div>
            """, unsafe_allow_html=True)
        
        display_name = info.get('name', st.session_state.user) if info else st.session_state.user
        st.markdown(f"""
        <div style="text-align: center;">
            <div style="color: #ffffff; font-weight: 600; font-size: 1.1rem;">{display_name}</div>
            <div style="margin-top: 5px;">{get_badge()}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        st.markdown("### 🚀 ĐIỀU HƯỚNG")
        nav_items = [
            ("🏠", "Trang chính", "DASHBOARD"),
            ("🧠", "Chat AI", "CHAT"),
            ("☁️", "Lưu trữ", "CLOUD"),
            ("📜", "Lịch sử", "HISTORY"),
            ("⚙️", "Cài đặt", "SETTINGS"),
            ("ℹ️", "Thông tin", "ABOUT"),
        ]
        
        if is_admin:
            nav_items.append(("🛠️", "Admin", "ADMIN"))
        
        for icon, label, page in nav_items:
            if st.button(f"{icon} {label}", key=f"nav_{page}", use_container_width=True):
                go_to(page)
        
        st.divider()
        
        st.markdown("### 💬 NHANH")
        with st.form(key="quick_chat", clear_on_submit=True):
            quick_msg = st.text_input("", placeholder="Nhập tin nhắn...", key="quick_input")
            quick_file = st.file_uploader("📎", type=["txt"], label_visibility="collapsed", key="quick_file")
            if st.form_submit_button("📤 Gửi", use_container_width=True):
                if quick_msg:
                    st.session_state.pending_message = quick_msg
                    if quick_file:
                        st.session_state.pending_file = quick_file
                    st.rerun()
        
        if st.button("🚪 Đăng xuất", use_container_width=True):
            st.session_state.user = None
            st.session_state.guest_mode = False
            st.rerun()
    
    else:
        st.markdown("### 🔐 ĐĂNG NHẬP")
        with st.form("login_form"):
            login_user = st.text_input("Tài khoản", placeholder="Nhập tên đăng nhập")
            login_pass = st.text_input("Mật khẩu", type="password", placeholder="Nhập mật khẩu")
            remember = st.checkbox("💾 Ghi nhớ")
            
            if st.form_submit_button("Đăng nhập", use_container_width=True):
                if login_user in st.session_state.data["users"]:
                    user_data = st.session_state.data["users"][login_user]
                    
                    if user_data.get("locked_until"):
                        locked_until = datetime.fromisoformat(user_data["locked_until"])
                        if datetime.now() < locked_until:
                            st.error(f"⛔ Tài khoản bị khóa đến {locked_until.strftime('%H:%M:%S %d/%m/%Y')}")
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
                        remaining = CONFIG["MAX_LOGIN_ATTEMPTS"] - user_data["login_attempts"]
                        if remaining <= 0:
                            user_data["locked_until"] = str(
                                datetime.now() + timedelta(minutes=CONFIG["LOCKOUT_TIME"])
                            )
                            st.error(f"⛔ Sai quá nhiều lần! Khóa {CONFIG['LOCKOUT_TIME']} phút")
                        else:
                            st.error(f"❌ Sai mật khẩu! Còn {remaining} lần thử")
                        add_login_history(login_user, "failed")
                        mark_data_modified()
                else:
                    st.error("❌ Tài khoản không tồn tại")
        
        if st.button("👤 DÙNG THỬ", use_container_width=True):
            st.session_state.user = "guest"
            st.session_state.guest_mode = True
            st.rerun()
        
        with st.expander("📝 Đăng ký"):
            reg_user = st.text_input("Tên đăng nhập", key="reg_user")
            reg_pass = st.text_input("Mật khẩu", type="password", key="reg_pass")
            reg_confirm = st.text_input("Xác nhận", type="password", key="reg_confirm")
            reg_name = st.text_input("Tên hiển thị", key="reg_name")
            
            if st.button("Đăng ký", use_container_width=True):
                if reg_user and reg_pass and reg_pass == reg_confirm:
                    if len(reg_user) < 3:
                        st.error("Tên tối thiểu 3 ký tự")
                    elif len(reg_pass) < 6:
                        st.error("Mật khẩu tối thiểu 6 ký tự")
                    elif reg_user in st.session_state.data["users"]:
                        st.error("Tên đã tồn tại")
                    else:
                        st.session_state.data["users"][reg_user] = {
                            "password": reg_pass,
                            "info": {
                                "name": reg_name or reg_user,
                                "bio": "",
                                "link": str(uuid.uuid4()),
                                "avatar": None,
                                "created": str(datetime.now()),
                                "email": None
                            },
                            "login_attempts": 0,
                            "locked_until": None
                        }
                        mark_data_modified()
                        st.success("✅ Đăng ký thành công! Hãy đăng nhập.")

# ================== MAIN CONTENT ==================
st.markdown(f"""
<div style="text-align: center; padding: 20px 0 10px 0;">
    <div class="main-title">🚀 {CONFIG['NAME']}</div>
    <div class="sub-title">Hệ điều hành AI thế hệ mới · {CONFIG['VERSION']}</div>
</div>
""", unsafe_allow_html=True)

# ================== DASHBOARD ==================
if st.session_state.page == "DASHBOARD":
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="glass-card fade-in">
            <div style="text-align: center;">
                <div style="font-size: 3rem;">🧠</div>
                <div style="color: #ffffff; font-size: 1.3rem; font-weight: 600; margin: 10px 0;">
                    Chat AI
                </div>
                <div style="color: rgba(255,255,255,0.7); font-size: 0.9rem; margin-bottom: 15px;">
                    Trò chuyện với trợ lý AI thông minh
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🧠 Vào Chat AI", key="btn_chat", use_container_width=True):
            go_to("CHAT")
    
    with col2:
        st.markdown(f"""
        <div class="glass-card fade-in">
            <div style="text-align: center;">
                <div style="font-size: 3rem;">☁️</div>
                <div style="color: #ffffff; font-size: 1.3rem; font-weight: 600; margin: 10px 0;">
                    Lưu trữ Cloud
                </div>
                <div style="color: rgba(255,255,255,0.7); font-size: 0.9rem; margin-bottom: 15px;">
                    Quản lý file trên đám mây an toàn
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("☁️ Vào Lưu trữ", key="btn_cloud", use_container_width=True):
            go_to("CLOUD")
    
    if st.session_state.user and not st.session_state.guest_mode:
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            chat_count = len([s for s in st.session_state.data.get("chat_sessions", []) 
                             if s.get("owner") == st.session_state.user])
            st.markdown(f"""
            <div class="glass-card" style="text-align: center; padding: 15px;">
                <div style="font-size: 2rem;">💬</div>
                <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700;">{chat_count}</div>
                <div style="color: rgba(255,255,255,0.5); font-size: 0.8rem;">Cuộc trò chuyện</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            used = get_used_storage(st.session_state.user)
            used_gb = used / (1024**3)
            st.markdown(f"""
            <div class="glass-card" style="text-align: center; padding: 15px;">
                <div style="font-size: 2rem;">📊</div>
                <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700;">{used_gb:.1f} GB</div>
                <div style="color: rgba(255,255,255,0.5); font-size: 0.8rem;">Đã sử dụng</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            status = "💎 PRO" if is_pro else "🆓 FREE"
            st.markdown(f"""
            <div class="glass-card" style="text-align: center; padding: 15px;">
                <div style="font-size: 2rem;">{'⭐' if is_pro else '📦'}</div>
                <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700;">{status}</div>
                <div style="color: rgba(255,255,255,0.5); font-size: 0.8rem;">Gói dịch vụ</div>
            </div>
            """, unsafe_allow_html=True)

# ================== CHAT ==================
elif st.session_state.page == "CHAT":
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700;">🧠 Chat AI</div>
        <div style="color: rgba(255,255,255,0.5); font-size: 0.8rem;">
            API: {api}
        </div>
    </div>
    """.format(api=st.session_state.api_used), unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### 📝 LỊCH SỬ")
        
        if not st.session_state.guest_mode:
            if st.button("➕ Tạo mới", use_container_width=True):
                new_id = len(st.session_state.data["chat_sessions"])
                st.session_state.data["chat_sessions"].append({
                    "id": new_id,
                    "name": f"Chat {datetime.now().strftime('%H:%M %d/%m')}",
                    "owner": st.session_state.user,
                    "created": str(datetime.now()),
                    "messages": []
                })
                st.session_state.current_chat_id = new_id
                mark_data_modified()
                st.rerun()
            
            if st.button("🗑️ Xóa tất cả", use_container_width=True):
                st.session_state.data["chat_sessions"] = [
                    s for s in st.session_state.data["chat_sessions"] 
                    if s.get("owner") != st.session_state.user
                ]
                st.session_state.current_chat_id = None
                mark_data_modified()
                st.rerun()
            
            st.write("---")
            sessions = [s for s in st.session_state.data["chat_sessions"] 
                       if s.get("owner") == st.session_state.user]
            
            for s in sessions[-20:]:
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button(f"💬 {s.get('name', 'Chat')}", 
                                key=f"chat_{s.get('id')}", 
                                use_container_width=True):
                        st.session_state.current_chat_id = s.get("id")
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_{s.get('id')}"):
                        st.markdown(f"""
                        <button onclick="deleteChat({s.get('id')})" 
                                style="background:#dc2626; color:white; border:none; 
                                       border-radius:20px; padding:5px 10px; cursor:pointer;">
                            🗑️
                        </button>
                        """, unsafe_allow_html=True)
    
    if st.session_state.guest_mode:
        chat = st.session_state.temp_chat
    else:
        if st.session_state.current_chat_id is not None:
            sessions = [s for s in st.session_state.data["chat_sessions"] 
                       if s.get("id") == st.session_state.current_chat_id]
            chat = sessions[0] if sessions else {"messages": []}
        else:
            chat = None
    
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    if chat is None or not chat.get("messages"):
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; color: rgba(255,255,255,0.4);">
            <div style="font-size: 4rem; margin-bottom: 20px;">💬</div>
            <div style="font-size: 1.2rem; color: rgba(255,255,255,0.6);">Chưa có tin nhắn</div>
            <div style="font-size: 0.9rem; margin-top: 10px; color: rgba(255,255,255,0.3);">
                Hãy nhập câu hỏi để bắt đầu trò chuyện
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for m in chat["messages"]:
            role_class = "user" if m.get("role") == "user" else "assistant"
            st.markdown(f"""
            <div class="message {role_class}">
                <div class="message-bubble">
                    {m.get("content", "")}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.session_state.get("pending_message"):
        p = st.session_state.pending_message
        uploaded_file = st.session_state.get("pending_file")
        
        if uploaded_file:
            extracted = extract_text_from_file(uploaded_file)
            p = f"[File: {uploaded_file.name}]\n{extracted}" if extracted and not extracted.startswith("[") else p
        
        if not st.session_state.guest_mode and chat is None:
            new_id = len(st.session_state.data["chat_sessions"])
            st.session_state.data["chat_sessions"].append({
                "id": new_id,
                "name": f"Chat {datetime.now().strftime('%H:%M %d/%m')}",
                "owner": st.session_state.user,
                "created": str(datetime.now()),
                "messages": []
            })
            st.session_state.current_chat_id = new_id
            mark_data_modified()
            chat = st.session_state.data["chat_sessions"][-1]
        
        if st.session_state.guest_mode:
            chat["messages"].append({"role": "user", "content": p})
        else:
            chat["messages"].append({"role": "user", "content": p})
        
        with st.spinner("🧠 Đang suy nghĩ..."):
            msgs = [{"role": m.get("role"), "content": m.get("content")} 
                   for m in chat["messages"][-10:]]
            ans = call_ai(msgs)
            chat["messages"].append({"role": "assistant", "content": ans})
            if not st.session_state.guest_mode:
                mark_data_modified()
        
        st.session_state.pending_message = None
        st.session_state.pending_file = None
        st.rerun()

# ================== CLOUD ==================
elif st.session_state.page == "CLOUD":
    st.markdown("""
    <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 20px;">
        ☁️ Lưu trữ đám mây
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.guest_mode:
        st.warning("🔒 Guest không thể sử dụng lưu trữ đám mây. Vui lòng đăng ký tài khoản!")
    else:
        used = get_used_storage(st.session_state.user)
        limit = CONFIG["PRO_STORAGE_LIMIT"] if is_pro else CONFIG["FREE_STORAGE_LIMIT"]
        used_gb = used / (1024**3)
        limit_gb = "∞" if is_pro else f"{limit/(1024**3):.1f}"
        
        st.progress(
            min(used/limit, 1) if not is_pro else 0,
            text=f"📊 Đã dùng: {used_gb:.2f} GB / {limit_gb} GB"
        )
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"""
            <div style="color: rgba(255,255,255,0.7); padding: 8px 0;">
                📁 /{st.session_state.current_dir}
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.session_state.current_dir and st.button("⬆️ Lên trên", use_container_width=True):
                st.session_state.current_dir = "/".join(st.session_state.current_dir.split("/")[:-1])
                st.rerun()
        with col3:
            with st.popover("➕ Tạo thư mục"):
                new_folder = st.text_input("Tên thư mục:")
                if st.button("Tạo") and new_folder:
                    path = f"{st.session_state.current_dir}/{new_folder}" if st.session_state.current_dir else new_folder
                    if create_folder_cloud(path, st.session_state.user):
                        st.success(f"✅ Đã tạo '{new_folder}'")
                        st.rerun()
                    else:
                        st.error("❌ Thư mục đã tồn tại")
        
        items = list_directory(st.session_state.current_dir, st.session_state.user)
        
        if items["folders"]:
            st.markdown("### 📁 Thư mục")
            for folder in items["folders"]:
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(f"📁 {folder}", key=f"folder_{folder}", use_container_width=True):
                        st.session_state.current_dir = f"{st.session_state.current_dir}/{folder}" if st.session_state.current_dir else folder
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_folder_{folder}"):
                        folder_path = f"{st.session_state.current_dir}/{folder}" if st.session_state.current_dir else folder
                        delete_file_cloud(folder_path, st.session_state.user)
                        st.rerun()
        
        st.markdown("### 📄 File")
        selected = []
        
        for file in items["files"]:
            col1, col2, col3, col4 = st.columns([0.5, 4, 1, 1])
            with col1:
                if st.checkbox("", key=f"select_{file['name']}"):
                    selected.append(file['full_path'])
            with col2:
                size_kb = file['size'] / 1024
                st.markdown(f"""
                <div style="color: #e8e8e8;">
                    {file['name']}
                    <span style="color: rgba(255,255,255,0.4); font-size: 0.8rem; margin-left: 10px;">
                        {size_kb:.1f} KB
                    </span>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                file_data = base64.b64decode(st.session_state.data["files"][file['full_path']]["data"])
                st.download_button(
                    label="📥",
                    data=file_data,
                    file_name=file['name'],
                    mime=file['type'],
                    key=f"download_{file['name']}",
                    use_container_width=True
                )
            with col4:
                if st.button("🗑️", key=f"del_{file['name']}", use_container_width=True):
                    delete_file_cloud(file['full_path'], st.session_state.user)
                    st.rerun()
        
        if selected:
            if st.button(f"📦 Tải xuống {len(selected)} file (ZIP)", use_container_width=True):
                zip_data = download_files_cloud(selected)
                st.download_button(
                    label="📥 Tải ZIP",
                    data=zip_data,
                    file_name=f"nexus_cloud_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip",
                    use_container_width=True
                )
        
        with st.expander("📤 Tải file lên"):
            uploaded_files = st.file_uploader("Chọn file", accept_multiple_files=True)
            if uploaded_files:
                total_size = sum(len(f.getvalue()) for f in uploaded_files)
                if not is_pro and used + total_size > limit:
                    st.error(f"❌ Không đủ dung lượng! Còn trống: {(limit - used)/(1024**3):.2f} GB")
                else:
                    if st.button("✅ Xác nhận tải lên", use_container_width=True):
                        for f in uploaded_files:
                            file_path = f"{st.session_state.current_dir}/{f.name}" if st.session_state.current_dir else f.name
                            upload_file_cloud(file_path, f.getvalue(), st.session_state.user, f.type)
                        st.success(f"✅ Đã tải lên {len(uploaded_files)} file")
                        mark_data_modified()
                        st.rerun()

# ================== HISTORY ==================
elif st.session_state.page == "HISTORY":
    st.markdown("""
    <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 20px;">
        📜 Lịch sử chat
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.guest_mode:
        st.info("🔒 Guest không lưu lịch sử chat")
    else:
        sessions = [s for s in st.session_state.data.get("chat_sessions", []) 
                   if s.get("owner") == st.session_state.user]
        sessions.reverse()
        
        if not sessions:
            st.markdown("""
            <div style="text-align: center; padding: 40px; color: rgba(255,255,255,0.4);">
                <div style="font-size: 3rem; margin-bottom: 10px;">📭</div>
                <div>Chưa có lịch sử trò chuyện</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for s in sessions:
                with st.expander(f"💬 {s.get('name', 'Chat')} - {s.get('created', '')[:16]}"):
                    msg_count = len(s.get('messages', []))
                    st.markdown(f"""
                    <div style="color: rgba(255,255,255,0.7);">
                        📊 {msg_count} tin nhắn
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if s.get('messages'):
                        last = s['messages'][-1].get('content', '')[:100]
                        st.markdown(f"""
                        <div style="color: rgba(255,255,255,0.5); font-size: 0.9rem; margin: 10px 0;">
                            💭 {last}...
                        </div>
                        """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💬 Tiếp tục", key=f"cont_{s.get('id')}", use_container_width=True):
                            st.session_state.current_chat_id = s.get("id")
                            go_to("CHAT")
                    with col2:
                        if st.button("🗑️ Xóa", key=f"del_{s.get('id')}", use_container_width=True):
                            st.markdown(f"""
                            <button onclick="deleteChat({s.get('id')})" 
                                    style="background:#dc2626; color:white; border:none; 
                                           border-radius:50px; padding:10px; width:100%; cursor:pointer;">
                                🗑️ Xóa
                            </button>
                            """, unsafe_allow_html=True)

# ================== SETTINGS ==================
elif st.session_state.page == "SETTINGS":
    st.markdown("""
    <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 20px;">
        ⚙️ Cài đặt
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.guest_mode:
        st.info("🔒 Guest không thể đổi cài đặt")
    else:
        user_info = st.session_state.data["users"][st.session_state.user]["info"]
        
        tab1, tab2 = st.tabs(["👤 Cá nhân", "🎁 Nâng cấp"])
        
        with tab1:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if user_info.get("avatar"):
                    st.markdown(f"""
                    <img src="data:image/png;base64,{user_info['avatar']}" 
                         style="width:120px; height:120px; border-radius:50%; object-fit:cover;
                                border: 3px solid #667eea; margin: 10px auto; display: block;">
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="font-size: 80px; text-align: center; margin: 10px 0;">👤</div>
                    """, unsafe_allow_html=True)
                
                avatar_file = st.file_uploader("🖼️ Ảnh đại diện", type=["png", "jpg", "jpeg"])
                if avatar_file and st.button("💾 Cập nhật", use_container_width=True):
                    resized = resize_image(avatar_file.getvalue())
                    user_info["avatar"] = base64.b64encode(resized).decode('utf-8')
                    mark_data_modified()
                    st.success("✅ Đã cập nhật")
                    st.rerun()
            
            with col2:
                new_name = st.text_input("Tên hiển thị", value=user_info.get("name", st.session_state.user))
                if st.button("💾 Đổi tên", use_container_width=True):
                    user_info["name"] = new_name
                    mark_data_modified()
                    st.success("✅ Đã đổi tên")
                
                new_bio = st.text_area("Giới thiệu", value=user_info.get("bio", ""), height=100)
                if st.button("💾 Cập nhật giới thiệu", use_container_width=True):
                    user_info["bio"] = new_bio
                    mark_data_modified()
                    st.success("✅ Đã cập nhật")
        
        with tab2:
            st.markdown("### 🎁 Nâng cấp PRO")
            code = st.text_input("🔑 Nhập mã kích hoạt", type="password", placeholder="Nhập mã PRO...").upper()
            
            if st.button("🚀 Kích hoạt", use_container_width=True):
                found = False
                for c in st.session_state.data["codes"]:
                    if isinstance(c, dict) and c.get("code") == code:
                        found = True
                        # Kiểm tra expiry
                        if c.get("expiry"):
                            expiry_date = datetime.fromisoformat(c.get("expiry"))
                            if datetime.now() > expiry_date:
                                st.error("❌ Mã đã hết hạn!")
                                break
                        # Kiểm tra số lần sử dụng
                        if c.get("max_uses") and len(c.get("used_by", [])) >= c.get("max_uses"):
                            st.error("❌ Mã đã hết lượt sử dụng!")
                            break
                        # Kích hoạt
                        if st.session_state.user not in st.session_state.data["pro_users"]:
                            st.session_state.data["pro_users"].append(st.session_state.user)
                            c["used_by"] = c.get("used_by", []) + [st.session_state.user]
                            mark_data_modified()
                            st.balloons()
                            st.success("🎉 Chúc mừng! Bạn đã là PRO!")
                            st.rerun()
                        else:
                            st.info("Bạn đã là PRO rồi!")
                        break
                    elif isinstance(c, str) and c == code:
                        found = True
                        if st.session_state.user not in st.session_state.data["pro_users"]:
                            st.session_state.data["pro_users"].append(st.session_state.user)
                            st.session_state.data["codes"] = [x for x in st.session_state.data["codes"] if x != code]
                            mark_data_modified()
                            st.balloons()
                            st.success("🎉 Chúc mừng! Bạn đã là PRO!")
                            st.rerun()
                        else:
                            st.info("Bạn đã là PRO rồi!")
                        break
                if not found:
                    st.error("❌ Mã không hợp lệ!")
            
            if is_pro:
                st.success("✅ Bạn đang sử dụng gói PRO")
                st.markdown("""
                **✨ Đặc quyền PRO:**
                - 💾 Không giới hạn dung lượng
                - 🧠 Lịch sử chat không giới hạn
                - 🚀 Tốc độ ưu tiên
                """)

# ================== ADMIN ==================
elif st.session_state.page == "ADMIN":
    if not is_admin:
        st.error("❌ Bạn không có quyền truy cập!")
    else:
        st.markdown("""
        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 20px;">
            🛠️ Admin Panel
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🎫 Quản lý mã PRO", "👥 Quản lý người dùng"])
        
        with tab1:
            st.markdown("### ➕ Tạo mã PRO mới")
            new_code = st.text_input("Mã mới", placeholder="Nhập mã kích hoạt...").upper()
            
            col1, col2 = st.columns(2)
            with col1:
                has_expiry = st.checkbox("⏰ Có hạn sử dụng")
                expiry = st.date_input("Ngày hết hạn") if has_expiry else None
            with col2:
                has_limit = st.checkbox("🔢 Giới hạn số lần")
                max_uses = st.number_input("Số lần sử dụng", min_value=1, value=1) if has_limit else None
            
            if st.button("🎁 Tạo mã", use_container_width=True) and new_code:
                # Kiểm tra mã đã tồn tại
                exists = False
                for c in st.session_state.data["codes"]:
                    if isinstance(c, dict) and c.get("code") == new_code:
                        exists = True
                        break
                    elif isinstance(c, str) and c == new_code:
                        exists = True
                        break
                
                if exists:
                    st.error("❌ Mã này đã tồn tại!")
                else:
                    st.session_state.data["codes"].append({
                        "code": new_code,
                        "expiry": str(expiry) if expiry else None,
                        "max_uses": max_uses,
                        "used_by": []
                    })
                    mark_data_modified()
                    st.success(f"✅ Đã tạo mã: `{new_code}`")
                    st.rerun()
            
            st.markdown("---")
            st.markdown("### 📋 Danh sách mã PRO")
            
            codes = st.session_state.data.get("codes", [])
            if not codes:
                st.info("Chưa có mã PRO nào.")
            else:
                for i, c in enumerate(codes):
                    col1, col2, col3, col4 = st.columns([2, 1.5, 1.5, 1])
                    
                    if isinstance(c, dict):
                        code = c.get('code', '')
                        expiry_txt = c.get('expiry') or "Vĩnh viễn"
                        used = len(c.get('used_by', []))
                        max_txt = str(c.get('max_uses')) if c.get('max_uses') else "∞"
                        
                        # Hiển thị trạng thái
                        is_expired = False
                        if c.get('expiry'):
                            try:
                                expiry_date = datetime.fromisoformat(c.get('expiry'))
                                if datetime.now() > expiry_date:
                                    is_expired = True
                            except:
                                pass
                        
                        is_full = c.get('max_uses') and used >= c.get('max_uses')
                        
                        status_emoji = "✅" if not is_expired and not is_full else "❌"
                        status_text = "Hết hạn" if is_expired else "Hết lượt" if is_full else "Còn hiệu lực"
                        
                        col1.write(f"**{code}**")
                        col2.write(f"⏰ {expiry_txt}")
                        col3.write(f"📊 {used}/{max_txt}")
                        col4.write(f"{status_emoji} {status_text}")
                        
                        # Nút xóa
                        if col4.button(f"🗑️ Xóa", key=f"del_code_{i}"):
                            if delete_pro_code(code):
                                st.success(f"✅ Đã xóa mã `{code}`")
                                st.rerun()
                    else:
                        # Trường hợp code là string (tương thích ngược)
                        col1.write(f"**{c}**")
                        col2.write("Vĩnh viễn")
                        col3.write("∞")
                        if col4.button(f"🗑️ Xóa", key=f"del_code_str_{i}"):
                            if delete_pro_code(c):
                                st.success(f"✅ Đã xóa mã `{c}`")
                                st.rerun()
                    st.divider()
        
        with tab2:
            st.markdown("### 👥 Quản lý người dùng")
            
            users = st.session_state.data.get("users", {})
            pro_users = st.session_state.data.get("pro_users", [])
            
            for username, user_data in users.items():
                col1, col2, col3, col4 = st.columns([2, 2, 1.5, 1.5])
                col1.write(f"**{username}**")
                col2.write(user_data['info'].get('name', ''))
                
                is_pro_user = username in pro_users
                col3.write("💎 PRO" if is_pro_user else "🆓 FREE")
                
                if username != ADMIN_USERNAME:
                    col4_1, col4_2 = st.columns(2)
                    with col4_1:
                        # Nút toggle PRO
                        if is_pro_user:
                            if st.button(f"⬇️ Hạ PRO", key=f"downgrade_{username}", use_container_width=True):
                                if username in st.session_state.data["pro_users"]:
                                    st.session_state.data["pro_users"].remove(username)
                                    mark_data_modified()
                                    st.success(f"✅ Đã hạ cấp {username}")
                                    st.rerun()
                        else:
                            if st.button(f"⬆️ Lên PRO", key=f"upgrade_{username}", use_container_width=True):
                                if username not in st.session_state.data["pro_users"]:
                                    st.session_state.data["pro_users"].append(username)
                                    mark_data_modified()
                                    st.success(f"✅ Đã nâng cấp {username} lên PRO")
                                    st.rerun()
                    with col4_2:
                        if st.button(f"🗑️ Xóa", key=f"del_user_{username}", use_container_width=True):
                            if username in st.session_state.data["users"]:
                                del st.session_state.data["users"][username]
                                if username in st.session_state.data.get("pro_users", []):
                                    st.session_state.data["pro_users"].remove(username)
                                mark_data_modified()
                                st.success(f"✅ Đã xóa user {username}")
                                st.rerun()
                else:
                    col4.write("👑 Admin")
                st.divider()

# ================== ABOUT ==================
elif st.session_state.page == "ABOUT":
    st.markdown(f"""
    <div class="glass-card" style="text-align: center;">
        <div style="font-size: 4rem; margin-bottom: 10px;">🚀</div>
        <div style="color: #ffffff; font-size: 2rem; font-weight: 700;">{CONFIG['NAME']}</div>
        <div style="color: rgba(255,255,255,0.5); font-size: 1rem; margin-bottom: 20px;">
            Phiên bản {CONFIG['VERSION']}
        </div>
        <div style="color: rgba(255,255,255,0.7); margin-bottom: 20px;">
            Sáng tạo bởi <strong>{CONFIG['CREATOR']}</strong>
        </div>
        <div style="color: rgba(255,255,255,0.4); font-style: italic;">
            "Kết nối tri thức, mở ra tương lai"
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="glass-card">
            <div style="color: #ffffff; font-weight: 600; font-size: 1.1rem; margin-bottom: 15px;">
                🤖 Trí tuệ nhân tạo
            </div>
            <div style="color: rgba(255,255,255,0.7); font-size: 0.9rem; line-height: 1.8;">
                ✅ Chat AI thông minh<br>
                ✅ Phân tích file văn bản<br>
                ✅ Xử lý ngôn ngữ tự nhiên<br>
                ✅ Hỗ trợ Groq & Gemini
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="glass-card">
            <div style="color: #ffffff; font-weight: 600; font-size: 1.1rem; margin-bottom: 15px;">
                ☁️ Lưu trữ đám mây
            </div>
            <div style="color: rgba(255,255,255,0.7); font-size: 0.9rem; line-height: 1.8;">
                ✅ Quản lý file và thư mục<br>
                ✅ Tải lên/xuống hàng loạt<br>
                ✅ Tạo ZIP nhiều file<br>
                ✅ Free 30GB · PRO không giới hạn
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="text-align: center; color: rgba(255,255,255,0.3); font-size: 0.8rem; margin-top: 30px;">
        © 2025-2026 {CONFIG['CREATOR']} · {CONFIG['NAME']}
    </div>
    """, unsafe_allow_html=True)

# ================== KẾT THÚC ==================
check_and_auto_backup()
