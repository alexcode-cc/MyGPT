# 後端實作說明

## 技術棧

- **Express.js** - Web 框架
- **Axios** - HTTP 客戶端（用於與 Ollama 通訊）
- **CORS** - 跨域資源共享中間件
- **Multer** - 檔案上傳處理
- **form-data** - FormData 處理

## 伺服器設定

```javascript
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const multer = require('multer');
const fs = require('fs');
const path = require('path');
const FormData = require('form-data');

const app = express();
app.use(cors());
app.use(express.json({ limit: '50mb' })); // 支援大型圖片

const OLLAMA_API = 'http://localhost:11434/api';

// 檔案上傳設定
const upload = multer({ 
  dest: '/tmp/uploads/',
  limits: { fileSize: 25 * 1024 * 1024 } // 25MB
});

const PORT = 3001;
const HOST = '0.0.0.0';
app.listen(PORT, HOST, () => {
  console.log(`Server running on http://${HOST}:${PORT}`);
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

處理音檔上傳並使用 Ollama 的語音模型進行轉錄。

```javascript
app.post('/api/transcribe', upload.single('audio'), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: '未提供音訊檔案' });
  }

  const filePath = req.file.path;
  const whisperModel = req.body.model || 'whisper';

  try {
    // 讀取音訊檔案並轉為 base64
    const audioBuffer = fs.readFileSync(filePath);
    const audioBase64 = audioBuffer.toString('base64');

    // 嘗試使用 whisper 模型
    const response = await axios.post(`${OLLAMA_API}/generate`, {
      model: whisperModel,
      prompt: '請將這段音訊轉錄為文字。',
      images: [audioBase64],
      stream: false
    }, { timeout: 120000 });

    fs.unlinkSync(filePath); // 清理暫存檔案
    res.json({ text: response.data.response || '' });
  } catch (error) {
    // 如果 whisper 不可用，嘗試 qwen2-audio
    // ...
  }
});
```

### 音訊轉錄說明

由於 Ollama 目前不直接支援音訊多模態輸入（[Issue #6367](https://github.com/ollama/ollama/issues/6367)），
本專案採用與 [Open WebUI](https://github.com/open-webui/open-webui) 相同的策略：

1. 使用者上傳音檔
2. 後端使用 STT 模型（如 whisper、qwen2-audio）將音訊轉為文字
3. 將轉換後的文字返回前端

### 支援的音訊模型

| 模型 | 安裝指令 | 說明 |
|------|----------|------|
| whisper | `ollama pull whisper` | OpenAI Whisper 語音識別 |
| qwen2-audio | `ollama pull qwen2-audio` | Qwen 音訊模型 |

## 4. 音訊模型檢查 API (GET /api/audio-models)

檢查本地 Ollama 是否安裝了音訊模型。

```javascript
app.get('/api/audio-models', async (req, res) => {
  try {
    const response = await axios.get(`${OLLAMA_API}/tags`);
    const models = response.data.models || [];
    
    const audioModels = models.filter(m => {
      const name = m.name.toLowerCase();
      return name.includes('whisper') || 
             name.includes('audio') ||
             name.includes('qwen2-audio');
    });
    
    res.json({ 
      available: audioModels.length > 0,
      models: audioModels.map(m => m.name)
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
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
