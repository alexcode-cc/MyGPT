<!-- App.vue -->
<template>
  <div class="app-container">
    <!-- 側邊欄 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <h2 v-if="!sidebarCollapsed">設定</h2>
        <button class="toggle-btn" @click="sidebarCollapsed = !sidebarCollapsed">
          {{ sidebarCollapsed ? '▶' : '◀' }}
        </button>
      </div>
      
      <div class="sidebar-content" v-if="!sidebarCollapsed">
        <!-- 模型選擇 -->
        <div class="setting-group">
          <label>選擇模型</label>
          <select v-model="selectedModel">
            <option v-for="model in models" :key="model.name" :value="model.name">
              {{ model.name }}
            </option>
          </select>
        </div>

        <!-- 系統提示詞 -->
        <div class="setting-group">
          <label>系統提示詞</label>
          <textarea
            v-model="systemPrompt"
            placeholder="輸入系統提示詞，例如：總是使用繁體中文回應"
            rows="6"
          ></textarea>
          <div class="prompt-actions">
            <button class="btn-secondary" @click="saveSystemPrompt">儲存</button>
            <button class="btn-secondary" @click="clearSystemPrompt">清除</button>
          </div>
        </div>

        <!-- 預設提示詞範本 -->
        <div class="setting-group">
          <label>快速範本</label>
          <div class="template-list">
            <button 
              v-for="template in promptTemplates" 
              :key="template.name"
              class="template-btn"
              @click="applyTemplate(template.prompt)"
            >
              {{ template.name }}
            </button>
          </div>
        </div>

        <!-- 對話管理 -->
        <div class="setting-group">
          <label>對話管理</label>
          <button class="btn-danger" @click="clearChat">清除對話</button>
        </div>
      </div>
    </aside>

    <!-- 主聊天區域 -->
    <main class="chat-container">
      <div class="header">
        <h1>本地 AI 助手</h1>
        <div class="header-info">
          <span class="model-badge" v-if="selectedModel">{{ selectedModel }}</span>
          <span class="system-prompt-indicator" v-if="systemPrompt" title="系統提示詞已啟用">
            📝 系統提示詞已設定
          </span>
        </div>
      </div>

      <div class="messages" ref="messagesContainer">
        <!-- 歡迎訊息 -->
        <div v-if="messages.length === 0" class="welcome-message">
          <h2>歡迎使用本地 AI 助手</h2>
          <p>選擇模型並開始對話，或在左側設定系統提示詞來自訂 AI 的行為。</p>
          <div class="quick-prompts">
            <button @click="userInput = '你好，請介紹一下自己'">👋 打個招呼</button>
            <button @click="userInput = '請用繁體中文解釋什麼是人工智慧'">🤖 什麼是 AI</button>
            <button @click="userInput = '請幫我寫一個簡單的程式範例'">💻 程式範例</button>
          </div>
        </div>

        <div 
          v-for="(msg, idx) in messages" 
          :key="idx"
          :class="['message', msg.role]"
        >
          <div class="avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
          <div class="content">
            <div class="message-header">
              <span class="role-label">{{ msg.role === 'user' ? '你' : 'AI' }}</span>
            </div>
            <div class="message-body" v-html="formatMarkdown(msg.content)"></div>
          </div>
        </div>
        
        <div v-if="isTyping" class="message assistant typing">
          <div class="avatar">🤖</div>
          <div class="content">
            <div class="message-header">
              <span class="role-label">AI</span>
              <span class="typing-indicator">正在輸入...</span>
            </div>
            <div class="message-body">{{ currentResponse || '思考中...' }}</div>
          </div>
        </div>
      </div>

      <div class="input-area">
        <textarea
          v-model="userInput"
          @keydown.enter.exact.prevent="sendMessage"
          placeholder="輸入訊息... (Enter 發送, Shift+Enter 換行)"
          :disabled="isTyping"
        />
        <button @click="sendMessage" :disabled="isTyping || !userInput.trim()">
          發送
        </button>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue';
import { marked } from 'marked';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

const API_BASE = '/api';
const selectedModel = ref('deepseek-r1:8b');
const models = ref<any[]>([]);
const messages = ref<Message[]>([]);
const userInput = ref('');
const isTyping = ref(false);
const currentResponse = ref('');
const messagesContainer = ref<HTMLElement>();
const sidebarCollapsed = ref(false);

// 系統提示詞
const systemPrompt = ref('');

// 預設提示詞範本
const promptTemplates = [
  { name: '繁體中文', prompt: '請總是使用繁體中文回應所有訊息。' },
  { name: '簡潔回答', prompt: '請簡潔扼要地回答問題，避免冗長的解釋。' },
  { name: '詳細解釋', prompt: '請詳細解釋每個概念，並提供相關範例。' },
  { name: '程式專家', prompt: '你是一位資深程式開發者，請提供專業的程式建議和最佳實踐。使用繁體中文回應。' },
  { name: '友善助手', prompt: '你是一位友善且有耐心的助手，請用輕鬆的語氣回應。使用繁體中文。' },
  { name: '學習導師', prompt: '你是一位耐心的學習導師，請用淺顯易懂的方式解釋概念，適時提問以確認理解。使用繁體中文。' },
];

onMounted(async () => {
  await loadModels();
  loadSavedSettings();
});

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

// 監聽模型變更並儲存
watch(selectedModel, (newModel) => {
  localStorage.setItem('selectedModel', newModel);
});

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

function formatMarkdown(text: string) {
  return marked(text);
}

async function scrollToBottom() {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
}

// 系統提示詞相關功能
function saveSystemPrompt() {
  localStorage.setItem('systemPrompt', systemPrompt.value);
  alert('系統提示詞已儲存！');
}

function clearSystemPrompt() {
  systemPrompt.value = '';
  localStorage.removeItem('systemPrompt');
}

function applyTemplate(prompt: string) {
  systemPrompt.value = prompt;
}

function clearChat() {
  if (confirm('確定要清除所有對話嗎？')) {
    messages.value = [];
  }
}
</script>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  background: #f5f5f5;
}

/* 側邊欄樣式 */
.sidebar {
  width: 300px;
  background: white;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
}

.sidebar.collapsed {
  width: 50px;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e0e0e0;
}

.sidebar-header h2 {
  margin: 0;
  font-size: 1.2rem;
}

.toggle-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  padding: 0.5rem;
  color: #666;
}

.toggle-btn:hover {
  color: #007bff;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.setting-group {
  margin-bottom: 1.5rem;
}

.setting-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #333;
}

.setting-group select,
.setting-group textarea {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: inherit;
  font-size: 0.9rem;
}

.setting-group textarea {
  resize: vertical;
  min-height: 100px;
}

.prompt-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.btn-secondary {
  flex: 1;
  padding: 0.5rem;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
}

.btn-secondary:hover {
  background: #5a6268;
}

.btn-danger {
  width: 100%;
  padding: 0.5rem;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-danger:hover {
  background: #c82333;
}

.template-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.template-btn {
  padding: 0.4rem 0.8rem;
  background: #e9ecef;
  border: 1px solid #dee2e6;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s;
}

.template-btn:hover {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

/* 主聊天區域 */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-width: 1000px;
  margin: 0 auto;
  background: #f5f5f5;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: white;
  border-bottom: 1px solid #e0e0e0;
}

.header h1 {
  margin: 0;
  font-size: 1.5rem;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.model-badge {
  background: #e9ecef;
  padding: 0.3rem 0.8rem;
  border-radius: 20px;
  font-size: 0.85rem;
  color: #495057;
}

.system-prompt-indicator {
  font-size: 0.85rem;
  color: #28a745;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

/* 歡迎訊息 */
.welcome-message {
  text-align: center;
  padding: 3rem;
  color: #666;
}

.welcome-message h2 {
  color: #333;
  margin-bottom: 1rem;
}

.quick-prompts {
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-top: 2rem;
  flex-wrap: wrap;
}

.quick-prompts button {
  padding: 0.5rem 1rem;
  background: white;
  border: 1px solid #ddd;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-prompts button:hover {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.message {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.message.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}

.content {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  max-width: 70%;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.message-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.role-label {
  font-weight: 600;
  font-size: 0.85rem;
  color: #666;
}

.typing-indicator {
  font-size: 0.8rem;
  color: #999;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.message-body {
  line-height: 1.6;
}

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

.message-body :deep(pre code) {
  background: none;
  padding: 0;
}

.message.user .content {
  background: #007bff;
  color: white;
}

.message.user .role-label {
  color: rgba(255,255,255,0.8);
}

.input-area {
  display: flex;
  gap: 1rem;
  padding: 1rem 2rem;
  background: white;
  border-top: 1px solid #e0e0e0;
}

textarea {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: none;
  font-family: inherit;
  min-height: 60px;
}

textarea:focus {
  outline: none;
  border-color: #007bff;
}

button {
  padding: 0.75rem 2rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

button:hover:not(:disabled) {
  background: #0056b3;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 響應式設計 */
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
</style>
