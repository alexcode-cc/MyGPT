# 本地 AI 助手 - 技術文件

本專案是一個使用 Ollama 本地大型語言模型服務，搭建類似 ChatGPT 的網頁聊天應用程式。

## 目錄

- [專案架構](./architecture.md) - 系統架構與技術選型
- [前端實作](./frontend.md) - Vue.js 前端詳細說明
- [後端實作](./backend.md) - Express.js 後端 API 說明
- [API 文件](./api.md) - API 端點規格
- [Faster-Whisper 音檔轉錄](./faster-whisper.md) - 語音轉文字服務說明
- [部署指南](./deployment.md) - 部署與設定說明

## 快速開始

```bash
# 安裝依賴
npm install
cd server && npm install && cd ..

# 安裝 Whisper 服務依賴（可選，音檔轉錄功能）
cd whisper-server && uv venv && source .venv/bin/activate && uv pip install -r requirements.txt && cd ..

# 啟動後端
cd server && npm start

# 啟動 Whisper 服務（新終端，可選）
cd whisper-server && ./start.sh

# 啟動前端（新終端）
npm run dev
```

開啟瀏覽器訪問 `http://localhost:5173`
