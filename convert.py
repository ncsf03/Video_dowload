import yt_dlp
import os
import shutil
import sys
from pathlib import Path
import threading
import customtkinter as ctk
from tkinter import messagebox

cancelado = False

def verificar_ffmpeg():
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    ffmpeg_path = os.path.join(base_path, "ffmpeg", "ffmpeg.exe")
    return ffmpeg_path if os.path.exists(ffmpeg_path) else None


def get_documents_path():
    try:
        return str(Path.home() / "Documents")
    except Exception as e:
        return None

def baixar_youtube(url, formato, status_callback, progress_callback):
    global cancelado
    try:
        documents_path = get_documents_path()
        if not documents_path:
            status_callback("Erro ao localizar a pasta Documentos.")
            return

        output_path = os.path.join(documents_path, 'YouTubeDownloads', formato.upper())
        os.makedirs(output_path, exist_ok=True)

        ffmpeg_path = verificar_ffmpeg()

        if formato == 'mp4' and not ffmpeg_path:
            status_callback("FFmpeg não está instalado.")
            return

        def hook(d):
            if cancelado:
                raise Exception("Download cancelado pelo usuário.")
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded = d.get('downloaded_bytes', 0)
                if total:
                    percent = downloaded / total * 100
                    progress_callback(percent)
                status_callback(f"Baixando: {d.get('_percent_str', '').strip()}")
            elif d['status'] == 'finished':
                status_callback("Download concluído. Convertendo...")

        ydl_opts = {
            'format': 'bestaudio/best' if formato == 'mp3' else 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [hook],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if formato == 'mp3' else [],
            'ffmpeg_location': ffmpeg_path,
            'merge_output_format': 'mp4' if formato == 'mp4' else 'mp3'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            status_callback("Iniciando download...")
            ydl.download([url])

        status_callback(f"Concluído! Arquivo salvo em: {output_path}")
        progress_callback(100.0)
    except Exception as e:
        if str(e) != "Download cancelado pelo usuário.":
            status_callback(f"Erro: {e}")
        else:
            status_callback("Download cancelado.")
        progress_callback(0)

def iniciar_interface():
    global cancelado

    def iniciar_download_thread():
        global cancelado
        cancelado = False
        url = entrada_url.get().strip()
        formato = var_formato.get()

        if not url:
            messagebox.showwarning("Aviso", "Insira uma URL válida.")
            return

        btn_baixar.configure(state="disabled")
        btn_cancelar.configure(state="normal")
        status_var.set("Preparando...")

        def run():
            def atualizar_status(msg):
                app.after(0, lambda: status_var.set(msg))
            def atualizar_progresso(p):
                app.after(0, lambda: progress_bar.set(p / 100))
            baixar_youtube(url, formato, atualizar_status, atualizar_progresso)
            app.after(0, lambda: btn_baixar.configure(state="normal"))
            app.after(0, lambda: btn_cancelar.configure(state="disabled"))

        threading.Thread(target=run, daemon=True).start()

    def cancelar_download():
        global cancelado
        cancelado = True
        status_var.set("Cancelando...")

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    global app
    app = ctk.CTk()
    app.title("YouTube Downloader")
    app.geometry("460x400")
    app.resizable(False, False)

    # Layout moderno
    ctk.CTkLabel(app, text="🎵 YouTube Downloader", font=("Segoe UI", 20, "bold")).pack(pady=(20, 10))
    ctk.CTkLabel(app, text="Cole o link do vídeo:", font=("Segoe UI", 14)).pack(pady=(5, 2))
    entrada_url = ctk.CTkEntry(app, width=400, height=35)
    entrada_url.pack(pady=5)

    ctk.CTkLabel(app, text="Formato de saída:", font=("Segoe UI", 13)).pack(pady=(10, 2))
    var_formato = ctk.StringVar(value="mp3")
    formato_frame = ctk.CTkFrame(app, fg_color="transparent")
    formato_frame.pack()
    ctk.CTkRadioButton(formato_frame, text="MP3", variable=var_formato, value="mp3").grid(row=0, column=0, padx=10)
    ctk.CTkRadioButton(formato_frame, text="MP4", variable=var_formato, value="mp4").grid(row=0, column=1, padx=10)

    progress_bar = ctk.CTkProgressBar(app, width=400)
    progress_bar.set(0)
    progress_bar.pack(pady=15)

    status_var = ctk.StringVar(value="")
    ctk.CTkLabel(app, textvariable=status_var, font=("Segoe UI", 12), wraplength=420).pack(pady=5)

    botoes_frame = ctk.CTkFrame(app, fg_color="transparent")
    botoes_frame.pack(pady=15)

    btn_baixar = ctk.CTkButton(botoes_frame, text="▶️ Baixar", command=iniciar_download_thread)
    btn_baixar.grid(row=0, column=0, padx=10)

    btn_cancelar = ctk.CTkButton(botoes_frame, text="❌ Cancelar", command=cancelar_download, state="disabled")
    btn_cancelar.grid(row=0, column=1, padx=10)

    app.mainloop()

if __name__ == "__main__":
    iniciar_interface()
