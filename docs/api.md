# API 文件

## 基本資訊

- **Base URL**: `http://localhost:3001/api`
- **內容類型**: `application/json`

## 端點列表

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/api/models` | 取得可用模型列表 |
| POST | `/api/chat` | 發送聊天訊息 |

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

## 狀態碼

| 狀態碼 | 說明 |
|--------|------|
| 200 | 成功 |
| 500 | 伺服器錯誤（Ollama 服務問題、模型不存在等） |
