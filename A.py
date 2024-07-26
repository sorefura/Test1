import time
import sys

def download_simulation(total_size, chunk_size):
    downloaded_size = 0
    while downloaded_size < total_size:
        time.sleep(1)  # ダウンロードのシミュレーション
        downloaded_size += chunk_size
        if downloaded_size > total_size:
            downloaded_size = total_size
        progress = f"Downloaded {downloaded_size} of {total_size} bytes ({(downloaded_size / total_size) * 100:.2f}%)"
        print(progress)
        sys.stdout.flush()  # ここでバッファをフラッシュする

if __name__ == "__main__":
    total_size = 1024 * 1024 * 100  # 100MB
    chunk_size = 1024 * 1024 * 10   # 10MB
    download_simulation(total_size, chunk_size)
