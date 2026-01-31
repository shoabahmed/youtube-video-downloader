import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import urllib.request
from PIL import Image, ImageTk
import io
from core.downloader import DownloaderHandler
from utils.validators import validate_url

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")  # Changed to green to match the button in ref

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Any Video Downloader")
        self.geometry("850x450")
        self.resizable(False, False)

        # State
        self.handler = DownloaderHandler()
        self.video_info = None
        self.download_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.thumbnail_image = None
        
        # Main Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._create_widgets()

    def _create_widgets(self):
        # Main Container (Card-like)
        self.main_container = ctk.CTkFrame(self, corner_radius=15)
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        # --- Header ---
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="YouTube Downloader", font=("Roboto", 16, "bold"), text_color="gray")
        self.title_label.pack(side="left")
        
        # (Optional) Settings Icon placeholder
        # self.settings_btn = ctk.CTkButton(self.header_frame, text="⚙", width=30, height=30, fg_color="transparent", text_color="gray")
        # self.settings_btn.pack(side="right")

        # --- Input Section ---
        self.input_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        self.url_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Paste YouTube URL here...", height=40, font=("Roboto", 13))
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.fetch_btn = ctk.CTkButton(self.input_frame, text="Fetch Info", command=self.on_fetch_click, height=40, font=("Roboto", 13, "bold"), fg_color="#333", hover_color="#444")
        self.fetch_btn.pack(side="right")

        # --- Video Info Section ---
        self.info_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.info_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        self.info_frame.grid_columnconfigure(1, weight=1) # Text expands

        # Thumbnail (Placeholder initially)
        self.thumb_label = ctk.CTkLabel(self.info_frame, text="", width=160, height=90, fg_color="#222", corner_radius=8)
        self.thumb_label.grid(row=0, column=0, rowspan=2, padx=(0, 15))

        # Title & Meta
        self.video_title_label = ctk.CTkLabel(self.info_frame, text="", font=("Roboto", 15, "bold"), anchor="w", justify="left")
        self.video_title_label.grid(row=0, column=1, sticky="w", pady=(0, 5))
        
        self.video_meta_label = ctk.CTkLabel(self.info_frame, text="", font=("Roboto", 12), text_color="gray", anchor="w")
        self.video_meta_label.grid(row=1, column=1, sticky="nw")

        # --- Options Section (Row) ---
        self.options_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.options_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=10)
        
        self.type_var = ctk.StringVar(value="Video (MP4)")
        self.type_menu = ctk.CTkOptionMenu(self.options_frame, values=["Video (MP4)", "Audio (MP3)"], command=self.update_resolution_options, variable=self.type_var, width=140)
        self.type_menu.pack(side="left", padx=(0, 10))

        self.res_menu = ctk.CTkOptionMenu(self.options_frame, values=[], width=140)
        self.res_menu.pack(side="left", padx=(0, 10))
        
        self.path_btn = ctk.CTkButton(self.options_frame, text="Change Folder", width=120, command=self.select_path, fg_color="#333", hover_color="#444")
        self.path_btn.pack(side="left")

        # --- Controls Section ---
        self.download_btn = ctk.CTkButton(self.main_container, text="Download", command=self.on_download_click, height=45, font=("Roboto", 16, "bold"), state="disabled", fg_color="#2E7D32", hover_color="#1B5E20") # Green
        self.download_btn.grid(row=4, column=0, sticky="ew", padx=20, pady=10)

        # --- Status Section ---
        self.status_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.status_frame.grid(row=5, column=0, sticky="ew", padx=20, pady=(5, 15))
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="Idle", font=("Roboto", 11), text_color="gray")
        self.status_label.pack(side="left")
        
        self.progress_bar = ctk.CTkProgressBar(self.status_frame, height=6, progress_color="#2E7D32")
        self.progress_bar.pack(side="right", fill="x", expand=True, padx=(15, 0))
        self.progress_bar.set(0)


    def select_path(self):
        path = filedialog.askdirectory()
        if path:
            self.download_path = path
            # self.path_label.configure(text=f"Save to: {self.download_path}") # Removed explicit label, could add tooltip or log

    def on_fetch_click(self):
        url = self.url_entry.get().strip()
        if not validate_url(url):
            self.status_label.configure(text="Invalid URL", text_color="red")
            return
        
        self.fetch_btn.configure(state="disabled")
        self.status_label.configure(text="Fetching video metadata...", text_color="white")
        self.progress_bar.set(0)
        self.video_title_label.configure(text="Loading...")
        self.video_meta_label.configure(text="")
        self.thumb_label.configure(image=None, text="...")
        
        # Threading
        threading.Thread(target=self._fetch_metadata_thread, args=(url,), daemon=True).start()

    def _fetch_metadata_thread(self, url):
        try:
            self.video_info = self.handler.fetch_metadata(url)
            
            # Fetch Thumbnail
            if self.video_info.thumbnail_url:
                try:
                    with urllib.request.urlopen(self.video_info.thumbnail_url) as u:
                        raw_data = u.read()
                    
                    image = Image.open(io.BytesIO(raw_data))
                    # Resize to fit 160x90
                    image = image.resize((160, 90), Image.Resampling.LANCZOS)
                    self.thumbnail_image = ImageTk.PhotoImage(image)
                except Exception as e:
                    print(f"Thumbnail error: {e}")
                    self.thumbnail_image = None
            
            self.after(0, self._on_fetch_success)
        except Exception as e:
            self.after(0, lambda: self._on_fetch_error(str(e)))

    def _on_fetch_success(self):
        self.fetch_btn.configure(state="normal")
        self.status_label.configure(text="Ready to download", text_color="gray")
        
        # Update Info UI
        self.video_title_label.configure(text=self.video_info.title)
        self.video_meta_label.configure(text=f"{self.video_info.author} • {self.video_info.length}s")
        
        if self.thumbnail_image:
            self.thumb_label.configure(image=self.thumbnail_image, text="")
        else:
            self.thumb_label.configure(text="No Image")

        self.download_btn.configure(state="normal")
        self.update_resolution_options()

    def _on_fetch_error(self, error_msg):
        self.fetch_btn.configure(state="normal")
        self.status_label.configure(text=f"Error: {error_msg}", text_color="red")
        self.video_title_label.configure(text="Error")
        messagebox.showerror("Error", error_msg)

    def update_resolution_options(self, _=None):
        mode = self.type_var.get()
        values = []
        if mode == "Video (MP4)":
            streams = self.video_info.streams_mp4
            values = [f"{s['resolution']} ({s['filesize']})" for s in streams]
        else:
            streams = self.video_info.streams_mp3
            values = [f"{s['resolution']} ({s['filesize']})" for s in streams]
        
        if not values:
            values = ["No streams available"]
            self.download_btn.configure(state="disabled")
        else:
            self.download_btn.configure(state="normal")

        self.res_menu.configure(values=values)
        self.res_menu.set(values[0])

    def on_download_click(self):
        mode = self.type_var.get()
        selection = self.res_menu.get()
        
        selected_stream = None
        streams = self.video_info.streams_mp4 if mode == "Video (MP4)" else self.video_info.streams_mp3
        
        for s in streams:
            if f"{s['resolution']} ({s['filesize']})" == selection:
                selected_stream = s
                break
        
        if not selected_stream:
            return

        self.download_btn.configure(state="disabled")
        self.url_entry.configure(state="disabled")
        self.type_menu.configure(state="disabled")
        self.res_menu.configure(state="disabled")
        self.path_btn.configure(state="disabled")
        self.fetch_btn.configure(state="disabled")
        
        self.status_label.configure(text="Initializing download...", text_color="white")
        self.progress_bar.set(0)

        is_audio = (mode == "Audio (MP3)")
        threading.Thread(target=self._download_thread, args=(selected_stream['itag'], is_audio), daemon=True).start()

    def _download_thread(self, itag, is_audio):
        try:
            self.handler.download_stream(
                itag, 
                self.download_path, 
                self._update_progress, 
                self._download_complete,
                is_audio=is_audio
            )
            self.after(0, self._on_download_success_ui)
        except Exception as e:
            self.after(0, lambda: self._on_download_error(str(e)))

    def _update_progress(self, percentage, downloaded, total):
        self.after(0, lambda: self._update_progress_ui(percentage))

    def _update_progress_ui(self, percentage):
        self.progress_bar.set(percentage / 100)
        self.status_label.configure(text=f"Downloading... {percentage:.1f}%")

    def _download_complete(self, file_path):
        pass

    def _on_download_success_ui(self):
        self.status_label.configure(text="Download Completed!", text_color="green")
        self.progress_bar.set(1)
        self._reset_ui_state()
        messagebox.showinfo("Success", "Download Completed!")

    def _on_download_error(self, error_msg):
        self.status_label.configure(text="Download Failed", text_color="red")
        self._reset_ui_state()
        messagebox.showerror("Download Error", error_msg)

    def _reset_ui_state(self):
        self.download_btn.configure(state="normal")
        self.url_entry.configure(state="normal")
        self.type_menu.configure(state="normal")
        self.res_menu.configure(state="normal")
        self.path_btn.configure(state="normal")
        self.fetch_btn.configure(state="normal")

if __name__ == "__main__":
    app = App()
    app.mainloop()