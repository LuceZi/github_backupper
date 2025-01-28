import requests

def fetch_repos(username, token=None):
    if token:
        url = "https://api.github.com/user/repos"
        headers = {"Authorization": f"token {token}"}
    else:
        url = f"https://api.github.com/users/{username}/repos"
        headers = {}

    repositories = []
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for repo in data:
                repositories.append({
                    "name": repo["name"],
                    "private": repo["private"],
                    "url": repo["html_url"]
                })
        
        elif response.status_code == 401:
            print("身份驗證失敗，切換到公開專案模式...")
            return fetch_repos(username, token=None)
        else:
            print(f"無法獲取數據，HTTP 狀態碼：{response.status_code}")
            
    except Exception as e:
        print(f"發生錯誤：{e}")
    
    return repositories

def main():
    username = "LuceZi"  # 你的 GitHub 用戶名
    token =None
    repos = fetch_repos(username, token)
    if repos:
        if token:
            print(f"找到 {len(repos)} 個專案（包含私人專案）：")
        else:
            print(f"找到 {len(repos)} 個公開專案：")
        
        for repo in repos:
            status = "私人" if repo["private"] else "公開"
            print(f"名稱：{repo['name']} - 類型：{status} - URL：{repo['url']}")
    else:
        print("未找到任何專案或發生錯誤。")

if __name__ == "__main__":
    main()
