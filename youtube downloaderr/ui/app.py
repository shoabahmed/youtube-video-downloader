import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
from core.downloader import YouTubeHandler
from utils.validators import validate_youtube_url

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gemini YouTube Downloader")
        self.geometry("800x600")
        self.resizable(False, False)

        # State
        self.handler = YouTubeHandler()
        self.video_info = None
        self.download_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.selected_itag = None
        
        # Grid layout configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Header
        self.grid_rowconfigure(1, weight=0) # Input
        self.grid_rowconfigure(2, weight=1) # Info Area (flexible)
        self.grid_rowconfigure(3, weight=0) # Controls
        self.grid_rowconfigure(4, weight=0) # Status

        self._create_widgets()

    def _create_widgets(self):
        # --- Header ---
        self.header_frame = ctk.CTkFrame(self, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="YouTube Downloader", font=("Roboto", 24, "bold"))
        self.title_label.pack(pady=15)

        # --- Input Section ---
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=20)
        
        self.url_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Paste YouTube URL here...", height=40, font=("Roboto", 14))
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.fetch_btn = ctk.CTkButton(self.input_frame, text="Fetch Info", command=self.on_fetch_click, height=40, font=("Roboto", 14, "bold"))
        self.fetch_btn.pack(side="right")

        # --- Video Info Section (Initially Hidden/Empty) ---
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent") # Placeholder
        self.info_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        
        self.video_title_label = ctk.CTkLabel(self.info_frame, text="", font=("Roboto", 18, "bold"), wraplength=700)
        self.video_title_label.pack(pady=(10, 5))
        
        self.video_meta_label = ctk.CTkLabel(self.info_frame, text="", font=("Roboto", 12), text_color="gray")
        self.video_meta_label.pack(pady=(0, 20))

        # Options Container
        self.options_frame = ctk.CTkFrame(self.info_frame)
        self.options_frame.pack(fill="x", pady=10)
        self.options_frame.pack_forget() # Hide initially

        # Format Selection
        self.type_var = ctk.StringVar(value="Video (MP4)")
        self.type_label = ctk.CTkLabel(self.options_frame, text="Format:", font=("Roboto", 14))
        self.type_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")
        
        self.type_menu = ctk.CTkOptionMenu(self.options_frame, values=["Video (MP4)", "Audio (MP3)"], command=self.update_resolution_options, variable=self.type_var)
        self.type_menu.grid(row=0, column=1, padx=20, pady=20, sticky="w")

        # Resolution Selection
        self.res_label = ctk.CTkLabel(self.options_frame, text="Quality:", font=("Roboto", 14))
        self.res_label.grid(row=0, column=2, padx=20, pady=20, sticky="w")
        
        self.res_menu = ctk.CTkOptionMenu(self.options_frame, values=[])
        self.res_menu.grid(row=0, column=3, padx=20, pady=20, sticky="w")

        # Path Selection
        self.path_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        self.path_frame.pack(fill="x", pady=10)
        self.path_frame.pack_forget() 

        self.path_label = ctk.CTkLabel(self.path_frame, text=f"Save to: {self.download_path}", text_color="gray")
        self.path_label.pack(side="left", padx=10)
        
        self.path_btn = ctk.CTkButton(self.path_frame, text="Change Folder", width=100, command=self.select_path)
        self.path_btn.pack(side="right", padx=10)

        # --- Controls Section ---
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=20)
        
        self.download_btn = ctk.CTkButton(self.controls_frame, text="Download", command=self.on_download_click, height=50, font=("Roboto", 16, "bold"), state="disabled", fg_color="green", hover_color="darkgreen")
        self.download_btn.pack(fill="x")

        # --- Status Section ---
        self.status_frame = ctk.CTkFrame(self, corner_radius=0)
        self.status_frame.grid(row=4, column=0, sticky="ew")
        
        self.progress_bar = ctk.CTkProgressBar(self.status_frame, height=15)
        self.progress_bar.pack(fill="x", padx=20, pady=(10, 5))
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="Ready", font=("Roboto", 12))
        self.status_label.pack(pady=(0, 10))

    def select_path(self):
        path = filedialog.askdirectory()
        if path:
            self.download_path = path
            self.path_label.configure(text=f"Save to: {self.download_path}")

    def on_fetch_click(self):
        url = self.url_entry.get().strip()
        if not validate_youtube_url(url):
            self.status_label.configure(text="Invalid URL", text_color="red")
            return
        
        self.fetch_btn.configure(state="disabled")
        self.status_label.configure(text="Fetching video metadata...", text_color="white")
        self.progress_bar.set(0)
        
        # Threading
        threading.Thread(target=self._fetch_metadata_thread, args=(url,), daemon=True).start()

    def _fetch_metadata_thread(self, url):
        try:
            self.video_info = self.handler.fetch_metadata(url)
            self.after(0, self._on_fetch_success)
        except Exception as e:
            self.after(0, lambda: self._on_fetch_error(str(e)))

    def _on_fetch_success(self):
        self.fetch_btn.configure(state="normal")
        self.status_label.configure(text="Metadata loaded.", text_color="green")
        
        # Update Info UI
        self.video_title_label.configure(text=self.video_info.title)
        self.video_meta_label.configure(text=f"{self.video_info.author} • {self.video_info.length}s")
        
        self.options_frame.pack(fill="x", pady=10)
        self.path_frame.pack(fill="x", pady=10)
        self.download_btn.configure(state="normal")
        
        self.update_resolution_options()

    def _on_fetch_error(self, error_msg):
        self.fetch_btn.configure(state="normal")
        self.status_label.configure(text=f"Error: {error_msg}", text_color="red")
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
        
        # Parse selection to find itag
        # Format is "Res (Size)" e.g. "720p (12.5 MB)"
        # We can just match the index or search strings
        
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
        
        self.status_label.configure(text="Initializing download...", text_color="white")
        self.progress_bar.set(0)

        threading.Thread(target=self._download_thread, args=(selected_stream['itag'],), daemon=True).start()

    def _download_thread(self, itag):
        try:
            self.handler.download_stream(
                itag, 
                self.download_path, 
                self._update_progress, 
                self._download_complete
            )
            # Success is handled in callback, but we need to reset UI
            self.after(0, self._on_download_success_ui)
        except Exception as e:
            self.after(0, lambda: self._on_download_error(str(e)))

    def _update_progress(self, percentage, downloaded, total):
        # Update UI thread safe
        self.after(0, lambda: self._update_progress_ui(percentage))

    def _update_progress_ui(self, percentage):
        self.progress_bar.set(percentage / 100)
        self.status_label.configure(text=f"Downloading... {percentage:.1f}%")

    def _download_complete(self, file_path):
        pass # Can handle specific post-processing here if needed

    def _on_download_success_ui(self):
        self.status_label.configure(text="Download Completed Successfully!", text_color="green")
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

if __name__ == "__main__":
    app = App()
    app.mainloop()
