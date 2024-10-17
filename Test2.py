import subprocess
import sys
import os

def download_file(jfrog_url, local_path):
    """Jfrog CLIを使用してファイルをダウンロードする関数"""
    try:
        # JFrog CLIを使用してファイルをダウンロード
        result = subprocess.run(
            ['jfrog', 'rt', 'dl', jfrog_url, '--output', local_path],
            capture_output=True,
            text=True
        )

        # コマンドの標準出力とエラー出力を確認
        if result.returncode != 0:
            print(f"Error downloading file: {result.stderr}", flush=True)
            return

        # ダウンロードしたファイルのサイズを取得
        total_size = os.path.getsize(local_path)
        print(total_size)  # ファイルサイズを出力（最初の行）

        # 進行状況の表示
        print("Download completed successfully.")
    except Exception as e:
        print(f"Error during file download: {e}", flush=True)

if __name__ == "__main__":
    # コマンドライン引数からURLとローカルパスを取得
    if len(sys.argv) != 3:
        print("Usage: python DownloadFile.py <URL> <local_path>")
        sys.exit(1)

    jfrog_url = sys.argv[1]
    local_path = sys.argv[2]

    download_file(jfrog_url, local_path)
