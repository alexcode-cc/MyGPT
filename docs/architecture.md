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
                                  │
                                  │ 音檔轉錄
                                  ▼
                        ┌─────────────────┐
                        │                 │
                        │ Faster-Whisper  │
                        │   (Port 8001)   │
                        │                 │
                        └─────────────────┘
                            語音轉文字
```

## 技術選型

### 前端

| 技術 | 版本 | 用途 |
|------|------|------|
| Vue.js | 3.4+ | 前端框架 |
| TypeScript | 5.4+ | 型別檢查 |
| Vite | 5.1+ | 開發伺服器與建置工具 |
| marked | 12.0+ | Markdown 渲染 |
| Web Speech API | - | 瀏覽器即時語音輸入 |

### 後端

| 技術 | 版本 | 用途 |
|------|------|------|
| Node.js | 18+ | 執行環境 |
| Express | 4.18+ | Web 框架 |
| Axios | 1.6+ | HTTP 客戶端 |
| CORS | 2.8+ | 跨域資源共享 |
| Multer | 1.4+ | 檔案上傳處理 |
| form-data | 4.0+ | FormData 轉發 |

### AI 服務

| 技術 | 用途 |
|------|------|
| Ollama | 本地大型語言模型服務 |
| Faster-Whisper | 高效能語音轉文字服務 |

### Faster-Whisper 服務

| 技術 | 版本 | 用途 |
|------|------|------|
| Python | 3.9+ | 執行環境 |
| FastAPI | 0.100+ | Web 框架 |
| faster-whisper | 1.0+ | Whisper 推理引擎 |
| CTranslate2 | - | 高效 Transformer 推理 |
| Uvicorn | 0.23+ | ASGI 伺服器 |

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

### 音檔轉錄流程

```
1. 使用者上傳音檔（📁 按鈕）
        │
        ▼
2. 前端發送 POST /api/transcribe (multipart/form-data)
        │
        ▼
3. Express 後端接收並轉發至 Faster-Whisper 服務
        │
        ▼
4. Faster-Whisper 處理流程：
   ┌──────────────────────────────────────┐
   │  a. 讀取音檔並解碼                    │
   │  b. 使用 Whisper 模型轉錄             │
   │  c. 分析文字中的多語言（Unicode）      │
   │  d. 返回轉錄結果和語言資訊            │
   └──────────────────────────────────────┘
        │
        ▼
5. 前端格式化轉錄結果：
   ┌──────────────────────────────────────┐
   │  [音檔轉錄內容]                       │
   │  檔案名稱：test.mp3                   │
   │  時長：35秒                           │
   │  語言：英語 + 日語                    │
   │  ---                                  │
   │  轉錄文字...                          │
   └──────────────────────────────────────┘
        │
        ▼
6. 使用者可直接發送或編輯後發送給 LLM
```

### 語音輸入方式比較

| 方式 | 按鈕 | 技術 | 處理位置 | 適用場景 |
|------|------|------|----------|----------|
| 即時語音 | 🎤 | Web Speech API | 瀏覽器 | 即時對話、短句輸入 |
| 音檔轉錄 | 📁 | Faster-Whisper | 後端服務 | 音樂歌詞、長音檔、高品質轉錄 |

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
├── whisper-server/          # Faster-Whisper 語音轉錄服務
│   ├── main.py             # FastAPI 伺服器
│   ├── requirements.txt    # Python 依賴
│   └── start.sh            # 啟動腳本（含 CUDA 設定）
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
- `conversations`：對話歷史
- `currentConversationId`：當前對話 ID

優點：
- 無需後端資料庫
- 重新整理頁面後設定仍然保留
- 簡單且足夠用於單人使用場景

### 為什麼使用獨立的 Faster-Whisper 服務？

1. **Ollama 限制**：Ollama 目前不支援音訊多模態輸入（[Issue #6367](https://github.com/ollama/ollama/issues/6367)）
2. **高效能**：Faster-Whisper 使用 CTranslate2 引擎，比原版 Whisper 快 4 倍
3. **GPU 加速**：支援 CUDA，可在 GPU 上高速運算
4. **多語言支援**：自動偵測語言，支援混合語言（如英語+日語歌曲）
5. **可配置性**：可選擇不同大小的模型（tiny 到 large-v3）

### Faster-Whisper 架構

```
┌─────────────────────────────────────────────────────────────┐
│                    Faster-Whisper 服務                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  FastAPI │───▶│  Whisper │───▶│ 多語言   │              │
│  │  接口    │    │  Model   │    │ 偵測     │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│       │               │               │                     │
│       │               ▼               │                     │
│       │         ┌──────────┐          │                     │
│       │         │CTranslate2│          │                     │
│       │         │ (GPU/CPU)│          │                     │
│       │         └──────────┘          │                     │
│       │                               │                     │
│       └───────────────────────────────┘                     │
│                       │                                      │
│                       ▼                                      │
│              ┌────────────────┐                             │
│              │ JSON Response  │                             │
│              │ - text         │                             │
│              │ - languages    │                             │
│              │ - segments     │                             │
│              └────────────────┘                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 可用 Whisper 模型

| 模型 | 參數量 | VRAM | 速度 | 適用場景 |
|------|--------|------|------|----------|
| tiny | 39M | ~1GB | 最快 | 快速測試 |
| base | 74M | ~1GB | 很快 | 基本轉錄 |
| small | 244M | ~2GB | 快 | 一般使用 |
| medium | 769M | ~5GB | 中等 | 較高品質 |
| large-v3 | 1550M | ~10GB | 慢 | 最高品質（預設） |
| turbo | 809M | ~6GB | 較快 | 速度與品質平衡 |
