# 前端實作說明

## 技術棧

- **Vue 3** - 使用 Composition API (`<script setup>`)
- **TypeScript** - 型別安全
- **Vite** - 快速開發與建置
- **marked** - Markdown 轉 HTML

## 元件結構

目前專案使用單一 `App.vue` 元件，包含以下區塊：

```
App.vue
├── 側邊欄 (Sidebar)
│   ├── 模型選擇
│   ├── 系統提示詞設定
│   ├── 快速範本
│   └── 對話管理
└── 主聊天區域 (Chat Container)
    ├── 標題列
    ├── 訊息區域
    └── 輸入區域
```

## 核心狀態

```typescript
// 模型相關
const selectedModel = ref('deepseek-r1:8b');  // 選擇的模型
const models = ref<any[]>([]);                 // 可用模型列表

// 訊息相關
const messages = ref<Message[]>([]);           // 對話歷史
const userInput = ref('');                     // 使用者輸入
const currentResponse = ref('');               // AI 正在輸出的回應
const isTyping = ref(false);                   // AI 是否正在回應

// UI 相關
const sidebarCollapsed = ref(false);           // 側邊欄是否收合
const messagesContainer = ref<HTMLElement>();  // 訊息容器 DOM 參考

// 系統提示詞
const systemPrompt = ref('');                  // 系統提示詞內容
```

## 訊息介面定義

```typescript
interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
}
```

## 核心功能實作

### 1. 載入可用模型

```typescript
async function loadModels() {
  try {
    const response = await fetch(`${API_BASE}/models`);
    const data = await response.json();
    models.value = data.models || [];
    
    // 如果儲存的模型不在列表中，使用第一個可用模型
    if (models.value.length > 0) {
      const savedModel = localStorage.getItem('selectedModel');
      const modelExists = models.value.some(m => m.name === savedModel);
      if (!modelExists) {
        selectedModel.value = models.value[0].name;
      }
    }
  } catch (error) {
    console.error('載入模型失敗:', error);
  }
}
```

### 2. 發送訊息與處理串流回應

```typescript
async function sendMessage() {
  if (!userInput.value.trim() || isTyping.value) return;

  const userMessage = userInput.value.trim();
  messages.value.push({ role: 'user', content: userMessage });
  userInput.value = '';
  isTyping.value = true;
  currentResponse.value = '';

  try {
    // 構建要發送的訊息，包含系統提示詞
    const messagesToSend: Message[] = [];
    
    // 如果有系統提示詞，加在最前面
    if (systemPrompt.value.trim()) {
      messagesToSend.push({ role: 'system', content: systemPrompt.value.trim() });
    }
    
    // 加入對話歷史
    messagesToSend.push(...messages.value);

    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: selectedModel.value,
        messages: messagesToSend,
        stream: true
      })
    });

    // 處理串流回應
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader!.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n').filter(line => line.trim().startsWith('data:'));
      
      for (const line of lines) {
        try {
          const data = JSON.parse(line.replace('data: ', ''));
          if (data.message?.content) {
            currentResponse.value += data.message.content;
            await scrollToBottom();
          }
        } catch (e) {}
      }
    }

    messages.value.push({ role: 'assistant', content: currentResponse.value });
    currentResponse.value = '';
  } catch (error) {
    console.error('發送訊息失敗:', error);
    messages.value.push({ role: 'assistant', content: '抱歉，發生錯誤，請稍後再試。' });
  } finally {
    isTyping.value = false;
  }
}
```

### 3. Markdown 渲染

```typescript
import { marked } from 'marked';

function formatMarkdown(text: string) {
  return marked(text);
}
```

在模板中使用 `v-html` 指令渲染：

```html
<div class="message-body" v-html="formatMarkdown(msg.content)"></div>
```

### 4. 系統提示詞管理

```typescript
// 儲存系統提示詞
function saveSystemPrompt() {
  localStorage.setItem('systemPrompt', systemPrompt.value);
  alert('系統提示詞已儲存！');
}

// 清除系統提示詞
function clearSystemPrompt() {
  systemPrompt.value = '';
  localStorage.removeItem('systemPrompt');
}

// 套用範本
function applyTemplate(prompt: string) {
  systemPrompt.value = prompt;
}

// 載入儲存的設定
function loadSavedSettings() {
  const savedPrompt = localStorage.getItem('systemPrompt');
  const savedModel = localStorage.getItem('selectedModel');
  
  if (savedPrompt) {
    systemPrompt.value = savedPrompt;
  }
  if (savedModel) {
    selectedModel.value = savedModel;
  }
}
```

### 5. 預設提示詞範本

```typescript
const promptTemplates = [
  { name: '繁體中文', prompt: '請總是使用繁體中文回應所有訊息。' },
  { name: '簡潔回答', prompt: '請簡潔扼要地回答問題，避免冗長的解釋。' },
  { name: '詳細解釋', prompt: '請詳細解釋每個概念，並提供相關範例。' },
  { name: '程式專家', prompt: '你是一位資深程式開發者，請提供專業的程式建議和最佳實踐。使用繁體中文回應。' },
  { name: '友善助手', prompt: '你是一位友善且有耐心的助手，請用輕鬆的語氣回應。使用繁體中文。' },
  { name: '學習導師', prompt: '你是一位耐心的學習導師，請用淺顯易懂的方式解釋概念，適時提問以確認理解。使用繁體中文。' },
];
```

## 樣式設計

### 響應式設計

```css
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100%;
    z-index: 100;
    box-shadow: 2px 0 10px rgba(0,0,0,0.1);
  }
  
  .sidebar.collapsed {
    width: 0;
    padding: 0;
    overflow: hidden;
  }
  
  .chat-container {
    width: 100%;
  }
}
```

### 程式碼區塊樣式

使用 Vue 的 `:deep()` 選擇器穿透 scoped 樣式：

```css
.message-body :deep(pre) {
  background: #f4f4f4;
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
}

.message-body :deep(code) {
  background: #f4f4f4;
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  font-size: 0.9em;
}
```

## Vite 設定

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true
      }
    }
  }
})
```

### Proxy 說明

- 所有 `/api` 開頭的請求會被轉發到後端 `http://localhost:3001`
- `changeOrigin: true` 確保請求的 Host 標頭正確設定
