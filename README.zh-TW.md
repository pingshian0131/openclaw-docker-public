# OpenClaw Docker

繁體中文 | [English](README.md)

使用 Docker Compose 運行多個 [OpenClaw](https://github.com/anthropics/claude-code) gateway 環境，內建 **Cron Dashboard** 管理自動化排程任務。

## 架構

```
docker-compose.yml
├── openclaw-work        Gateway（port 18791-18792）
├── openclaw-personal    Gateway（port 18793-18794）
├── cli-work             互動式 CLI
├── cli-personal         互動式 CLI
└── cron-dashboard       Flask 網頁管理介面（port 18799）
```

| 服務 | 說明 | Port |
|------|------|------|
| `openclaw-work` | 工作環境 Gateway | 18791, 18792 |
| `openclaw-personal` | 個人環境 Gateway | 18793, 18794 |
| `cli-work` | 工作環境 CLI（互動式） | — |
| `cli-personal` | 個人環境 CLI（互動式） | — |
| `cron-dashboard` | 排程任務管理面板 | 18799 |

## 前置需求

- **Docker** 和 **Docker Compose**（v2）
- **OpenClaw base image** — 需在本機建置為 `openclaw:local`。請依照 [OpenClaw 建置說明](https://github.com/anthropics/claude-code) 建立此映像檔。
- **Claude Code 認證檔** 位於 `~/.claude/.credentials.json`

## 快速開始

```bash
# 1. Clone 此 repo
git clone https://github.com/anthropics/openclaw-docker.git
cd openclaw-docker

# 2. 複製並編輯環境變數檔
cp .env.example .env
# 編輯 .env — 填入你的 gateway token 和 dashboard 密碼

# 3. 建置並啟動所有服務
docker compose up -d --build

# 4.（選擇性）匯入範例排程任務
docker compose exec cron-dashboard python seed.py
```

Cron Dashboard 現在可以透過 **http://localhost:18799** 存取。

## 設定

### 環境變數（`.env`）

| 變數 | 說明 |
|------|------|
| `OPENCLAW_WORK_TOKEN` | 工作環境 Gateway 認證 token |
| `OPENCLAW_PERSONAL_TOKEN` | 個人環境 Gateway 認證 token |
| `OPENCLAW_IMAGE` | Base image 名稱（預設 `openclaw:local`） |
| `CRON_DASHBOARD_PASSWORD` | Dashboard 登入密碼 |
| `CRON_DASHBOARD_SECRET_KEY` | Flask session 加密金鑰 |

### Volume Mounts

每個 gateway 會將你主機上的目錄掛載到容器中：

| 服務 | 主機路徑 | 容器路徑 | 用途 |
|------|----------|----------|------|
| `openclaw-work` | `~/work` | `/home/node/work` | 工作專案 |
| `openclaw-personal` | `~/projects` | `/home/node/projects` | 個人專案 |
| 共用 | `~/.openclaw-*` | `/home/node/.openclaw` | OpenClaw 設定 |
| 共用 | `~/.claude/.credentials.json` | `/home/node/.claude/.credentials.json` | Claude 認證（唯讀） |

編輯 `docker-compose.yml` 來掛載你自己的目錄，例如：

```yaml
volumes:
  - ~/.openclaw-work:/home/node/.openclaw
  - ~/.claude/.credentials.json:/home/node/.claude/.credentials.json:ro
  - ~/my-company-repo:/home/node/my-company-repo    # <-- 加入你的目錄
```

## 自訂設定

### 加裝 obsidian-cli

如果你的 skill 需要與 [Obsidian](https://obsidian.md/) vault 互動，取消 `Dockerfile.openclaw` 中 `obsidian-cli` 區段的註解即可安裝 [obsidian-cli](https://github.com/Yakitrak/obsidian-cli)，用於建立和管理筆記。

### 加裝 Python 套件

如果你的 Claude Code skill 需要 Python 依賴套件，請編輯 `Dockerfile.openclaw` — 裡面有註解說明如何安裝 pip 和套件。

### 更改 Port

修改 `docker-compose.yml` 中的 `ports` 對應。左邊是主機 port，右邊是容器 port（右邊保持 `18789`/`18790` 不變）。

### 只用單一 Gateway

如果只需要一個 gateway，移除 `docker-compose.yml` 中的 `openclaw-personal` 和 `cli-personal` 服務即可。

## Cron Dashboard

以 Flask + APScheduler 打造的網頁排程管理工具。

**功能：**
- 透過 cron 表達式建立、編輯、刪除排程任務
- 手動觸發任何任務
- 即時 cron 表達式驗證器
- 執行紀錄含 stdout/stderr 擷取
- 簡易密碼認證

**預設範例任務：**
- System Health Check（每 30 分鐘）
- Docker Cleanup（每週）
- Database Backup（每日，預設停用）

你可以透過 `http://localhost:18799` 的網頁介面新增自己的任務。

## 常用指令

```bash
# 啟動所有服務
docker compose up -d

# Dockerfile 有更動時重建
docker compose up -d --build

# 查看 log
docker compose logs -f openclaw-work
docker compose logs -f cron-dashboard

# 進入容器 shell
docker exec -it $(docker compose ps -q openclaw-work) sh

# 停止所有服務
docker compose down
```

## 授權

[MIT](LICENSE)
