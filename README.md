# 本地 AI 助手 - Ollama ChatBot

使用 Ollama 本地模型服務搭建的類似 ChatGPT 的網頁聊天應用。

## 功能特色

### 核心功能
- 支援串流回應，即時顯示 AI 回覆
- 自動載入 Ollama 已安裝的模型
- 支援 Markdown 格式渲染
- 現代化的聊天介面
- 系統提示詞設定與快速範本

### 對話管理
- 新增、切換、刪除對話
- 對話歷史自動儲存至 localStorage
- 對話標題編輯
- 即時切換模型

### 多模態支援
- **圖片上傳** 📷 - 支援視覺模型（如 qwen3-vl）分析圖片
- **語音輸入** 🎤 - 瀏覽器即時語音轉文字（Web Speech API）
- **音檔轉錄** 📁 - 使用 faster-whisper 轉錄音檔為文字

### 訊息編輯
- 編輯最後一則訊息並重新發送
- 編輯時保留原有圖片

## 系統需求

- Node.js 18+
- [Ollama](https://ollama.ai/) 已安裝並運行
- 至少一個已下載的 Ollama 模型

## 安裝 Ollama

```bash
# Linux / macOS
curl -fsSL https://ollama.ai/install.sh | sh

# 下載模型 (例如 qwen2.5:7b)
ollama pull qwen2.5:7b
```

## 專案結構

```
chatbot/
├── whisper-server/   # Faster-Whisper 語音轉錄服務
│   ├── main.py       # FastAPI 服務
│   ├── requirements.txt
│   └── start.sh      # 啟動腳本
├── server/           # 後端 API 服務
│   ├── app.js        # Express 伺服器
│   └── package.json
├── src/              # Vue 前端
│   ├── App.vue       # 主要元件
│   ├── main.ts       # 入口檔案
│   └── vite-env.d.ts
├── public/           # 靜態資源
│   └── favicon.svg
├── index.html        # HTML 模板
├── package.json      # 前端依賴
├── vite.config.ts    # Vite 設定
├── tsconfig.json     # TypeScript 設定
└── README.md
```

## 快速開始

### 1. 安裝依賴

```bash
# 安裝前端依賴
npm install

# 安裝後端依賴
cd server
npm install
cd ..

# 安裝 Whisper 服務依賴（可選，用於音檔轉錄）
cd whisper-server
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 2. 啟動 Ollama 服務

確保 Ollama 正在運行：

```bash
ollama serve
# 或連接遠端 Ollama 伺服器 (預設: 192.168.1.100:11434)
```

### 3. 啟動後端服務

```bash
cd server
npm start
```

後端將在 `http://localhost:3001` 運行。

### 4. 啟動 Whisper 服務（可選）

如需音檔轉錄功能，開啟新的終端：

```bash
cd whisper-server
./start.sh
```

Whisper 服務將在 `http://localhost:8001` 運行。

### 5. 啟動前端開發伺服器

開啟新的終端：

```bash
npm run dev
```

前端將在 `http://localhost:5173` 運行。

### 5. 開始使用

在瀏覽器開啟 `http://localhost:5173`，選擇模型並開始聊天！

## API 端點

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/api/models` | 取得可用模型列表 |
| POST | `/api/chat` | 發送聊天訊息（支援圖片多模態） |
| POST | `/api/transcribe` | 音檔轉文字（轉發到 faster-whisper） |
| GET | `/api/whisper/health` | 檢查 Whisper 服務狀態 |
| GET | `/api/whisper/models` | 取得 Whisper 模型資訊 |

### 聊天 API 請求範例

```json
{
  "model": "qwen3-vl:8b",
  "messages": [
    { 
      "role": "user", 
      "content": "描述這張圖片",
      "images": ["base64編碼的圖片..."]
    }
  ],
  "stream": true
}
```

## 生產環境部署

```bash
# 建置前端
npm run build

# 啟動後端服務
cd server
npm start
```

建置後的檔案會在 `dist/` 目錄，可以使用 nginx 或其他網頁伺服器提供服務。

## 多模態功能說明

### 圖片上傳 📷
點擊輸入框旁的 📷 按鈕上傳圖片，支援的視覺模型包括：
- `qwen3-vl` - Qwen 視覺語言模型（**僅支援圖片和影片，不支援音訊**）
- `llava` - LLaVA 視覺模型
- 其他支援圖片的多模態模型

### 語音輸入 🎤
點擊 🎤 按鈕開始即時語音輸入（使用瀏覽器 Web Speech API）：
- 支援 Chrome、Edge、Safari 等現代瀏覽器
- 預設識別繁體中文
- 無需安裝額外模型
- 語音會即時轉為文字顯示在輸入框

### 音檔轉錄 📁
點擊 📁 按鈕上傳音檔，使用 [faster-whisper](https://github.com/SYSTRAN/faster-whisper) 進行高品質轉錄：
- 支援 MP3、WAV、M4A、FLAC、OGG 等格式
- 自動偵測語言
- 需要啟動 whisper-server 服務（見下方說明）

**啟動 Whisper 服務：**
```bash
cd whisper-server
./start.sh
```

**環境變數設定（可選）：**
| 變數 | 預設值 | 說明 |
|------|--------|------|
| WHISPER_MODEL_SIZE | large-v3 | 模型大小（tiny/base/small/medium/large-v3/turbo） |
| WHISPER_DEVICE | cuda | 運算裝置（cuda/cpu） |
| WHISPER_COMPUTE_TYPE | float16 | 計算類型（float16/int8） |
| WHISPER_PORT | 8001 | 服務埠號 |

> **注意**：Ollama 不支援音訊多模態輸入，因此本專案整合獨立的 faster-whisper 服務處理音檔轉錄。

## 授權

MIT License
