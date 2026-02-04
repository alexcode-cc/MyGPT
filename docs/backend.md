# 後端實作說明

## 技術棧

- **Express.js** - Web 框架
- **Axios** - HTTP 客戶端（用於與 Ollama 和 Whisper 服務通訊）
- **CORS** - 跨域資源共享中間件
- **Multer** - 檔案上傳處理
- **form-data** - FormData 處理（轉發音檔到 Whisper 服務）

## 伺服器設定

```javascript
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const multer = require('multer');
const FormData = require('form-data');
const fs = require('fs');

const app = express();
app.use(cors());
app.use(express.json({ limit: '50mb' })); // 支援大型圖片

const OLLAMA_API = 'http://localhost:11434/api';
const WHISPER_API = process.env.WHISPER_API || 'http://localhost:8001';

// 檔案上傳設定
const upload = multer({ 
  dest: '/tmp/uploads/',
  limits: { fileSize: 50 * 1024 * 1024 } // 50MB
});

const PORT = 3001;
const HOST = '0.0.0.0';
app.listen(PORT, HOST, () => {
  console.log(`Server running on http://${HOST}:${PORT}`);
  console.log(`Whisper API: ${WHISPER_API}`);
});
```

### 設定說明

| 設定 | 值 | 說明 |
|------|-----|------|
| `OLLAMA_API` | `http://localhost:11434/api` | Ollama 服務的 API 端點 |
| `PORT` | `3001` | 後端服務監聽的埠號 |
| `HOST` | `0.0.0.0` | 監聽所有網路介面，允許外部連線 |

## API 端點實作

### 1. 聊天 API (POST /api/chat)

處理聊天請求，支援串流和非串流兩種模式。

```javascript
app.post('/api/chat', async (req, res) => {
  const { model, messages, stream = true } = req.body;
  
  try {
    if (stream) {
      // 串流回應
      res.setHeader('Content-Type', 'text/event-stream');
      res.setHeader('Cache-Control', 'no-cache');
      res.setHeader('Connection', 'keep-alive');

      const response = await axios.post(
        `${OLLAMA_API}/chat`,
        { model, messages, stream: true },
        { responseType: 'stream' }
      );

      response.data.on('data', (chunk) => {
        const lines = chunk.toString().split('\n').filter(line => line.trim());
        lines.forEach(line => {
          try {
            const data = JSON.parse(line);
            res.write(`data: ${JSON.stringify(data)}\n\n`);
          } catch (e) {}
        });
      });

      response.data.on('end', () => res.end());
    } else {
      // 非串流回應
      const response = await axios.post(`${OLLAMA_API}/chat`, {
        model,
        messages,
        stream: false
      });
      res.json(response.data);
    }
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

#### 串流處理流程

1. **設定回應標頭**
   - `Content-Type: text/event-stream` - 告知瀏覽器這是 SSE 串流
   - `Cache-Control: no-cache` - 禁止快取
   - `Connection: keep-alive` - 保持連線

2. **轉發請求至 Ollama**
   - 使用 Axios 的 `responseType: 'stream'` 取得串流回應

3. **處理串流資料**
   - 監聽 `data` 事件接收資料片段
   - 將 Ollama 的 JSON 格式轉換為 SSE 格式 (`data: {...}\n\n`)

4. **結束連線**
   - 監聽 `end` 事件，呼叫 `res.end()` 結束回應

### 2. 模型列表 API (GET /api/models)

取得 Ollama 已安裝的模型列表。

```javascript
app.get('/api/models', async (req, res) => {
  try {
    const response = await axios.get(`${OLLAMA_API}/tags`);
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

## Ollama API 介接

### Ollama API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/tags` | GET | 取得已安裝的模型列表 |
| `/api/chat` | POST | 聊天對話 |

### 聊天請求格式

```json
{
  "model": "deepseek-r1:8b",
  "messages": [
    { "role": "system", "content": "系統提示詞" },
    { "role": "user", "content": "使用者訊息" },
    { "role": "assistant", "content": "AI 回應" }
  ],
  "stream": true
}
```

### 串流回應格式

Ollama 的串流回應是以換行分隔的 JSON 物件：

```json
{"model":"deepseek-r1:8b","message":{"role":"assistant","content":"你"},"done":false}
{"model":"deepseek-r1:8b","message":{"role":"assistant","content":"好"},"done":false}
{"model":"deepseek-r1:8b","message":{"role":"assistant","content":"！"},"done":false}
{"model":"deepseek-r1:8b","message":{"role":"assistant","content":""},"done":true}
```

經過後端轉換後變成 SSE 格式：

```
data: {"model":"deepseek-r1:8b","message":{"role":"assistant","content":"你"},"done":false}

data: {"model":"deepseek-r1:8b","message":{"role":"assistant","content":"好"},"done":false}

data: {"model":"deepseek-r1:8b","message":{"role":"assistant","content":"！"},"done":false}

data: {"model":"deepseek-r1:8b","message":{"role":"assistant","content":""},"done":true}

```

## 錯誤處理

```javascript
catch (error) {
  res.status(500).json({ error: error.message });
}
```

當發生錯誤時，回傳 HTTP 500 狀態碼和錯誤訊息。

常見錯誤情況：
- Ollama 服務未啟動
- 指定的模型不存在
- 網路連線問題

## 中間件

### CORS

```javascript
app.use(cors());
```

允許所有來源的跨域請求。在生產環境中，應該限制允許的來源：

```javascript
app.use(cors({
  origin: 'https://your-domain.com'
}));
```

### JSON 解析

```javascript
app.use(express.json());
```

自動解析請求 body 中的 JSON 資料。

## 3. 音檔轉錄 API (POST /api/transcribe)

將音檔轉發到 faster-whisper 服務進行轉錄。

```javascript
app.post('/api/transcribe', upload.single('audio'), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: '未提供音訊檔案' });
  }

  const filePath = req.file.path;
  const originalName = req.file.originalname;

  try {
    // 建立 FormData 轉發到 Whisper 服務
    const formData = new FormData();
    formData.append('audio', fs.createReadStream(filePath), {
      filename: originalName,
      contentType: req.file.mimetype
    });
    formData.append('task', 'transcribe');

    const response = await axios.post(`${WHISPER_API}/transcribe`, formData, {
      headers: { ...formData.getHeaders() },
      timeout: 300000 // 5 分鐘超時
    });

    fs.unlinkSync(filePath); // 清理暫存檔案
    res.json(response.data);
  } catch (error) {
    if (fs.existsSync(filePath)) fs.unlinkSync(filePath);
    
    if (error.code === 'ECONNREFUSED') {
      return res.status(503).json({ 
        error: 'Whisper 服務未啟動',
        suggestion: 'cd whisper-server && ./start.sh'
      });
    }
    res.status(500).json({ error: error.message });
  }
});
```

## 4. Whisper 服務狀態檢查

```javascript
app.get('/api/whisper/health', async (req, res) => {
  try {
    const response = await axios.get(`${WHISPER_API}/health`, { timeout: 5000 });
    res.json({ available: true, ...response.data });
  } catch (error) {
    res.json({ available: false, error: error.message });
  }
});
```

## 相依套件

```json
{
  "dependencies": {
    "axios": "^1.6.7",
    "cors": "^2.8.5",
    "express": "^4.18.2",
    "form-data": "^4.0.0",
    "multer": "^1.4.5-lts.1"
  }
}
```

---

## Faster-Whisper 服務

### 簡介

本專案整合獨立的 [faster-whisper](https://github.com/SYSTRAN/faster-whisper) 服務處理音檔轉錄，
因為 Ollama 不支援音訊多模態輸入（[Issue #6367](https://github.com/ollama/ollama/issues/6367)）。

### 架構

```
瀏覽器 → Node.js (3001) → Python faster-whisper (8001)
              ↓
          Ollama (11434)
```

### 服務設定

位於 `whisper-server/main.py`，使用 FastAPI 框架。

**環境變數：**

| 變數 | 預設值 | 說明 |
|------|--------|------|
| WHISPER_MODEL_SIZE | large-v3 | 模型大小 |
| WHISPER_DEVICE | cuda | 運算裝置 |
| WHISPER_COMPUTE_TYPE | float16 | 計算類型 |
| WHISPER_PORT | 8001 | 服務埠號 |

### 可用模型

| 模型 | 參數量 | VRAM |
|------|--------|------|
| tiny | 39M | ~1GB |
| base | 74M | ~1GB |
| small | 244M | ~2GB |
| medium | 769M | ~5GB |
| large-v3 | 1550M | ~10GB |
| turbo | 809M | ~6GB |

### 啟動服務

```bash
cd whisper-server
./start.sh
```
