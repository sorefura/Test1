import tkinter as tk
from tkinter import messagebox, Listbox, Scrollbar, Button, Frame
import paramiko
import logging
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# ロガーの設定
logging.basicConfig(filename='app.log', level=logging.INFO)

class MenuScreen:
    def __init__(self, master):
        self.master = master
        self.master.title("メニュー画面")

        self.menu_frame = Frame(self.master)
        self.menu_frame.pack(pady=20)

        self.download_button = Button(self.menu_frame, text="ダウンロード", command=self.open_downloader)
        self.download_button.pack()

    def open_downloader(self):
        """ダウンロード画面を開く"""
        self.menu_frame.pack_forget()  # メニューを隠す
        JFrogDownloader(self.master, self)  # JFrogDownloaderを呼び出す

    def show(self):
        """メニュー画面を表示"""
        self.menu_frame.pack(pady=20)

class JFrogDownloader:
    def __init__(self, master, menu_screen):
        self.master = master
        self.menu_screen = menu_screen
        
        self.create_downloader()  # ダウンロード画面を作成

        # Script情報
        self.info_script = 'DownloadInfo.py'
        self.dl_script   = 'DownloadFile.py'

        # JFrog情報
        self.JFROG_BASE_URL = 'https://your-jfrog-domain/artifactory/toprepository/main/'
        self.JFROG_API_URL  = 'https://your-jfrog-domain/artifactory/api/storage/'
        self.JFROG_INFO_PATH = os.path.join(os.getcwd(), self.info_script)
        self.JFROG_CURL_PATH = os.path.join(os.getcwd(), self.dl_script)
        self.API_KEY = "your-jfrog-api-key"

        # Linux接続情報
        self.HOST = 'your-linux-host'
        self.PORT = 22
        self.USERNAME = 'your-username'
        self.PASSWORD = 'your-password'
        self.REMOTE_PY_DIR = '/path/to/remote/dir'
        self.REMOTE_DL_DIR = '/path/to/remote/dir/script'

        # 閉じるイベントをバインド
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_downloader(self):
        """ダウンロード画面のGUIを作成する"""
        self.dl_listbox = Listbox(self.master, width=50, selectmode=tk.MULTIPLE)
        self.scrollbar = Scrollbar(self.master)

        self.dl_listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)
        
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.dl_listbox.pack(side=tk.LEFT, fill=tk.BOTH)

        self.download_button = Button(self.master, text="Download", command=self.on_download)
        self.download_button.pack()

        self.end_button = Button(self.master, text="終了", command=self.master.quit, state=tk.DISABLED)
        self.end_button.pack(pady=10)

        self.progress_frames = []

        # ディレクトリを取得してリストボックスに追加
        self.load_directories()

    def exec_ssh(self, command):
        """SSH経由でコマンドを実行する共通関数"""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.HOST, self.PORT, self.USERNAME, self.PASSWORD)

            stdin, stdout, stderr = ssh.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                logging.error(f"Error executing command: {stderr.read().decode()}")
                messagebox.showerror("Error", "Command execution failed.")
                return None

            return stdout

        except paramiko.SSHException as e:
            logging.error(f"SSH connection error: {e}")
            messagebox.showerror("Error", "SSH connection failed.")
            return None
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            messagebox.showerror("Error", "An unexpected error occurred.")
            return None

    def load_directories(self):
        """ディレクトリを取得してリストボックスに追加"""
        directories = self.get_files_in_directory("")  # ルートディレクトリを取得
        for directory in directories:
            self.listbox.insert(tk.END, directory)

    def get_files_in_directory(self, directory):
        """指定されたディレクトリ内のファイルを取得する"""
        try:
            response = self.exec_ssh(f"{self.JFROG_BASE_URL}{directory}")
            if response is None:
                return []

            files = response.json().get('children', [])
            return [f['uri'] for f in files if not f['folder']]
        except Exception as e:
            logging.error(f"Error fetching files: {e}")
            messagebox.showerror("Error", "Could not fetch files.")
            return []

    def download_file(self, file_name, progress_bar, completion_callback):
        """選択したファイルをダウンロード"""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.HOST, self.PORT, self.USERNAME, self.PASSWORD)

            sftp = ssh.open_sftp()
            sftp.put(self.JFROG_INFO_PATH, os.path.join(self.REMOTE_PY_DIR, self.info_script))
            sftp.put(self.JFROG_CURL_PATH, os.path.join(self.REMOTE_PY_DIR, self.dl_script))
            sftp.close()

            command = f"python3 {os.path.join(self.REMOTE_DIR, 'DownloadFile.py')} {self.JFROG_BASE_URL}{file_name} {self.REMOTE_DIR}/downloaded_file_{file_name.split('/')[-1]}"
            stdin, stdout, stderr = ssh.exec_command(command)

            total_size = 0
            downloaded_size = 0

            for line in iter(stdout.readline, ""):
                if line.strip().isdigit():
                    total_size = int(line.strip())
                    progress_bar['maximum'] = total_size
                else:
                    if "Downloaded" in line:
                        downloaded_size += int(line.split()[1])
                        progress_bar['value'] = downloaded_size
                        self.master.update_idletasks()

            exit_status = stdout.channel.recv_exit_status()
            if exit_status == 0 and downloaded_size == total_size:
                logging.info(f"Downloaded {file_name} successfully.")
                messagebox.showinfo("Success", f"Downloaded {file_name} successfully.")
            else:
                logging.error(f"Download incomplete or failed for: {file_name}.")
                messagebox.showerror("Error", "Download incomplete or failed.")
        except Exception as e:
            logging.error(f"Error during file download: {e}")
            messagebox.showerror("Error", "Could not download the file.")
        finally:
            ssh.close()
            completion_callback()

    def on_download(self):
        """ダウンロードボタンの処理"""
        selected = list(self.listbox.curselection())
        if not selected:
            messagebox.showwarning("Warning", "Please select a directory.")
            return

        for frame in self.progress_frames:
            frame.destroy()
        self.progress_frames.clear()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for index in selected:
                file_name = self.listbox.get(index)
                frame = Frame(self.master)
                frame.pack(pady=5)

                progress_bar = tk.Progressbar(frame, length=300)
                progress_bar.pack()

                self.progress_frames.append(frame)

                future = executor.submit(self.download_file, file_name, progress_bar, self.on_download_complete)
                futures.append(future)

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Error in thread: {e}")
                    messagebox.showerror("Error", "An error occurred during download.")

    def on_download_complete(self):
        """すべてのダウンロードが完了した時の処理"""
        if all(progress['value'] == progress['maximum'] for frame in self.progress_frames for progress in frame.winfo_children() if isinstance(progress, tk.Progressbar)):
            self.end_button.config(state=tk.NORMAL)

    def on_close(self):
        """ウィンドウを閉じる処理"""
        self.menu_screen.show()  # メニュー画面を表示する
        self.master.destroy()  # ダウンロード画面を閉じる

# Tkinterの設定
root = tk.Tk()
menu_screen = MenuScreen(root)
root.mainloop()
