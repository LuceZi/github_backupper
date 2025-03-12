import os
import json
import time
import requests
import logging
from logging.handlers import RotatingFileHandler

from my_package import *

def setup_logging(log_file="backup.log"):
    """設置日誌紀錄，使用滾動日誌"""
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
        self.first_time_setup = False  # 預設為 False
        self.config = self.load_config()  # 載入設定檔
        
        # 如果是第一次建立 config，提醒使用者後退出
        if self.first_time_setup:
            print("🔧 `config.json` 已建立，請手動填寫 GitHub 帳號與 Token，然後重新執行程式！")
            print("⚠️ 預設存放路徑: backups/ (或外接硬碟)")
            exit(0)  # 直接結束程式
        
        # 初始化路徑設定
        self.save_path = self.config['save_path']
        self.github_name = self.config['github_name']
        self.token = self.config['token']
        self.existing_files = self.config['existing_files']

        if not self.save_path:
            self.set_external_drive_path()

    def load_config(self):
        """載入配置文件，若無則建立預設配置"""
        default_config = {
            'save_path': '',
            'github_name': '',
            'token': '',
            'existing_files': []
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # 確保所有必要的鍵都存在
                    for key in default_config:
                        if key not in config:
                            config[key] = default_config[key]
                    return config
            except json.JSONDecodeError:
                print("❌ 設定檔解析錯誤，將重置配置")
        else:
            print("⚠️ `config.json` 不存在，將建立新設定檔...")
            self.first_time_setup = True  # 標記為第一次建立設定檔
        
        # 創建新的設定檔
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=4)
        
        return default_config

    def save_config(self):
        """將配置文件保存回磁碟"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            print("✅ 配置已成功保存")
        except Exception as e:
            print(f"❌ 配置保存失敗: {e}")

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
           
            # **未偵測到外接設備，使用專案目錄下的 backups**
        self.save_path = os.path.join(os.getcwd(), "backups")
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)
        
        # 更新 config
        self.config['save_path'] = self.save_path
        self.save_config()
        
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
    scheduler = Scheduler(config_file)  # 這裡會自動檢查 config，若無則退出
    
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
