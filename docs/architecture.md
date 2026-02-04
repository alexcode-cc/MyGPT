# 系統架構

## 架構概覽

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   Vue.js 前端   │────▶│  Express 後端   │────▶│  Ollama 服務    │
│   (Port 5173)   │     │   (Port 3001)   │     │  (Port 11434)   │
│                 │◀────│                 │◀────│                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
      瀏覽器                  API 閘道              本地 LLM
```

## 技術選型

### 前端

| 技術 | 版本 | 用途 |
|------|------|------|
| Vue.js | 3.4+ | 前端框架 |
| TypeScript | 5.4+ | 型別檢查 |
| Vite | 5.1+ | 開發伺服器與建置工具 |
| marked | 12.0+ | Markdown 渲染 |

### 後端

| 技術 | 版本 | 用途 |
|------|------|------|
| Node.js | 18+ | 執行環境 |
| Express | 4.18+ | Web 框架 |
| Axios | 1.6+ | HTTP 客戶端 |
| CORS | 2.8+ | 跨域資源共享 |

### AI 服務

| 技術 | 用途 |
|------|------|
| Ollama | 本地大型語言模型服務 |

## 資料流程

### 聊天請求流程

```
1. 使用者輸入訊息
        │
        ▼
2. Vue 前端發送 POST /api/chat
        │
        ▼
3. Vite Proxy 轉發至 Express 後端
        │
        ▼
4. Express 轉發至 Ollama API
        │
        ▼
5. Ollama 處理並串流回應
        │
        ▼
6. Express 將串流轉換為 SSE 格式
        │
        ▼
7. 前端即時顯示回應內容
```

### 系統提示詞處理流程

```
1. 使用者設定系統提示詞
        │
        ▼
2. 儲存至 localStorage
        │
        ▼
3. 發送訊息時，系統提示詞加入訊息陣列最前面
        │
        ▼
4. 完整訊息格式：
   [
     { role: "system", content: "系統提示詞" },
     { role: "user", content: "使用者訊息1" },
     { role: "assistant", content: "AI 回應1" },
     { role: "user", content: "使用者訊息2" },
     ...
   ]
```

## 專案結構

```
chatbot/
├── docs/                    # 技術文件
│   ├── README.md
│   ├── architecture.md
│   ├── frontend.md
│   ├── backend.md
│   ├── api.md
│   └── deployment.md
├── server/                  # 後端 API 服務
│   ├── app.js              # Express 伺服器
│   └── package.json        # 後端依賴
├── src/                     # Vue 前端
│   ├── App.vue             # 主要元件
│   ├── main.ts             # 入口檔案
│   └── vite-env.d.ts       # TypeScript 型別定義
├── public/                  # 靜態資源
│   └── favicon.svg
├── index.html               # HTML 模板
├── package.json             # 前端依賴
├── vite.config.ts           # Vite 設定
├── tsconfig.json            # TypeScript 設定
├── tsconfig.node.json       # Node TypeScript 設定
├── .gitignore
└── README.md
```

## 設計考量

### 為什麼使用 Proxy？

開發環境中，前端運行在 `localhost:5173`，後端運行在 `localhost:3001`。使用 Vite 的 proxy 功能可以：

1. 避免跨域問題
2. 簡化前端 API 呼叫路徑
3. 模擬生產環境的部署結構

### 為什麼使用 Server-Sent Events (SSE)？

1. **即時性**：使用者可以看到 AI 正在「思考」和「輸入」
2. **使用者體驗**：避免長時間等待完整回應
3. **相容性**：SSE 比 WebSocket 更簡單，且瀏覽器原生支援

### 本地儲存策略

使用 `localStorage` 儲存：
- `systemPrompt`：系統提示詞
- `selectedModel`：選擇的模型

優點：
- 無需後端資料庫
- 重新整理頁面後設定仍然保留
- 簡單且足夠用於單人使用場景
