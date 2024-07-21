import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import threading

class JFrogDownloader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("JFrog Downloader")
        self.geometry("300x200")

        self.t1_button = tk.Button(self, text="T1-ROM", command=self.open_t1_rom)
        self.t1_button.pack(pady=20)

        self.pre_button = tk.Button(self, text="Pre-ROM", command=self.open_pre_rom)
        self.pre_button.pack(pady=20)

    def open_t1_rom(self):
        self.new_window(T1ROMWindow)

    def open_pre_rom(self):
        self.new_window(PreROMWindow)

    def new_window(self, window_class):
        new_win = tk.Toplevel(self)
        window_class(new_win)

class MasterWindow:
    def __init__(self, master):
        self.master = master
        self.master.geometry("400x600")

        self.radio_var = tk.StringVar(value="A-Pro")

        self.Pro_Label = tk.Label(master, text= "Product :")
        self.Pro_Label.grid(row=0, column=0, padx=(25, 5), pady=(5, 1), sticky='nw')

        self.t1_radio = tk.Radiobutton(master, text="A-Pro", variable=self.radio_var, value="A-Pro", command=self.update_path)
        self.t1_radio.grid(row=1, column=0, padx=(35, 5), pady=1, sticky='nw')

        self.pre_radio = tk.Radiobutton(master, text="B-Pro", variable=self.radio_var, value="B-Pro", command=self.update_path)
        self.pre_radio.grid(row=2, column=0, padx=(35, 5), pady=1, sticky='nw')

        self.cn_Label = tk.Label(master, text= "Common :")
        self.cn_Label.grid(row=0, column=1, padx=(25, 5), pady=(5, 1), sticky='nw')

        self.checkboxes_frame = tk.Frame(master)
        self.checkboxes_frame.grid(row=1, column=1, rowspan=3, pady=1, sticky='wn')

        self.list_Label = tk.Label(master, text= "Ver_List :")
        self.list_Label.grid(row=0, column=2, padx=(35, 5), pady=(5, 1), sticky='nw')

        self.folder_listbox = tk.Listbox(master, selectmode=tk.MULTIPLE)
        self.folder_listbox.grid(row=1, column=2, rowspan=3, padx=(45,20), pady=1, sticky='nwe')

        #self.url_entry = tk.Entry(master, width=50)
        #self.url_entry.grid(row=2, column=0, columnspan=3, pady=5, sticky='nw')

        self.download_button = tk.Button(master, text="Download", command=self.download_files)
        self.download_button.grid(row=3, column=0, columnspan=3, pady=5)

        self.progress = ttk.Progressbar(master, orient="horizontal", length=400, mode="determinate")
        self.progress.grid(row=4, column=0, padx=10, columnspan=3, pady=5)

        # グリッドの列のサイズ調整
        master.grid_rowconfigure(2, weight=1)
        master.grid_columnconfigure(2, weight=1)

        self.check_vars = ["00_A", "01_A", "02_A"]
        self.update_path()

    def update_path(self):
        selected_option = self.radio_var.get()
        self.clear_checkboxes()
        self.folder_listbox.delete(0, tk.END)  # Listboxの初期化

        if selected_option == "A-Pro":
            options = ["00_A", "01_A", "02_A"]
            #self.url_entry.delete(0, tk.END)
            #self.url_entry.insert(0, "http://A-Pro")
        elif selected_option == "B-Pro":
            options = ["00_B", "01_B", "02_B"]
            #self.url_entry.delete(0, tk.END)
            #self.url_entry.insert(0, "http://B-Pro")
        else:
            options = []

        self.create_checkboxes(options)
        # self.fetch_folders()

    def create_checkboxes(self, options):
        self.check_vars = []
        for i, option in enumerate(options):
            var = tk.StringVar(value="")
            checkbox = tk.Checkbutton(self.checkboxes_frame, text=option, variable=var, onvalue=option, offvalue="")
            checkbox.grid(row=i, column=0, pady=(1, 2),padx=(35, 0), sticky='nw')
            self.check_vars.append(var)

    def clear_checkboxes(self):
        for widget in self.checkboxes_frame.winfo_children():
            widget.destroy()

    def fetch_folders(self):
        url = self.url_entry.get()
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            folders = data.get('folder', [])
            for folder in folders:
                self.folder_listbox.insert(tk.END, folder)
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Failed to fetch data: {e}")
        except ValueError:
            messagebox.showerror("Error", "Invalid JSON response")

    def list_files(self):
        # Artifactoryからディレクトリリストを取得する処理
        path = self.path_entry.get()
        # ここでJFrog APIにリクエストを送信してディレクトリリストを取得
        # 仮のリストを追加
        files = ["file1.txt", "file2.txt", "file3.txt"]
        self.file_listbox.delete(0, tk.END)
        for file in files:
            self.file_listbox.insert(tk.END, file)

    def download_files(self):
        selected_files = [self.file_listbox.get(idx) for idx in self.file_listbox.curselection()]
        if not selected_files:
            messagebox.showwarning("Warning", "No files selected.")
            return
        self.progress["value"] = 0
        self.progress["maximum"] = len(selected_files)
        threading.Thread(target=self._download_files_thread, args=(selected_files,)).start()

    def _download_files_thread(self, files):
        for idx, file in enumerate(files):
            self.download_file(file)
            self.progress["value"] = idx + 1

    def download_file(self, file):
        # ファイルのダウンロード処理
        url = f"http://example.com/artifactory/{file}"  # ここに実際のURLを設定
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            save_path = filedialog.asksaveasfilename(initialfile=file)
            if save_path:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
        else:
            messagebox.showerror("Error", f"Failed to download {file}")

class T1ROMWindow(MasterWindow):
    def __init__(self, master):
        super().__init__(master)
        self.master.title("T1-ROM Downloader")

class PreROMWindow(MasterWindow):
    def __init__(self, master):
        super().__init__(master)
        self.master.title("Pre-ROM Downloader")
        # 必要に応じて、ここにPre-ROM固有の処理を追加

if __name__ == "__main__":
    app = JFrogDownloader()
    app.mainloop()
