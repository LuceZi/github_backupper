import os
import subprocess
import logging
from datetime import datetime

def setup_logging(log_file="backup.log"):
    """設定日誌紀錄"""
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

def log_message(message):
    """寫入日誌"""
    logging.info(message)
    print(message)  # 同時印在終端

def clone_or_pull_repo(repo_url, target_dir, token=None):
    """
    Clone 或 Pull 專案，並支持私人專案。
    - 如果目標目錄存在，執行 git pull
    - 否則執行 git clone
    - 支持私人專案需要使用 Token
    """
    try:
        # 確保 repo_url 是正確格式，不包含 https://github.com/，例如：LuceZi/repo_name
        if repo_url.startswith("https://github.com/"):
            repo_url = repo_url.replace("https://github.com/", "")

        # 組合 GitHub 存儲庫的完整 URL
        repo_git_url = f"https://{token}:x-oauth-basic@github.com/{repo_url}.git"
        
        if os.path.exists(target_dir):
            # 執行 pull
            log_message(f"更新專案 {repo_url} 到 {target_dir}...")
            result = subprocess.run(
                ["git", "-C", target_dir, "pull"],
                capture_output=True, text=True, env={"GIT_ASKPASS": "echo", "GIT_USERNAME": "token", "GIT_PASSWORD": token}
            )
        else:
            # 執行 clone
            log_message(f"複製專案 {repo_url} 到 {target_dir}...")
            os.makedirs(os.path.dirname(target_dir), exist_ok=True)
            result = subprocess.run(
                ["git", "clone", repo_git_url, target_dir],
                capture_output=True, text=True
            )
        
        if result.returncode == 0:
            log_message(f"成功完成操作：{repo_url}")
        else:
            log_message(f"操作失敗：{repo_url}\n{result.stderr}")
    except Exception as e:
        log_message(f"執行過程中出現異常：{e}")

def main():
    setup_logging()
    repos = [
        {"name": "ExampleRepo1", "url": "LuceZi/win-python-uwu", "path": "backups/ExampleRepo1"},
        {"name": "PrivateRepo", "url": "LuceZi/Raspi-ssd1316-system-monitor", "path": "backups/PrivateRepo"},
    ]

    for repo in repos:
        clone_or_pull_repo(repo["url"], repo["path"])

if __name__ == "__main__":
    main()
