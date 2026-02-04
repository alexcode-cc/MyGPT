# 部署指南

## 系統需求

- **Node.js**: 18.0 或更高版本
- **npm**: 9.0 或更高版本
- **Ollama**: 已安裝並至少有一個模型

## 開發環境設定

### 1. 安裝 Ollama

```bash
# Linux / macOS
curl -fsSL https://ollama.ai/install.sh | sh

# 驗證安裝
ollama --version
```

### 2. 下載模型

```bash
# 下載推薦的模型
ollama pull deepseek-r1:8b

# 或其他模型
ollama pull llama3.1:8b
ollama pull qwen2.5:7b
```

### 3. 啟動 Ollama 服務

```bash
ollama serve
```

預設會在 `http://localhost:11434` 提供服務。

### 4. 安裝專案依賴

```bash
# 前端依賴
cd chatbot
npm install

# 後端依賴
cd server
npm install
```

### 5. 啟動服務

**終端 1 - 啟動後端：**
```bash
cd chatbot/server
npm start
```

**終端 2 - 啟動前端：**
```bash
cd chatbot
npm run dev
```

### 6. 開啟瀏覽器

訪問 `http://localhost:5173`

---

## 生產環境部署

### 方案 1: 簡單部署

#### 1. 建置前端

```bash
cd chatbot
npm run build
```

建置結果會在 `dist/` 目錄。

#### 2. 使用 Express 提供靜態檔案

修改 `server/app.js`：

```javascript
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json());

// 提供前端靜態檔案
app.use(express.static(path.join(__dirname, '../dist')));

// ... API 路由 ...

// SPA fallback
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../dist/index.html'));
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on port ${PORT}`);
});
```

#### 3. 啟動服務

```bash
cd server
npm start
```

現在只需要一個服務，訪問 `http://your-server:3001` 即可。

---

### 方案 2: 使用 Nginx 反向代理

#### Nginx 設定

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端靜態檔案
    location / {
        root /path/to/chatbot/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        
        # SSE 支援
        proxy_set_header Cache-Control 'no-cache';
        proxy_buffering off;
        proxy_read_timeout 86400;
    }
}
```

---

### 方案 3: 使用 Docker

#### Dockerfile

```dockerfile
# 建置階段
FROM node:18-alpine AS builder

WORKDIR /app

# 複製並安裝前端依賴
COPY package*.json ./
RUN npm ci

# 複製前端原始碼並建置
COPY . .
RUN npm run build

# 執行階段
FROM node:18-alpine

WORKDIR /app

# 複製後端檔案
COPY server/package*.json ./
RUN npm ci --production

COPY server/ ./
COPY --from=builder /app/dist ./dist

# 暴露埠號
EXPOSE 3001

# 啟動服務
CMD ["node", "app.js"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  chatbot:
    build: .
    ports:
      - "3001:3001"
    environment:
      - OLLAMA_API=http://host.docker.internal:11434/api
    restart: unless-stopped
```

#### 建置與執行

```bash
docker-compose up -d
```

---

## 環境變數

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `PORT` | `3001` | 後端服務埠號 |
| `OLLAMA_API` | `http://localhost:11434/api` | Ollama API 端點 |

### 使用環境變數

修改 `server/app.js`：

```javascript
const OLLAMA_API = process.env.OLLAMA_API || 'http://localhost:11434/api';
const PORT = process.env.PORT || 3001;
```

啟動時設定：

```bash
OLLAMA_API=http://192.168.1.100:11434/api PORT=8080 npm start
```

---

## 遠端 Ollama 服務

如果 Ollama 運行在其他機器上：

### 1. 設定 Ollama 監聽所有介面

在 Ollama 伺服器上：

```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

### 2. 修改後端設定

```javascript
const OLLAMA_API = 'http://192.168.1.100:11434/api';
```

或使用環境變數：

```bash
OLLAMA_API=http://192.168.1.100:11434/api npm start
```

---

## 安全性建議

### 生產環境檢查清單

- [ ] 設定 CORS 只允許特定來源
- [ ] 使用 HTTPS
- [ ] 設定防火牆規則
- [ ] 限制 API 請求頻率
- [ ] 不要暴露 Ollama 服務到公網

### CORS 限制範例

```javascript
app.use(cors({
  origin: ['https://your-domain.com'],
  methods: ['GET', 'POST'],
  allowedHeaders: ['Content-Type']
}));
```

### 請求頻率限制

```javascript
const rateLimit = require('express-rate-limit');

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 分鐘
  max: 100 // 最多 100 個請求
});

app.use('/api/', limiter);
```

---

## 常見問題

### Ollama 連線失敗

**症狀**: API 回傳 500 錯誤

**解決方案**:
1. 確認 Ollama 服務正在運行：`ollama list`
2. 確認 Ollama API 可訪問：`curl http://localhost:11434/api/tags`
3. 檢查防火牆設定

### 串流回應不工作

**症狀**: AI 回應一次全部顯示，沒有逐字效果

**解決方案**:
1. 確認 Nginx 設定有 `proxy_buffering off;`
2. 確認請求中 `stream: true`

### 模型載入緩慢

**症狀**: 第一次對話回應很慢

**說明**: 這是正常的，Ollama 需要將模型載入記憶體。後續對話會快很多。

**建議**: 使用較小的模型（如 7B、8B）以加快載入速度。
