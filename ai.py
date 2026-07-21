import os
import sys
import subprocess

# ==========================================
# TỰ ĐỘNG KIỂM TRA VÀ CÀI ĐẶT THƯ VIỆN NẾU THIẾU
# ==========================================
def auto_install_libraries():
    required_libraries = {
        "customtkinter": "customtkinter",
        "llama_cpp": "llama-cpp-python"
    }
    missing_libraries = []
    for lib_name, pip_name in required_libraries.items():
        try:
            __import__(lib_name)
        except ImportError:
            missing_libraries.append(pip_name)
            
    if missing_libraries:
        print("=" * 60)
        print("PHÁT HIỆN THIẾU THƯ VIỆN HỆ THỐNG!")
        print(f"Đang tiến hành tự động cài đặt: {', '.join(missing_libraries)}")
        print("Vui lòng đợi trong giây lát...")
        print("=" * 60)
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
            for lib in missing_libraries:
                print(f"\n[Nexus System] Cài đặt {lib}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
            print("\n" + "=" * 60)
            print("CÀI ĐẶT HOÀN TẤT! Đang khởi động Nexus AI Gateway...")
            print("=" * 60 + "\n")
        except Exception as e:
            print(f"\n[LỖI] Không thể tự động cài đặt thư viện: {e}")
            input("Nhấn Enter để thoát...")
            sys.exit(1)

auto_install_libraries()

# ==========================================
# KHỞI CHẠY KHÔNG GIAN ỨNG DỤNG CHÍNH
# ==========================================
import json
import threading
import time
import gc
import customtkinter as ctk
from llama_cpp import Llama

# TỰ ĐỘNG ĐỊNH VỊ THƯ MỤC CÙNG CẤP VỚI FILE SCRIPT
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")

class SettingsWindow(ctk.CTkToplevel):
    """Cửa sổ cài đặt phụ gom gọn tất cả tính năng quản lý mô hình và ngôn ngữ"""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Nexus Settings")
        self.geometry("420x450")
        self.resizable(False, False)
        self.transient(parent)  
        self.grab_set()         
        
        self.configure(fg_color="#1a1a1a")
        
        # Tiêu đề quản lý mô hình
        self.lbl_model = ctk.CTkLabel(self, text="", font=("Segoe UI", 13, "bold"), text_color="#ffffff")
        self.lbl_model.pack(anchor="w", padx=20, pady=(20, 5))
        
        self.frame_model = ctk.CTkFrame(self, fg_color="#222222", corner_radius=8)
        self.frame_model.pack(fill="x", padx=20, pady=5)
        
        self.opt_models = ctk.CTkOptionMenu(self.frame_model, values=list(self.parent.config["models"].keys()), command=self.parent.change_model_selection, fg_color="#2b2b2b", button_color="#3a3a3a", text_color="#ffffff")
        self.opt_models.set(self.parent.config["current_model"])
        self.opt_models.pack(fill="x", padx=15, pady=10)
        
        self.frame_model_buttons = ctk.CTkFrame(self.frame_model, fg_color="transparent")
        self.frame_model_buttons.pack(fill="x", padx=15, pady=(0, 10))
        
        self.btn_add_model = ctk.CTkButton(self.frame_model_buttons, text="", width=180, height=30, font=("Segoe UI", 12), fg_color="#2baf54", hover_color="#228b42", text_color="#ffffff", command=self.add_model_action)
        self.btn_add_model.pack(side="left")
        
        self.btn_del_model = ctk.CTkButton(self.frame_model_buttons, text="", width=180, height=30, font=("Segoe UI", 12), fg_color="#c9302c", hover_color="#a72825", text_color="#ffffff", command=self.del_model_action)
        self.btn_del_model.pack(side="right")
        
        # Tiêu đề quản lý ngôn ngữ mở rộng
        self.lbl_lang = ctk.CTkLabel(self, text="", font=("Segoe UI", 13, "bold"), text_color="#ffffff")
        self.lbl_lang.pack(anchor="w", padx=20, pady=(20, 5))
        
        self.frame_lang = ctk.CTkFrame(self, fg_color="#222222", corner_radius=8)
        self.frame_lang.pack(fill="x", padx=20, pady=5)
        
        self.btn_add_lang = ctk.CTkButton(self.frame_lang, text="", height=32, font=("Segoe UI", 12), fg_color="#333333", text_color="#ffffff", command=self.add_lang_action)
        self.btn_add_lang.pack(fill="x", padx=15, pady=(15, 8))
        
        self.btn_del_lang = ctk.CTkButton(self.frame_lang, text="", height=32, font=("Segoe UI", 12), fg_color="#555555", text_color="#ffffff", command=self.del_lang_action)
        self.btn_del_lang.pack(fill="x", padx=15, pady=(0, 15))
        
        self.update_languages()

    def update_languages(self):
        lang = self.parent.config["current_lang"]
        trans = self.parent.translations.get(lang, self.parent.translations["en"])
        
        self.lbl_model.configure(text=trans["lbl_model_manage"])
        self.lbl_lang.configure(text=trans["lbl_lang_manage"])
        self.btn_add_model.configure(text=trans["settings_add_model"])
        self.btn_del_model.configure(text=trans["settings_del_model"])
        self.btn_add_lang.configure(text=trans["settings_add_lang"])
        self.btn_del_lang.configure(text=trans["settings_del_lang"])

    def add_model_action(self):
        lang = self.parent.config["current_lang"]
        trans = self.parent.translations.get(lang, self.parent.translations["en"])
        
        dialog_name = ctk.CTkInputDialog(text=trans["prompt_model_name"], title="Add Model")
        name = dialog_name.get_input()
        if not name: return
        
        dialog_path = ctk.CTkInputDialog(text=trans["prompt_model_path"], title="Model Path")
        path = dialog_path.get_input()
        if not path: return
        
        # Chuẩn hóa đường dẫn: Nếu truyền file ở thư mục hiện tại thì tự chuyển thành đường dẫn tuyệt đối chính xác
        raw_path = path.strip('"').strip("'")
        if not os.path.isabs(raw_path):
            raw_path = os.path.join(BASE_DIR, raw_path)
            
        self.parent.config["models"][name] = raw_path
        self.parent.config["current_model"] = name
        self.parent.save_settings_data()
        
        self.opt_models.configure(values=list(self.parent.config["models"].keys()))
        self.opt_models.set(name)
        self.parent.update_main_model_menu()

    def del_model_action(self):
        current = self.opt_models.get()
        if len(self.parent.config["models"]) <= 1:
            return
        
        if self.parent.ai is not None and self.parent.config["current_model"] == current:
            self.parent.toggle_model()
            
        del self.parent.config["models"][current]
        first_key = list(self.parent.config["models"].keys())[0]
        self.parent.config["current_model"] = first_key
        self.parent.save_settings_data()
        
        self.opt_models.configure(values=list(self.parent.config["models"].keys()))
        self.opt_models.set(first_key)
        self.parent.update_main_model_menu()

    def add_lang_action(self):
        lang = self.parent.config["current_lang"]
        trans = self.parent.translations.get(lang, self.parent.translations["en"])
        
        dialog_code = ctk.CTkInputDialog(text=trans["prompt_lang_code"], title="Language Code")
        code = dialog_code.get_input()
        if not code: return
        code = code.strip().lower()
        
        dialog_name = ctk.CTkInputDialog(text=trans["prompt_lang_name"], title="Language Name")
        name = dialog_name.get_input()
        if not name: return
        
        self.parent.config["languages"][code] = {"name": name}
        self.parent.register_dynamic_translation(code, name)
        self.parent.save_settings_data()
        self.update_languages()

    def del_lang_action(self):
        current = self.parent.config["current_lang"]
        if current in ["vi", "en"]:
            return
            
        del self.parent.config["languages"][current]
        self.parent.config["current_lang"] = "vi"
        self.parent.save_settings_data()
        
        self.parent.btn_lang_toggle.configure(text="🌐 VI")
        self.parent.apply_language_ui()
        self.parent.render_current_chat_messages()
        self.update_languages()


class ChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Nexus AI Gateway")
        self.geometry("1050x780")
        self.resizable(True, True)
        
        self.ai = None
        self.sidebar_visible = True
        self.bubble_widgets = []
        self.current_streaming_bubble = None
        self.chat_buttons_refs = {}
        self.settings_window = None
        self.placeholder_text = ""
        
        self.load_settings_data()
        self.load_history_data()
        
        self.translations = {
            "vi": {
                "btn_new_chat": "+ Tạo cuộc trò chuyện",
                "status_offline": "AI Chưa nạp",
                "status_loading": "Đang nạp AI...",
                "status_unloading": "Đang giải phóng RAM...",
                "status_online": "AI Sẵn sàng",
                "status_failed": "Lỗi nạp file",
                "btn_load": "Khởi động bộ não AI",
                "btn_unload": "Giải phóng RAM",
                "placeholder_msg": "Nhập tin nhắn tới AI...",
                "btn_send": "GỬI",
                "sys_offline_msg": "Hệ thống: AI đang ngoại tuyến. Hãy nhấn nút khởi động phía trên.",
                "sys_online_msg": "Hệ thống: Kết nối thành công cục bộ. Hãy bắt đầu chat.",
                "new_chat_title": "Cuộc trò chuyện mới",
                "lbl_model_manage": "QUẢN LÝ MÔ HÌNH LLM (.GGUF)",
                "lbl_lang_manage": "QUẢN LÝ NGÔN NGỮ HỆ THỐNG",
                "btn_settings": "⚙️ Cài đặt hệ thống",
                "settings_add_model": "+ Thêm Model",
                "settings_del_model": "✕ Xóa Model",
                "settings_add_lang": "+ Thêm Ngôn Ngữ Mới",
                "settings_del_lang": "✕ Xóa Ngôn Ngữ Hiện Tại",
                "prompt_model_name": "Nhập tên nhãn của mô hình mới (VD: Llama3):",
                "prompt_model_path": "Nhập đường dẫn tuyệt đối tới file .gguf:",
                "prompt_lang_code": "Nhập mã ngôn ngữ viết tắt (Ví dụ: fr, ja, ru):",
                "prompt_lang_name": "Nhập tên hiển thị (Ví dụ: French):"
            },
            "en": {
                "btn_new_chat": "+ Create New Chat",
                "status_offline": "AI Offline",
                "status_loading": "Loading AI...",
                "status_unloading": "Freeing RAM...",
                "status_online": "AI Ready",
                "status_failed": "Load Failed",
                "btn_load": "Boot AI Engine",
                "btn_unload": "Free Up RAM",
                "placeholder_msg": "Type a message to AI...",
                "btn_send": "SEND",
                "sys_offline_msg": "System: AI is offline. Please boot the engine above.",
                "sys_online_msg": "System: Connected successfully. Start chatting.",
                "new_chat_title": "New Conversation",
                "lbl_model_manage": "LLM MODEL MANAGEMENT (.GGUF)",
                "lbl_lang_manage": "SYSTEM LANGUAGE MANAGEMENT",
                "btn_settings": "⚙️ System Settings",
                "settings_add_model": "+ Add Model",
                "settings_del_model": "✕ Delete Model",
                "settings_add_lang": "+ Add New Language",
                "settings_del_lang": "✕ Delete Current Language",
                "prompt_model_name": "Enter new model label name (e.g. Llama3):",
                "prompt_model_path": "Enter absolute path to .gguf file:",
                "prompt_lang_code": "Enter language code abbreviation (e.g. fr, ja):",
                "prompt_lang_name": "Enter display name (e.g. French):"
            }
        }
        
        for lang_code, lang_info in self.config["languages"].items():
            if lang_code not in self.translations:
                self.register_dynamic_translation(lang_code, lang_info['name'])

        # ---------------- GIAO DIỆN TỔNG THỂ (GRID 2 CỘT) ----------------
        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=3) 
        self.grid_rowconfigure(0, weight=1)
        
        # ==========================================
        # PHẦN 1: SIDEBAR TỐI GIẢN (CHỮ TRẮNG TOÀN BỘ)
        # ==========================================
        self.sidebar = ctk.CTkFrame(self, corner_radius=0, fg_color="#1e1e1e", width=280)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        self.btn_new_chat = ctk.CTkButton(self.sidebar, text="", command=self.create_new_chat, fg_color="#0068ff", hover_color="#0052cc", font=("Segoe UI", 13, "bold"), text_color="#ffffff", height=38)
        self.btn_new_chat.pack(pady=10, padx=12, fill="x")
        
        self.scroll_chat_list = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.scroll_chat_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.divider = ctk.CTkFrame(self.sidebar, fg_color="#333333", height=2)
        self.divider.pack(fill="x", pady=10, padx=10)
        
        self.lbl_active_model_title = ctk.CTkLabel(self.sidebar, text="MODEL:", font=("Segoe UI", 10, "bold"), text_color="#ffffff")
        self.lbl_active_model_title.pack(anchor="w", padx=15, pady=0)
        
        self.lbl_active_model = ctk.CTkLabel(self.sidebar, text=self.config["current_model"], font=("Segoe UI", 12, "italic"), text_color="#ffffff")
        self.lbl_active_model.pack(anchor="w", padx=15, pady=(0, 10))
        
        self.btn_open_settings = ctk.CTkButton(self.sidebar, text="", height=36, font=("Segoe UI", 12, "bold"), fg_color="#2b2b2b", hover_color="#3a3a3a", text_color="#ffffff", command=self.open_settings_window)
        self.btn_open_settings.pack(fill="x", padx=12, pady=12)

        # ==========================================
        # PHẦN 2: KHUNG TRÒ CHUYỆN CHÍNH (MAIN AREA)
        # ==========================================
        self.main_area = ctk.CTkFrame(self, fg_color="#121212", corner_radius=0)
        self.main_area.grid(row=0, column=1, sticky="nsew")
        
        self.frame_top = ctk.CTkFrame(self.main_area, fg_color="#1a1a1a", height=50, corner_radius=0)
        self.frame_top.pack(fill="x", side="top")
        
        self.btn_toggle_sidebar = ctk.CTkButton(self.frame_top, text="☰", width=35, height=32, fg_color="transparent", hover_color="#262626", font=("Segoe UI", 16, "bold"), text_color="#ffffff", command=self.toggle_sidebar)
        self.btn_toggle_sidebar.pack(pady=8, padx=(10, 5), side="left")
        
        self.lbl_brand = ctk.CTkLabel(self.frame_top, text="NEXUS AI GATEWAY", font=("Segoe UI", 15, "bold"), text_color="#ffffff")
        self.lbl_brand.pack(pady=8, padx=5, side="left")
        
        self.btn_lang_toggle = ctk.CTkButton(self.frame_top, text=f"🌐 {self.config['current_lang'].upper()}", width=65, height=32, fg_color="#262626", font=("Segoe UI", 12, "bold"), text_color="#ffffff", command=self.toggle_language_runtime)
        self.btn_lang_toggle.pack(pady=8, padx=10, side="left")
        
        self.btn_load = ctk.CTkButton(self.frame_top, text="", command=self.toggle_model, fg_color="#333333", font=("Segoe UI", 12, "bold"), text_color="#ffffff", height=32)
        self.btn_load.pack(pady=8, padx=15, side="right")
        
        self.lbl_status = ctk.CTkLabel(self.frame_top, text="", font=("Segoe UI", 13, "bold"), text_color="#ffffff")
        self.lbl_status.pack(pady=8, padx=15, side="right")
        
        self.scroll_chat_view = ctk.CTkScrollableFrame(self.main_area, fg_color="#121212", corner_radius=0)
        self.scroll_chat_view.pack(fill="both", expand=True, padx=10, pady=5)
        
        # --- THANH NHẬP LIỆU PHÍA DƯỚI (MÀU CHỮ TRẮNG) ---
        self.frame_input = ctk.CTkFrame(self.main_area, fg_color="#1a1a1a", height=60, corner_radius=0)
        self.frame_input.pack(fill="x", side="bottom")
        
        self.entry_msg = ctk.CTkEntry(self.frame_input, font=("Segoe UI", 14), fg_color="#262626", text_color="#ffffff", border_width=0, height=40)
        self.entry_msg.pack(side="left", fill="x", expand=True, padx=(15, 10), pady=10)
        self.entry_msg.bind("<Return>", lambda event: self.send_message())
        
        self.entry_msg.bind("<FocusIn>", self.on_entry_focus_in)
        self.entry_msg.bind("<FocusOut>", self.on_entry_focus_out)
        
        self.btn_send = ctk.CTkButton(self.frame_input, text="", width=70, height=40, command=self.send_message, state="normal", font=("Segoe UI", 13, "bold"), fg_color="#0068ff", hover_color="#0052cc", text_color="#ffffff")
        self.btn_send.pack(side="right", padx=(0, 15), pady=10)
        
        self.apply_language_ui()
        self.refresh_sidebar()
        self.select_default_or_first_chat()

    def on_entry_focus_in(self, event):
        if self.entry_msg.get() == self.placeholder_text:
            self.entry_msg.delete(0, "end")
            self.entry_msg.configure(text_color="#ffffff")

    def on_entry_focus_out(self, event):
        if self.entry_msg.get().strip() == "":
            self.entry_msg.delete(0, "end")
            self.entry_msg.insert(0, self.placeholder_text)
            self.entry_msg.configure(text_color="#ffffff")

    def register_dynamic_translation(self, code, name):
        self.translations[code] = {
            "btn_new_chat": f"+ {name}", "status_offline": f"Offline ({code.upper()})", "status_loading": "Loading...",
            "status_unloading": "Unloading...", "status_online": "Online", "status_failed": "Failed", "btn_load": f"Boot AI ({code.upper()})",
            "btn_unload": "Free RAM", "placeholder_msg": "Type message...", "btn_send": "SEND",
            "sys_offline_msg": "AI Offline", "sys_online_msg": "AI Connected", "new_chat_title": "New Chat",
            "lbl_model_manage": "MODELS MANAGEMENT", "lbl_lang_manage": "LANGUAGES MANAGEMENT",
            "btn_settings": f"⚙️ Settings ({code.upper()})",
            "settings_add_model": "+ Add Model", "settings_del_model": "✕ Delete Model",
            "settings_add_lang": "+ Add New Language", "settings_del_lang": "✕ Delete Current Language",
            "prompt_model_name": "Model name:", "prompt_model_path": "Model path .gguf:",
            "prompt_lang_code": "Language code:", "prompt_lang_name": "Language name:"
        }

    def load_settings_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                    return
            except:
                pass
        
        # TỰ ĐỘNG THÔNG MINH: Quét tất cả file .gguf nằm cùng thư mục để đưa vào danh sách nếu file json chưa được tạo
        gguf_files = [file for file in os.listdir(BASE_DIR) if file.endswith(".gguf")]
        detected_models = {}
        current_active = "Qwen2.5-1.5B"
        
        if gguf_files:
            for file in gguf_files:
                name_label = os.path.splitext(file)[0]
                detected_models[name_label] = os.path.join(BASE_DIR, file)
            current_active = list(detected_models.keys())[0]
        else:
            # Dự phòng tên file mặc định nếu thư mục hiện tại trống rỗng
            detected_models = {
                "Qwen2.5-1.5B": os.path.join(BASE_DIR, "qwen2.5-1.5b-instruct-q3_k_m.gguf")
            }
            
        self.config = {
            "current_lang": "vi",
            "current_model": current_active,
            "models": detected_models,
            "languages": {
                "vi": {"name": "Tiếng Việt"},
                "en": {"name": "English"}
            }
        }
        self.save_settings_data()

    # BỔ SUNG HÀM LƯU CONFIG PHỤC HỒI LỖI ATTRIBUTEERROR
    def save_settings_data(self):
        """Ghi cấu hình cài đặt hiện tại xuống file JSON cục bộ"""
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    def load_history_data(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.all_chats = json.load(f)
                    if isinstance(self.all_chats, list):
                        return
            except:
                pass
        self.all_chats = []

    def save_history_data(self):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.all_chats, f, ensure_ascii=False, indent=4)

    def toggle_language_runtime(self):
        available_langs = list(self.config["languages"].keys())
        current_idx = available_langs.index(self.config["current_lang"])
        next_idx = (current_idx + 1) % len(available_langs)
        
        self.config["current_lang"] = available_langs[next_idx]
        self.save_settings_data()
        
        self.btn_lang_toggle.configure(text=f"🌐 {self.config['current_lang'].upper()}")
        self.apply_language_ui()
        self.render_current_chat_messages()
        self.refresh_sidebar()
        
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.update_languages()

    def apply_language_ui(self):
        lang = self.config["current_lang"]
        trans = self.translations.get(lang, self.translations["en"])
        
        self.btn_new_chat.configure(text=trans["btn_new_chat"])
        self.btn_send.configure(text=trans["btn_send"])
        self.btn_open_settings.configure(text=trans["btn_settings"])
        
        old_placeholder = self.placeholder_text
        self.placeholder_text = trans["placeholder_msg"]
        
        current_text = self.entry_msg.get()
        if current_text == "" or current_text == old_placeholder:
            self.entry_msg.delete(0, "end")
            self.entry_msg.insert(0, self.placeholder_text)
            self.entry_msg.configure(text_color="#ffffff")
        
        if self.ai is None:
            self.lbl_status.configure(text=trans["status_offline"], text_color="#ffffff")
            self.btn_load.configure(text=trans["btn_load"], fg_color="#333333")
        else:
            self.lbl_status.configure(text=trans["status_online"], text_color="#ffffff")
            self.btn_load.configure(text=trans["btn_unload"], fg_color="#c9302c")

    def open_settings_window(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self)
        else:
            self.settings_window.focus()

    def change_model_selection(self, choice):
        self.config["current_model"] = choice
        self.save_settings_data()
        self.update_main_model_menu()
        if self.ai is not None:
            self.toggle_model()

    def update_main_model_menu(self):
        self.lbl_active_model.configure(text=self.config["current_model"])

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar.grid_forget()
            self.grid_columnconfigure(0, weight=0)
            self.sidebar_visible = False
        else:
            self.sidebar.grid(row=0, column=0, sticky="nsew")
            self.grid_columnconfigure(0, weight=1)
            self.sidebar_visible = True

    def select_default_or_first_chat(self):
        if not self.all_chats:
            self.create_new_chat()
        else:
            self.switch_chat(self.all_chats[0]["id"])

    def create_new_chat(self):
        lang = self.config["current_lang"]
        default_title = self.translations.get(lang, self.translations["en"])["new_chat_title"]
        
        chat_id = str(int(time.time() * 1000))
        new_chat = {
            "id": chat_id,
            "title": default_title,
            "messages": [{"role": "system", "content": "You are a helpful local AI assistant."}]
        }
        self.all_chats.insert(0, new_chat)
        self.save_history_data()
        self.refresh_sidebar()
        self.switch_chat(chat_id)

    def delete_chat(self, chat_id):
        self.all_chats = [c for c in self.all_chats if c["id"] != chat_id]
        self.save_history_data()
        self.refresh_sidebar()
        if self.current_chat_id == chat_id:
            self.current_chat_id = None
            self.select_default_or_first_chat()
        elif not self.all_chats:
            self.select_default_or_first_chat()

    def switch_chat(self, chat_id):
        if not any(c["id"] == chat_id for c in self.all_chats): return
        self.current_chat_id = chat_id
        
        for cid, widgets in self.chat_buttons_refs.items():
            if cid == chat_id:
                widgets["btn"].configure(fg_color="#262626")
            else:
                widgets["btn"].configure(fg_color="transparent")
        self.render_current_chat_messages()

    def refresh_sidebar(self):
        for widgets in self.chat_buttons_refs.values():
            widgets["frame"].destroy()
        self.chat_buttons_refs.clear()
        
        lang = self.config["current_lang"]
        default_title = self.translations.get(lang, self.translations["en"])["new_chat_title"]
        
        for chat_data in self.all_chats:
            chat_id = chat_data["id"]
            item_frame = ctk.CTkFrame(self.scroll_chat_list, fg_color="transparent")
            item_frame.pack(fill="x", pady=3, padx=2)
            
            display_title = chat_data['title']
            if display_title in ["Cuộc trò chuyện mới", "New Conversation", "New Chat"]:
                display_title = default_title
                
            btn_title = ctk.CTkButton(item_frame, text=f"💬  {display_title}", anchor="w", fg_color="transparent", hover_color="#262626", font=("Segoe UI", 13), text_color="#ffffff", height=35, command=lambda cid=chat_id: self.switch_chat(cid))
            btn_title.pack(side="left", fill="x", expand=True)
            
            btn_del = ctk.CTkButton(item_frame, text="✕", width=25, height=35, fg_color="transparent", hover_color="#3a1e1e", text_color="#ffffff", font=("Segoe UI", 12), command=lambda cid=chat_id: self.delete_chat(cid))
            btn_del.pack(side="right", padx=(2, 0))
            
            self.chat_buttons_refs[chat_id] = {"frame": item_frame, "btn": btn_title}

    def get_chat_by_id(self, chat_id):
        for c in self.all_chats:
            if c["id"] == chat_id: return c
        return None

    def clear_chat_view(self):
        for w in self.bubble_widgets:
            w.destroy()
        self.bubble_widgets.clear()
        self.current_streaming_bubble = None

    def add_bubble_message(self, text, sender="user"):
        row_container = ctk.CTkFrame(self.scroll_chat_view, fg_color="transparent")
        row_container.pack(fill="x", pady=6, padx=5)
        self.bubble_widgets.append(row_container)
        
        if sender == "user":
            bubble = ctk.CTkLabel(row_container, text=text, fg_color="#0068ff", text_color="#ffffff", font=("Segoe UI", 13), corner_radius=12, padx=12, pady=8, wraplength=450, justify="left")
            bubble.pack(side="right", anchor="e")
        elif sender == "assistant":
            bubble = ctk.CTkLabel(row_container, text=text, fg_color="#262626", text_color="#ffffff", font=("Segoe UI", 13), corner_radius=12, padx=12, pady=8, wraplength=450, justify="left")
            bubble.pack(side="left", anchor="w")
            return bubble
        else:
            bubble = ctk.CTkLabel(row_container, text=text, text_color="#ffffff", font=("Segoe UI", 11, "italic"), justify="center")
            bubble.pack(side="top", pady=2)
        self.scroll_chat_view._parent_canvas.yview_moveto(1.0)

    def render_current_chat_messages(self):
        self.clear_chat_view()
        current_chat = self.get_chat_by_id(self.current_chat_id)
        if not current_chat: return
        
        lang = self.config["current_lang"]
        trans = self.translations.get(lang, self.translations["en"])
            
        if self.ai is None:
            self.add_bubble_message(trans["sys_offline_msg"], "system")
        else:
            self.add_bubble_message(trans["sys_online_msg"], "system")
            
        for msg in current_chat["messages"]:
            if msg["role"] == "user":
                self.add_bubble_message(msg["content"], "user")
            elif msg["role"] == "assistant":
                self.add_bubble_message(msg["content"], "assistant")

    def toggle_model(self):
        lang = self.config["current_lang"]
        trans = self.translations.get(lang, self.translations["en"])
        
        if self.ai is None:
            self.lbl_status.configure(text=trans["status_loading"], text_color="#ffffff")
            self.btn_load.configure(state="disabled")
            threading.Thread(target=self.load_model_worker, daemon=True).start()
        else:
            self.lbl_status.configure(text=trans["status_unloading"], text_color="#ffffff")
            self.btn_load.configure(state="disabled")
            threading.Thread(target=self.unload_model_worker, daemon=True).start()

    def load_model_worker(self):
        lang = self.config["current_lang"]
        trans = self.translations.get(lang, self.translations["en"])
        active_model_name = self.config["current_model"]
        model_path = self.config["models"].get(active_model_name, "")
        
        # KIỂM TRA PHÒNG HỜ: Nếu di chuyển thư mục dẫn đến sai đường dẫn tuyệt đối cũ
        # Phần mềm sẽ tự kiểm tra xem file mô hình có nằm ngay trong thư mục cùng cấp hiện tại hay không
        if not os.path.exists(model_path):
            filename = os.path.basename(model_path)
            local_fallback_path = os.path.join(BASE_DIR, filename)
            if os.path.exists(local_fallback_path):
                model_path = local_fallback_path
                self.config["models"][active_model_name] = local_fallback_path
                self.save_settings_data()
        
        try:
            if not os.path.exists(model_path):
                raise FileNotFoundError()
                
            # ĐIỀU CHỈNH TỐI ƯU HÓA PHẦN CỨNG LINH HOẠT (ĐÁP ỨNG MỌI THIẾT BỊ)
            detected_cores = os.cpu_count() or 4
            # Phân bổ luồng xử lý thông minh để CPU chạy hết công suất mà không bị nghẽn hệ thống
            optimal_threads = max(2, detected_cores - 1) if detected_cores > 2 else detected_cores

            self.ai = Llama(
                model_path=model_path, 
                n_ctx=512,                  # Thu gọn dung lượng ngữ cảnh để chống tràn RAM trên máy yếu
                n_threads=optimal_threads,   # Tự động thay đổi tương thích với cấu hình CPU của thiết bị
                use_mmap=True,               # Bật ánh xạ SSD làm bộ nhớ ảo giảm áp lực trực tiếp lên thanh RAM
                use_mlock=False,             # Cho phép hệ điều hành chủ động giải phóng bộ nhớ khi cần, tránh đứng máy
                verbose=False
            )
            self.btn_load.configure(state="normal")
            self.apply_language_ui()
            self.render_current_chat_messages()
        except Exception:
            self.ai = None
            self.btn_load.configure(state="normal")
            self.lbl_status.configure(text=trans["status_failed"], text_color="#ffffff")

    def unload_model_worker(self):
        if self.ai is not None:
            try:
                if hasattr(self.ai, "close"):
                    self.ai.close()
                del self.ai
            except:
                pass
            self.ai = None
            
        gc.collect()
        gc.collect()
        
        self.btn_load.configure(state="normal")
        self.apply_language_ui()
        self.render_current_chat_messages()

    def send_message(self):
        cau_hoi = self.entry_msg.get().strip()
        if not cau_hoi or cau_hoi == self.placeholder_text or not self.current_chat_id: 
            return
            
        has_focus = (self.focus_get() == self.entry_msg)
        
        if self.ai is None:
            self.add_bubble_message(cau_hoi, "user")
            self.entry_msg.delete(0, "end")
            if not has_focus:
                self.entry_msg.insert(0, self.placeholder_text)
            lang = self.config["current_lang"]
            trans = self.translations.get(lang, self.translations["en"])
            self.add_bubble_message(trans["sys_offline_msg"], "system")
            return
            
        self.entry_msg.delete(0, "end")
        if not has_focus:
            self.entry_msg.insert(0, self.placeholder_text)
            
        self.add_bubble_message(cau_hoi, "user")
        self.current_streaming_bubble = self.add_bubble_message("...", "assistant")
        self.btn_send.configure(state="disabled")
        
        current_chat = self.get_chat_by_id(self.current_chat_id)
        if not current_chat: return
            
        is_first_message = len(current_chat["messages"]) <= 1
        current_chat["messages"].append({"role": "user", "content": cau_hoi})
        self.save_history_data()
        
        threading.Thread(target=self.ai_reply_worker, args=(is_first_message, cau_hoi), daemon=True).start()

    def ai_reply_worker(self, is_first_message, cau_hoi):
        try:
            current_chat = self.get_chat_by_id(self.current_chat_id)
            if not current_chat: return
            
            phan_hoi = self.ai.create_chat_completion(messages=current_chat["messages"], stream=True)
            cau_tra_loi_day_du = ""
            for chu_cai in phan_hoi:
                if self.ai is None: break
                delta = chu_cai['choices'][0]['delta']
                if 'content' in delta:
                    chu = delta['content']
                    cau_tra_loi_day_du += chu
                    if self.current_streaming_bubble:
                        self.current_streaming_bubble.configure(text=cau_tra_loi_day_du)
                        self.scroll_chat_view._parent_canvas.yview_moveto(1.0)
                        
            current_chat = self.get_chat_by_id(self.current_chat_id)
            if current_chat:
                current_chat["messages"].append({"role": "assistant", "content": cau_tra_loi_day_du})
                self.save_history_data()
                
                if is_first_message and self.ai is not None:
                    threading.Thread(target=self.generate_title_with_ai, args=(self.current_chat_id, cau_hoi, cau_tra_loi_day_du), daemon=True).start()
        except:
            if self.current_streaming_bubble:
                self.current_streaming_bubble.configure(text="[Error]")
        finally:
            if self.ai is not None:
                self.btn_send.configure(state="normal")

    def generate_title_with_ai(self, chat_id, cau_hoi, cau_tra_loi):
        if self.ai is None: return
        prompt_dat_ten = [
            {"role": "system", "content": "Đặt một tiêu đề cực kỳ ngắn gọn (từ 2 đến 5 words) bằng chính ngôn ngữ người dùng đang giao tiếp dựa trên ngữ cảnh được cung cấp. Không dùng dấu ngoặc kép."},
            {"role": "user", "content": f"Q: {cau_hoi}\nA: {cau_tra_loi}"}
        ]
        try:
            ket_qua = self.ai.create_chat_completion(messages=prompt_dat_ten, max_tokens=15, temperature=0.3, stream=False)
            tieu_de_ai = ket_qua['choices'][0]['message']['content'].strip().replace('"', '').replace("'", "")
            
            target_chat = self.get_chat_by_id(chat_id)
            if target_chat and tieu_de_ai:
                target_chat["title"] = tieu_de_ai
                self.save_history_data()
                self.after(0, self.update_sidebar_after_naming, chat_id)
        except:
            pass

    def update_sidebar_after_naming(self, chat_id):
        self.refresh_sidebar()
        if self.current_chat_id == chat_id and chat_id in self.chat_buttons_refs:
            self.chat_buttons_refs[chat_id]["btn"].configure(fg_color="#262626")

if __name__ == "__main__":
    app = ChatApp()
    app.mainloop()