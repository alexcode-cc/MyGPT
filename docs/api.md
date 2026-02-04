# API 文件

## 基本資訊

- **Base URL**: `http://localhost:3001/api`
- **內容類型**: `application/json`（除音檔上傳外）

## 端點列表

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/api/models` | 取得可用模型列表 |
| POST | `/api/chat` | 發送聊天訊息（支援圖片多模態） |
| POST | `/api/transcribe` | 音檔轉文字（使用 faster-whisper） |
| GET | `/api/whisper/health` | 檢查 Whisper 服務狀態 |
| GET | `/api/whisper/models` | 取得 Whisper 模型資訊 |

---

## GET /api/models

取得 Ollama 已安裝的模型列表。

### 請求

無需請求參數。

### 回應

```json
{
  "models": [
    {
      "name": "deepseek-r1:8b",
      "model": "deepseek-r1:8b",
      "modified_at": "2026-02-04T13:14:38.489460929+08:00",
      "size": 5225376047,
      "digest": "6995872bfe4c521a67b32da386cd21d5c6e819b6e0d62f79f64ec83be99f5763",
      "details": {
        "parent_model": "",
        "format": "gguf",
        "family": "qwen3",
        "families": ["qwen3"],
        "parameter_size": "8.2B",
        "quantization_level": "Q4_K_M"
      }
    },
    {
      "name": "llama3.1:8b",
      "model": "llama3.1:8b",
      "modified_at": "2026-02-02T17:02:33.50819743+08:00",
      "size": 4920753328,
      "digest": "46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e",
      "details": {
        "parent_model": "",
        "format": "gguf",
        "family": "llama",
        "families": ["llama"],
        "parameter_size": "8.0B",
        "quantization_level": "Q4_K_M"
      }
    }
  ]
}
```

### 回應欄位說明

| 欄位 | 類型 | 說明 |
|------|------|------|
| `models` | array | 模型列表 |
| `models[].name` | string | 模型名稱（用於 API 呼叫） |
| `models[].size` | number | 模型檔案大小（bytes） |
| `models[].details.parameter_size` | string | 模型參數量 |
| `models[].details.quantization_level` | string | 量化等級 |

### 錯誤回應

```json
{
  "error": "錯誤訊息"
}
```

---

## POST /api/chat

發送聊天訊息並取得 AI 回應。

### 請求

```json
{
  "model": "deepseek-r1:8b",
  "messages": [
    {
      "role": "system",
      "content": "請總是使用繁體中文回應。"
    },
    {
      "role": "user",
      "content": "你好"
    }
  ],
  "stream": true
}
```

### 請求欄位說明

| 欄位 | 類型 | 必填 | 預設值 | 說明 |
|------|------|------|--------|------|
| `model` | string | 是 | - | 要使用的模型名稱 |
| `messages` | array | 是 | - | 對話訊息陣列 |
| `stream` | boolean | 否 | `true` | 是否使用串流回應 |

### Message 物件

| 欄位 | 類型 | 說明 |
|------|------|------|
| `role` | string | 角色：`system`、`user` 或 `assistant` |
| `content` | string | 訊息內容 |
| `images` | string[] | （選填）base64 編碼的圖片陣列 |

### 圖片多模態範例

```json
{
  "model": "qwen3-vl:8b",
  "messages": [
    {
      "role": "user",
      "content": "請描述這張圖片",
      "images": ["iVBORw0KGgoAAAANSUhEUgAA..."]
    }
  ],
  "stream": true
}
```

### 角色說明

| 角色 | 說明 |
|------|------|
| `system` | 系統提示詞，用於設定 AI 的行為和風格 |
| `user` | 使用者發送的訊息 |
| `assistant` | AI 的回應（用於對話歷史） |

### 串流回應 (stream: true)

回應格式為 Server-Sent Events (SSE)：

```
Content-Type: text/event-stream

data: {"model":"deepseek-r1:8b","message":{"role":"assistant","content":"你"},"done":false}

data: {"model":"deepseek-r1:8b","message":{"role":"assistant","content":"好"},"done":false}

data: {"model":"deepseek-r1:8b","message":{"role":"assistant","content":"！"},"done":false}

data: {"model":"deepseek-r1:8b","message":{"role":"assistant","content":""},"done":true}

```

#### SSE 資料欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| `model` | string | 使用的模型 |
| `message.role` | string | 固定為 `assistant` |
| `message.content` | string | 回應內容片段 |
| `done` | boolean | 是否完成回應 |

### 非串流回應 (stream: false)

```json
{
  "model": "deepseek-r1:8b",
  "created_at": "2026-02-04T06:18:58.342999225Z",
  "message": {
    "role": "assistant",
    "content": "你好！有什麼我可以幫助你的嗎？"
  },
  "done": true,
  "total_duration": 2464190497,
  "load_duration": 1077379074,
  "prompt_eval_count": 3,
  "prompt_eval_duration": 29619124,
  "eval_count": 186,
  "eval_duration": 1325400265
}
```

### 錯誤回應

```json
{
  "error": "錯誤訊息"
}
```

---

## 使用範例

### JavaScript (Fetch API)

#### 取得模型列表

```javascript
const response = await fetch('/api/models');
const data = await response.json();
console.log(data.models);
```

#### 發送聊天訊息（串流）

```javascript
const response = await fetch('/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    model: 'deepseek-r1:8b',
    messages: [
      { role: 'system', content: '請使用繁體中文回應。' },
      { role: 'user', content: '什麼是人工智慧？' }
    ],
    stream: true
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n').filter(line => line.startsWith('data:'));
  
  for (const line of lines) {
    const data = JSON.parse(line.replace('data: ', ''));
    if (data.message?.content) {
      console.log(data.message.content);
    }
  }
}
```

### cURL

#### 取得模型列表

```bash
curl http://localhost:3001/api/models
```

#### 發送聊天訊息

```bash
curl -X POST http://localhost:3001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-r1:8b",
    "messages": [
      {"role": "user", "content": "你好"}
    ],
    "stream": false
  }'
```

---

## POST /api/transcribe

上傳音檔並轉換為文字（使用 faster-whisper）。

### 請求

- **Content-Type**: `multipart/form-data`

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `audio` | file | 是 | 音訊檔案（MP3、WAV、M4A、FLAC、OGG 等） |
| `language` | string | 否 | 語言代碼（如 'zh', 'en', 'ja'），不指定則自動偵測 |

### 回應

```json
{
  "text": "轉錄的完整文字內容",
  "language": "zh",
  "language_probability": 0.987,
  "duration": 125.5,
  "segments": [
    {
      "start": 0.0,
      "end": 3.5,
      "text": "第一段文字"
    }
  ]
}
```

### 錯誤回應

```json
{
  "error": "Whisper 服務未啟動",
  "detail": "請先啟動 whisper-server 服務",
  "suggestion": "cd whisper-server && ./start.sh"
}
```

### cURL 範例

```bash
curl -X POST http://localhost:3001/api/transcribe \
  -F "audio=@recording.mp3"
```

---

## GET /api/whisper/health

檢查 faster-whisper 服務狀態。

### 回應

```json
{
  "available": true,
  "status": "healthy",
  "model_loaded": true
}
```

---

## GET /api/whisper/models

取得 Whisper 可用模型資訊。

### 回應

```json
{
  "available_models": [
    {"name": "tiny", "parameters": "39M", "vram": "~1GB"},
    {"name": "large-v3", "parameters": "1550M", "vram": "~10GB"}
  ],
  "current_model": "large-v3",
  "device": "cuda",
  "compute_type": "float16"
}
```

---

## 狀態碼

| 狀態碼 | 說明 |
|--------|------|
| 200 | 成功 |
| 400 | 請求錯誤（如未提供音檔） |
| 500 | 伺服器錯誤（Ollama 服務問題、模型不存在等） |
| 503 | 服務不可用（Whisper 服務未啟動） |

---

## 音訊支援說明

Ollama 不支援音訊多模態輸入（[Issue #6367](https://github.com/ollama/ollama/issues/6367)），
因此本專案整合獨立的 [faster-whisper](https://github.com/SYSTRAN/faster-whisper) 服務處理音檔轉錄。

語音輸入的兩種方式：

| 功能 | 按鈕 | 技術 | 說明 |
|------|------|------|------|
| 即時語音 | 🎤 | Web Speech API | 瀏覽器原生，無需後端 |
| 音檔轉錄 | 📁 | faster-whisper | 高品質，支援多種格式 |
