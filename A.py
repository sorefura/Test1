import tkinter as tk
from tkinter import messagebox, Listbox, Scrollbar, Button, Frame
import requests
import paramiko
import subprocess
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# ロガーの設定
logging.basicConfig(filename='app.log', level=logging.INFO)

# JFrog情報
JFROG_BASE_URL = 'https://your-jfrog-domain/artifactory/toprepository/main/'
JFROG_CURL_PATH = os.path.join(os.getcwd(), 'DownloadFile.py')  # 現在のディレクトリにあるDownloadFile.py

# Linux接続情報
HOST = 'your-linux-host'
PORT = 22
USERNAME = 'your-username'
PASSWORD = 'your-password'
REMOTE_DIR = '/path/to/remote/dir'

def get_files_in_directory(directory):
    """指定されたディレクトリ内のファイルを取得する"""
    try:
        response = requests.get(f"{JFROG_BASE_URL}{directory}")
        response.raise_for_status()
        logging.info(f"{response.status_code()}:{JFROG_BASE_URL}{directory}")
        files = response.json().get('children', [])
        return [f['uri'] for f in files if not f['folder']]
    except Exception as e:
        logging.error(f"Error fetching files: {e}")
        messagebox.showerror("Error", "Could not fetch files.")
        return []

def download_file(file_name, progress_bar, completion_callback):
    """選択したファイルをダウンロード"""
    try:
        # Paramikoで接続
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(HOST, PORT, USERNAME, PASSWORD)

        sftp = ssh.open_sftp()
        sftp.put(JFROG_CURL_PATH, os.path.join(REMOTE_DIR, 'DownloadFile.py'))
        sftp.close()

        # DownloadFile.pyを実行
        command = f"python3 {os.path.join(REMOTE_DIR, 'DownloadFile.py')} {JFROG_BASE_URL}{file_name} {REMOTE_DIR}/downloaded_file_{file_name.split('/')[-1]}"
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        total_size = 0
        downloaded_size = 0

        # 標準出力を逐次読み取る
        for line in iter(process.stdout.readline, ""):
            if line.strip().isdigit():
                total_size = int(line.strip())  # 総ファイルサイズを取得
                progress_bar['maximum'] = total_size  # プログレスバーの最大値を設定
            else:
                # ダウンロードの進捗を更新
                if "Downloaded" in line:
                    downloaded_size += int(line.split()[1])  # ダウンロードされたサイズを取得
                    progress_bar['value'] = downloaded_size  # プログレスバーを更新
                    root.update_idletasks()  # GUIを更新

        process.stdout.close()
        process.wait()

        if process.returncode == 0:
            logging.info(f"Downloaded {file_name} successfully.")
            messagebox.showinfo("Success", f"Downloaded {file_name} successfully.")
        else:
            logging.error(f"Error during file download: {process.stderr.read()}")
            messagebox.showerror("Error", "Could not download the file.")
    except Exception as e:
        logging.error(f"Error during file download: {e}")
        messagebox.showerror("Error", "Could not download the file")
    finally:
        ssh.close()
        completion_callback()  # ダウンロード完了時にコールバックを呼び出す

def on_download():
    """ダウンロードボタンの処理"""
    selected = listbox.curselection()
    if not selected:
        messagebox.showwarning("Warning", "Please select a directory.")
        return

    # 進捗バーをリセット
    for frame in progress_frames:
        frame.destroy()
    progress_frames.clear()

    # スレッドプールを使用してダウンロードを実行
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for index in selected:
            file_name = listbox.get(index)
            frame = Frame(root)
            frame.pack(pady=5)

            progress_bar = tk.Progressbar(frame, length=300)
            progress_bar.pack()

            progress_frames.append(frame)

            future = executor.submit(download_file, file_name, progress_bar, lambda: on_download_complete())
            futures.append(future)

        # 結果を待機
        for future in as_completed(futures):
            try:
                future.result()  # 各スレッドの結果を取得（エラーがあればここで発生）
            except Exception as e:
                logging.error(f"Error in thread: {e}")
                messagebox.showerror("Error", "An error occurred during download.")

def on_download_complete():
    """すべてのダウンロードが完了した時の処理"""
    if all(progress['value'] == progress['maximum'] for frame in progress_frames for progress in frame.winfo_children() if isinstance(progress, tk.Progressbar)):
        end_button.config(state=tk.NORMAL)

# Tkinterの設定
root = tk.Tk()
root.title("JFrog Downloader")

# リストボックスとスクロールバー
listbox = Listbox(root, width=50, selectmode=tk.MULTIPLE)
scrollbar = Scrollbar(root)
listbox.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=listbox.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
listbox.pack(side=tk.LEFT, fill=tk.BOTH)

# ダウンロードボタン
download_button = Button(root, text="Download", command=on_download)
download_button.pack()

# 終了ボタン
end_button = Button(root, text="終了", command=root.quit, state=tk.DISABLED)
end_button.pack(pady=10)

# プログレスバーを格納するリスト
progress_frames = []

# ディレクトリを取得してリストボックスに追加
directories = get_files_in_directory("")  # ルートディレクトリを取得
for directory in directories:
    listbox.insert(tk.END, directory)

# アプリケーションの開始
root.mainloop()
