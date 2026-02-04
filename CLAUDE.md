# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 開發命令

### 前端（根目錄）

```bash
npm install          # 安裝前端依賴
npm run dev          # 啟動開發伺服器 (localhost:5173)
npm run build        # TypeScript 檢查 + Vite 打包 → dist/
npm run preview      # 預覽打包後的前端
```

### 後端（server/）

```bash
cd server && npm install   # 安裝後端依賴
cd server && npm start     # 生產模式啟動 (localhost:3001)
cd server && npm run dev   # 開發模式（--watch，代碼改動自動重啟）
```

### Whisper 音訊轉錄服務（whisper-server/，可選）

```bash
cd whisper-server && ./start.sh   # 啟動服務 (localhost:8001)
```

開發時需同時啟動前端和後端，前端的 `/api` 請求會由 Vite proxy 轉發至後端。

---

## 架構概攽

這是一個單頁聊天應用，前後端分離運行，後端作為 Ollama 和 Whisper 的代理層。

```
瀏览器 (Vue 3)
  │  開發時 Vite proxy /api → localhost:3001
  ↓
Express 後端 (server/app.js, port 3001)
  ├── POST /api/chat        → Ollama (localhost:11434) — SSE 串流轉發
  ├── GET  /api/models      → Ollama /api/tags
  ├── POST /api/transcribe  → faster-whisper (localhost:8001) — multipart 音檔轉發
  └── GET  /api/whisper/*   → faster-whisper 健康檢查 / 模型資訊

Ollama (本地 AI 推理)
  └── 支援圖片輸入 (base64)，視覺模型如 qwen3-vl

faster-whisper (Python FastAPI，可選)
  └── 音訊轉錄，支援多語言、CUDA 加速
```

### 關鍵架構決策

- **無後端資料庫**：對話數據全部儲存在瀏覽器的 `localStorage`，適用於單使用者本地開發。
- **SSE 串流**：`POST /api/chat` 使用 Server-Sent Events 將 Ollama 的逐字回應實時轉發給前端，而非 WebSocket。
- **Whisper 獨立服務**：Ollama 不支援音訊多模態，因此音訊轉錄由獨立的 Python 服務處理，後端僅做代理轉發。
- **圖片以 base64 傳輸**：透過 JSON body 直接附帶，無需額外的 multipart 處理（僅音檔上傳才用 multipart）。

### 前端結構

前端幾乎所有功能都集中在 `src/App.vue`（約 2800 行）中，使用 Vue 3 Composition API：

- **對話管理**：`conversations` ref 陣列，以 `currentConversationId` 切換，load/save 直接操作 `localStorage`。
- **訊息串流**：用 `fetch` + `ReadableStream` 讀取 SSE，將後端轉發的 Ollama 回應逐塊累積到 `currentResponse`，再更新 UI。
- **圖片上傳**：選擇後轉換為 base64，附帶在訊息的 `images` 陣列中隨聊天請求送出。
- **語音輸入**：直接使用瀏覽器原生 Web Speech API（無需後端），預設語言 `zh-TW`。
- **音訊轉錄**：將音檔以 multipart 表單上傳至 `POST /api/transcribe`，後端再轉發給 Whisper 服務。
- **Markdown 渲染**：使用 `marked` 庫將 AI 回應轉為 HTML。

### 後端結構

`server/app.js` 是單一 Express 應用，功能單一，僅做代理：

- 用 `axios` 連接 Ollama（`responseType: 'stream'`）和 Whisper（帶 `form-data`）。
- 音檔上傳由 `multer` 處理，暫存至 `/tmp/uploads/`，轉發完成後立即清理。
- `WHISPER_API` 可透過環境變數Override，預設 `http://localhost:8001`。

---

## Git Commit 規範

遵循 AngularJS Commit Conventions，所有訊息使用**繁體中文**。

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**：`feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`, `revert`

**Scope**：`frontend`, `backend`, `api`, `ui`, `config`, `deps`, `docs`

**Subject 規則**：繁體中文，不超過 50 字元，動詞開頭（新增、修復、更新、移除、重構），結尾不加句號。

**Body 規則**：繁體中文，說明「為什麼」和「做了什麼」，每行不超過 72 字元，與 Subject 之間空一行。

**Footer 規則**：關聯 Issue 用 `Closes #123` 或 `Fixes #123`；重大變動用 `BREAKING CHANGE: 說明`。

範例：
```
feat(frontend): 新增系統提示詞設定功能

- 新增側邊欄設定面板
- 支援自訂系統提示詞
- 新增預設提示詞範本
- 設定自動儲存至 localStorage
```

```
fix(backend): 修復串流回應中斷問題

當 Ollama 回應時間過長時，連線會意外中斷。
增加 keep-alive 設定以維持連線穩定。

Closes #42
```

---

## 程式碼規範

### 前端 (Vue.js)
- 使用 Composition API (`<script setup>`)
- 使用 TypeScript
- 元件檔案使用 PascalCase 命名
- CSS 使用 scoped 樣式

### 後端 (Express.js)
- 使用 CommonJS 模組（`require` / `module.exports`）
- API 路由以 `/api` 為前綴
- 錯誤回應格式一致：`{ error: string, detail?: string }`

---

## 重要檔案位置

| 檔案 | 說明 |
|------|------|
| `src/App.vue` | 前端主要元件，幾乎所有功能都在此 |
| `src/main.ts` | Vue 應用入口點 |
| `server/app.js` | 後端唯一入口，所有 API 路由均定義於此 |
| `server/package.json` | 後端獨立的依賴管理 |
| `vite.config.ts` | Vite 設定，含開發伺服器 proxy 配置 |
| `whisper-server/main.py` | Whisper 音訊轉錄服務（Python FastAPI） |
| `whisper-server/start.sh` | Whisper 服務啟動腳本（設定 CUDA 環境） |
| `docs/` | 技術文件（架構、API 規格、部署等） |
