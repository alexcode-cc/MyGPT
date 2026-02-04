# 本地 AI 助手 - Ollama ChatBot

使用 Ollama 本地模型服務搭建的類似 ChatGPT 的網頁聊天應用。

## 功能特色

- 支援串流回應，即時顯示 AI 回覆
- 自動載入 Ollama 已安裝的模型
- 支援 Markdown 格式渲染
- 現代化的聊天介面

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

### 4. 啟動前端開發伺服器

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
| POST | `/api/chat` | 發送聊天訊息 |

### 聊天 API 請求範例

```json
{
  "model": "qwen2.5:7b",
  "messages": [
    { "role": "user", "content": "你好！" }
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

## 授權

MIT License
