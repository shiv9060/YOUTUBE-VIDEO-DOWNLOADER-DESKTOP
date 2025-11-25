
"""
YouTube Video Downloader - GUI (Tkinter) + pytube


Requirements:
- Python 3.8+
- pytube
- pydub (for mp3 conversion)
- ffmpeg installed and on PATH (for pydub)
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pytube import YouTube
from pydub import AudioSegment

def check_ffmpeg():
    from shutil import which
    return which("ffmpeg") is not None

class YouTubeDownloaderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Video Downloader - Shivam Kumar")
        self.geometry("560x300")
        self.resizable(False, False)

        tk.Label(self, text="YouTube URL:").pack(anchor="w", padx=10, pady=(10,0))
        self.url_var = tk.StringVar()
        tk.Entry(self, textvariable=self.url_var, width=75).pack(padx=10)

        frame = tk.Frame(self)
        frame.pack(padx=10, pady=8, fill="x")
        tk.Label(frame, text="Resolution:").grid(row=0, column=0, sticky="w")
        self.res_var = tk.StringVar(value="highest")
        self.res_combo = ttk.Combobox(frame, textvariable=self.res_var, values=["highest", "1080p", "720p", "480p", "360p", "audio"], width=20, state="readonly")
        self.res_combo.grid(row=0, column=1, padx=6)

        tk.Label(frame, text="Format:").grid(row=0, column=2, sticky="w", padx=(12,0))
        self.format_var = tk.StringVar(value="mp4")
        ttk.Combobox(frame, textvariable=self.format_var, values=["mp4", "mp3"], width=10, state="readonly").grid(row=0, column=3, padx=6)

        tk.Label(self, text="Save to:").pack(anchor="w", padx=10)
        out_frame = tk.Frame(self)
        out_frame.pack(fill="x", padx=10)
        self.output_var = tk.StringVar(value=os.path.expanduser("~"))
        tk.Entry(out_frame, textvariable=self.output_var, width=60).pack(side="left")
        tk.Button(out_frame, text="Browse", command=self.browse_folder).pack(side="left", padx=6)

        self.download_btn = tk.Button(self, text="Download", command=self.start_download_thread, width=15)
        self.download_btn.pack(pady=10)

        self.progress = ttk.Progressbar(self, orient="horizontal", length=480, mode="determinate")
        self.progress.pack(padx=10)

        self.status_label = tk.Label(self, text="")
        self.status_label.pack(padx=10, pady=(6,0))

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.output_var.get())
        if folder:
            self.output_var.set(folder)

    def start_download_thread(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Input required", "Please paste a YouTube video URL.")
            return
        self.download_btn.config(state="disabled")
        self.progress['value'] = 0
        self.status_label.config(text="Starting...")
        t = threading.Thread(target=self.download_video, args=(url,))
        t.start()

    def download_video(self, url):
        try:
            yt = YouTube(url, on_progress_callback=self.on_progress)
        except Exception as e:
            self._done_error(f"Failed to fetch video: {e}")
            return

        fmt = self.format_var.get()
        res = self.res_var.get()
        out_dir = self.output_var.get()

        try:
            if fmt == "mp4":
                if res == "audio":
                    stream = yt.streams.filter(only_audio=True).first()
                elif res == "highest":
                    stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                else:
                    stream = yt.streams.filter(res=res, progressive=True, file_extension='mp4').first()
                if not stream:
                    self._done_error("Requested stream/resolution not available.")
                    return
                self.status_label.config(text="Downloading video...")
                out_path = stream.download(output_path=out_dir)
                self._done_success(f"Downloaded: {os.path.basename(out_path)}")

            elif fmt == "mp3":
                if not check_ffmpeg():
                    self._done_error("ffmpeg not found. Install ffmpeg to enable MP3 conversion.")
                    return
                stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
                if not stream:
                    self._done_error("Audio stream not available.")
                    return
                self.status_label.config(text="Downloading audio...")
                temp_path = stream.download(output_path=out_dir)
                base, _ = os.path.splitext(temp_path)
                mp3_path = base + ".mp3"
                self.status_label.config(text="Converting to MP3...")
                AudioSegment.from_file(temp_path).export(mp3_path, format="mp3")
                try:
                    os.remove(temp_path)
                except:
                    pass
                self._done_success(f"Downloaded: {os.path.basename(mp3_path)}")
        except Exception as e:
            self._done_error(f"Error: {e}")

    def on_progress(self, stream, chunk, bytes_remaining):
        total = stream.filesize
        downloaded = total - bytes_remaining
        percent = int(downloaded / total * 100)
        self.progress['value'] = percent

    def _done_success(self, msg):
        self.progress['value'] = 100
        self.status_label.config(text=msg)
        self.download_btn.config(state="normal")
        messagebox.showinfo("Success", msg)

    def _done_error(self, msg):
        self.status_label.config(text=msg)
        self.download_btn.config(state="normal")
        messagebox.showerror("Error", msg)


if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()
