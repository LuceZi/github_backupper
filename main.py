import os
import json
import time
import requests
import logging
from logging.handlers import RotatingFileHandler

from my_package import *

def setup_logging(log_file="backup_log.txt"):
    """設置日誌紀錄，使用滾動日誌，最多 20MB（4 個 5MB 檔案）"""
    handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[handler],
    )

class Scheduler:
    def __init__(self, config_file):
        self.config_file = config_file
        # 讀取現有配置
        self.config = self.load_config()
        self.save_path = self.config['save_path']
        self.github_name = self.config['github_name']
        self.token = self.config['token']
        self.existing_files = self.config['existing_files']

        if not self.save_path:
            self.set_external_drive_path()

    def load_config(self):
        """載入配置文件"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            # 如果配置文件不存在，初始化一個預設配置
            return {
                'save_path': '',
                'github_name': '',
                'token': '',
                'existing_files': []
            }
        
    def save_config(self):
        """將配置文件保存回磁碟"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def set_external_drive_path(self):
        """設置外接設備路徑"""
        # 假設我們需要檢查 media 和 mnt 下的設備
        potential_paths = ['/media/Raspi', '/mnt']
        for path in potential_paths:
            if os.path.exists(path):
                # 找到第一個掛載的外接設備
                for item in os.listdir(path):
                    device_path = os.path.join(path, item)
                    if os.path.isdir(device_path):
                        # 如果目標目錄是資料夾，設為存儲路徑
                        self.save_path = device_path
                        # 確保該設備下存在 github 資料夾
                        github_folder = os.path.join(self.save_path, 'github')
                        if not os.path.exists(github_folder):
                            os.makedirs(github_folder)
                        self.save_path = github_folder
                        self.config['save_path'] = self.save_path
                        # 保存配置
                        self.save_config()
                        print(f"已設置儲存路徑: {self.save_path}")
                        return
        print("沒有發現外接設備，請插入外接硬碟。")

    def fetch_github_repos(self):
        """使用 GitHub API 獲取指定使用者的專案列表"""
        repos = github_catcher.fetch_repos(self.github_name, self.token)
        return repos

    def clone_or_pull_repos(self, repos):
        """根據專案列表來進行 clone 或 pull 操作"""
        if repos is None or len(repos) == 0:
            log_message("沒有找到任何專案或 repos 列表為空。")
            return
        
        for repo in repos:
            repo_name = repo['name']
            repo_url = repo['url']
            repo_dir = os.path.join(self.save_path, repo_name)
            github_backupper.clone_or_pull_repo(repo_url, repo_dir, self.token)
            if repo_name not in self.existing_files:
                self.existing_files.append(repo_name)

        # 每次操作完成後更新配置文件
        self.config['existing_files'] = self.existing_files
        self.save_config()  # 保存更新過的配置文件
        
    def run(self):
        """執行 Scheduler 任務：檢查路徑、獲取專案、下載/更新專案"""
        log_message("開始定期檢查與下載 GitHub 專案...")
        self.load_config()  # 檢查並創建存檔路徑
        repos = self.fetch_github_repos()  # 獲取 GitHub 專案列表
        self.clone_or_pull_repos(repos)  # 克隆或拉取專案
        

def main():
    config_file = "config.json"
    scheduler = Scheduler(config_file)
    
    setup_logging()
    logging.info("日誌初始化完成")
    scheduler.run()  # 執行主要任務
    print("一次備份完成")

def startup():
    try:
        main()
    except Exception as e:
        print(f"QAQ: {e}")
        
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    finally:
        print("Progress end~~")

if __name__ == "__main__":
    startup()
