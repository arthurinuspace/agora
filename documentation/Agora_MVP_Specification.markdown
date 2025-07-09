# Agora - MVP 專案規格書

## 1. 專案概述
- **專案名稱:** Agora  
- **專案目標:** 開發一個整合於 Slack 工作區的應用程式，提供簡單、快速且匿名的投票工具，幫助團隊快速收集意見並進行決策。  
- **目標使用者:** Slack 工作區內的團隊成員。  
- **核心價值:** 匿名性、易用性、即時性、安全性。

## 2. 系統架構
- **後端:** Python 3.9+ 與 FastAPI 框架。  
- **Slack 互動:** 使用 `slack_bolt` SDK 處理 Slack API 事件。  
- **資料庫:** SQLite（檔案名稱：`agora.db`）。  
- **開發環境:** 本機執行 FastAPI，使用 `ngrok` 提供公開 HTTPS URL 以接收 Slack 事件。

## 3. MVP 核心功能

### 3.1. 發起投票
- **觸發方式:** 在 Slack 頻道輸入 `/agora` 指令。  
- **介面:** 彈出對話框（Modal），包含：  
  - **投票問題:** 文字輸入（最多 500 字元）。  
  - **選項:** 2 至 10 個選項。  
  - **投票類型:** 單選或複選（預設單選）。  
- **結果:** 提交後，在頻道中發布帶有問題和選項按鈕的投票訊息。

### 3.2. 進行投票
- **方式:** 點擊投票訊息中的選項按鈕。  
- **匿名性:** 系統不記錄投票者與所選選項的關聯。  
- **複選支援:** 若為複選投票，可選擇多個選項。

### 3.3. 防止重複投票
- **機制:** 記錄哪些使用者已對某投票操作（不記錄選項）。  
- **單選:** 已投票者無法再次投票，提示「您已經投過票了」。  
- **複選:** 可追加或取消選項。  
- **提示方式:** 使用僅使用者可見的 Ephemeral Message。

### 3.4. 即時更新票數
- **機制:** 投票後即時更新訊息，顯示：  
  - 每個選項的票數與百分比。  
  - 總投票人數。

### 3.5. 結束投票
- **方式:** 投票訊息下方有「結束投票」按鈕，僅發起人可點擊。  
- **結果:** 結束後按鈕失效，訊息標註「投票已結束」並顯示最終結果。

## 4. Slack App 設定
- **Slash Commands:**  
  - `/agora` - 發起投票  
  - **Request URL:** `[ngrok URL]/slack/events`  
- **Interactivity:**  
  - **Request URL:** `[ngrok URL]/slack/events`  
- **權限 (Bot Token Scopes):** `commands`, `chat:write`, `chat:write.public`, `users:read`, `channels:read`

## 5. API 端點 (FastAPI)
- **POST /slack/events:** 處理 Slack 事件。  
- **GET /health:** 健康檢查。

## 6. 資料庫結構 (SQLite)
- **`polls` 表:**  
  - `id` (INTEGER, PRIMARY KEY)  
  - `question` (TEXT, NOT NULL)  
  - `team_id` (TEXT, NOT NULL)  
  - `channel_id` (TEXT, NOT NULL)  
  - `creator_id` (TEXT, NOT NULL)  
  - `message_ts` (TEXT, UNIQUE)  
  - `vote_type` (TEXT, DEFAULT 'SINGLE')  
  - `status` (TEXT, DEFAULT 'OPEN')  
  - `created_at` (DATETIME, DEFAULT CURRENT_TIMESTAMP)  

- **`poll_options` 表:**  
  - `id` (INTEGER, PRIMARY KEY)  
  - `poll_id` (INTEGER, FOREIGN KEY)  
  - `option_text` (TEXT, NOT NULL)  
  - `votes` (INTEGER, DEFAULT 0)  

- **`voted_users` 表:**  
  - `id` (INTEGER, PRIMARY KEY)  
  - `poll_id` (INTEGER, FOREIGN KEY)  
  - `user_id` (TEXT, NOT NULL)  
  - `voted_at` (DATETIME, DEFAULT CURRENT_TIMESTAMP)  
  - **UNIQUE (poll_id, user_id)**  

- **`user_votes` 表 (複選):**  
  - `id` (INTEGER, PRIMARY KEY)  
  - `poll_id` (INTEGER, FOREIGN KEY)  
  - `user_id` (TEXT, NOT NULL)  
  - `option_id` (INTEGER, FOREIGN KEY)  
  - `voted_at` (DATETIME, DEFAULT CURRENT_TIMESTAMP)  
  - **UNIQUE (poll_id, user_id, option_id)**  

## 7. 技術棧
- **依賴:** `fastapi`, `uvicorn`, `slack_bolt`, `sqlalchemy`, `python-dotenv`

## 8. 安全性
- **請求驗證:** 驗證 Slack 簽名。  
- **敏感資訊:** 使用 `.env` 管理。