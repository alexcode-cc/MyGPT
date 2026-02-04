<!-- App.vue -->
<template>
  <div class="app-container">
    <!-- 側邊欄 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <h2 v-if="!sidebarCollapsed">對話列表</h2>
        <button class="toggle-btn" @click="sidebarCollapsed = !sidebarCollapsed">
          {{ sidebarCollapsed ? '▶' : '◀' }}
        </button>
      </div>
      
      <div class="sidebar-content" v-if="!sidebarCollapsed">
        <!-- 新增對話按鈕 -->
        <button class="btn-new-chat" @click="createNewConversation">
          ➕ 新增對話
        </button>

        <!-- 對話歷史列表 -->
        <div class="conversation-list">
          <div 
            v-for="conv in conversations" 
            :key="conv.id"
            :class="['conversation-item', { active: conv.id === currentConversationId }]"
            @click="switchConversation(conv.id)"
          >
            <div class="conversation-info">
              <span class="conversation-title">{{ conv.title }}</span>
              <span class="conversation-date">{{ formatDate(conv.updatedAt) }}</span>
            </div>
            <div class="conversation-actions">
              <button 
                class="action-btn edit-btn" 
                @click.stop="startEditTitle(conv)"
                title="編輯標題"
              >✏️</button>
              <button 
                class="action-btn delete-btn" 
                @click.stop="deleteConversation(conv.id)"
                title="刪除對話"
              >🗑️</button>
            </div>
          </div>
          
          <div v-if="conversations.length === 0" class="no-conversations">
            尚無對話紀錄
          </div>
        </div>

        <hr class="divider" />

        <!-- 設定區塊 -->
        <div class="settings-section">
          <h3 class="section-title" @click="settingsExpanded = !settingsExpanded">
            ⚙️ 設定
            <span class="expand-icon">{{ settingsExpanded ? '▼' : '▶' }}</span>
          </h3>
          
          <div v-if="settingsExpanded" class="settings-content">
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
                rows="4"
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

            <!-- 資料管理 -->
            <div class="setting-group">
              <label>資料管理</label>
              <button class="btn-danger" @click="clearAllData">清除所有資料</button>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <!-- 編輯標題對話框 -->
    <div v-if="editingConversation" class="modal-overlay" @click="cancelEditTitle">
      <div class="modal" @click.stop>
        <h3>編輯對話標題</h3>
        <input 
          v-model="editingTitle" 
          @keydown.enter="saveEditTitle"
          @keydown.escape="cancelEditTitle"
          ref="editTitleInput"
          placeholder="輸入新標題"
        />
        <div class="modal-actions">
          <button class="btn-secondary" @click="cancelEditTitle">取消</button>
          <button class="btn-primary" @click="saveEditTitle">儲存</button>
        </div>
      </div>
    </div>

    <!-- 主聊天區域 -->
    <main class="chat-container">
      <div class="header">
        <h1>{{ currentConversation?.title || '本地 AI 助手' }}</h1>
        <div class="header-info">
          <!-- 模型選擇下拉選單 -->
          <div class="model-selector" v-if="selectedModel">
            <button 
              class="model-badge clickable" 
              @click="toggleModelDropdown"
              :title="'點擊變更模型'"
            >
              {{ selectedModel }}
              <span class="dropdown-arrow">▼</span>
            </button>
            <div v-if="showModelDropdown" class="model-dropdown">
              <div 
                v-for="model in models" 
                :key="model.name"
                :class="['model-option', { active: model.name === selectedModel }]"
                @click="selectModel(model.name)"
              >
                {{ model.name }}
              </div>
            </div>
          </div>
          <span class="system-prompt-indicator" v-if="systemPrompt" title="系統提示詞已啟用">
            📝 系統提示詞已設定
          </span>
          <span class="message-count" v-if="messages.length > 0">
            {{ messages.length }} 則訊息
          </span>
        </div>
      </div>
      <!-- 點擊外部關閉下拉選單 -->
      <div v-if="showModelDropdown" class="dropdown-backdrop" @click="showModelDropdown = false"></div>

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
              <span class="message-time" v-if="msg.timestamp">{{ formatTime(msg.timestamp) }}</span>
              <!-- 編輯按鈕：只顯示在最後一組對話的使用者訊息上 -->
              <button 
                v-if="msg.role === 'user' && canEditMessage(idx)"
                class="edit-message-btn"
                @click="editLastMessage"
                title="編輯並重新發送"
              >
                ✏️
              </button>
            </div>
            <!-- 顯示附加的圖片 -->
            <div v-if="msg.images && msg.images.length > 0" class="message-images">
              <img 
                v-for="(img, imgIdx) in msg.images" 
                :key="imgIdx" 
                :src="'data:image/jpeg;base64,' + img" 
                alt="上傳的圖片"
                class="message-image"
                @click="previewImage('data:image/jpeg;base64,' + img)"
              />
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
        <!-- 編輯模式提示 -->
        <div v-if="isEditingMessage" class="editing-indicator">
          <span>✏️ 編輯訊息中</span>
          <button class="cancel-edit-btn" @click="cancelEditMessage">取消編輯</button>
        </div>

        <!-- 圖片預覽區 -->
        <div v-if="uploadedImages.length > 0 || editingImages.length > 0" class="uploaded-images-preview">
          <!-- 編輯模式下的原有圖片 -->
          <div 
            v-for="(img, idx) in editingImages" 
            :key="'edit-img-' + idx" 
            class="uploaded-image-item editing"
          >
            <img :src="'data:image/jpeg;base64,' + img" alt="原有圖片" />
            <button class="remove-media-btn" @click="removeEditingImage(idx)">✕</button>
          </div>
          <!-- 新上傳的圖片 -->
          <div 
            v-for="(img, idx) in uploadedImages" 
            :key="'new-img-' + idx" 
            class="uploaded-image-item"
          >
            <img :src="img.preview" alt="預覽" />
            <button class="remove-media-btn" @click="removeUploadedImage(idx)">✕</button>
          </div>
        </div>
        
        <!-- 語音輸入狀態 -->
        <div v-if="isRecording" class="speech-indicator">
          <span class="recording-dot"></span>
          <span>正在聆聽... 說完後點擊麥克風停止</span>
        </div>
        
        <div class="input-row">
          <!-- 上傳圖片按鈕 -->
          <input
            type="file"
            ref="fileInput"
            accept="image/*"
            multiple
            @change="handleImageUpload"
            style="display: none"
          />
          <button 
            class="upload-btn" 
            @click="triggerImageUpload"
            :disabled="isTyping"
            title="上傳圖片（支援視覺模型如 qwen3-vl）"
          >
            📷
          </button>
          
          <!-- 語音輸入按鈕 -->
          <button 
            class="upload-btn"
            :class="{ 'recording': isRecording }"
            @click="toggleSpeechRecognition"
            :disabled="isTyping || !speechSupported"
            :title="speechSupported ? (isRecording ? '停止語音輸入' : '語音輸入（點擊開始說話）') : '您的瀏覽器不支援語音輸入'"
          >
            {{ isRecording ? '🔴' : '🎤' }}
          </button>
          
          <textarea
            ref="messageInput"
            v-model="userInput"
            @keydown.enter.exact.prevent="sendMessage"
            @keydown.escape="cancelEditMessage"
            @paste="handlePaste"
            :placeholder="getInputPlaceholder"
            :disabled="isTyping"
          />
          <button 
            @click="sendMessage" 
            :disabled="isTyping || !hasContent"
            :class="{ 'resend-btn': isEditingMessage }"
          >
            {{ isEditingMessage ? '重新發送' : '發送' }}
          </button>
        </div>
      </div>
    </main>

    <!-- 圖片預覽對話框 -->
    <div v-if="previewImageUrl" class="image-preview-modal" @click="previewImageUrl = null">
      <img :src="previewImageUrl" alt="預覽圖片" @click.stop />
      <button class="close-preview-btn" @click="previewImageUrl = null">✕</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue';
import { marked } from 'marked';

// 介面定義
interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: number;
  images?: string[]; // base64 編碼的圖片
}

interface UploadedImage {
  file: File;
  preview: string;
  base64: string;
}

// 語音識別介面
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  isFinal: boolean;
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
  model?: string;
  systemPrompt?: string;
}

// 常數
const API_BASE = '/api';
const STORAGE_KEY = 'chatbot_conversations';
const CURRENT_CONV_KEY = 'chatbot_current_conversation';

// 狀態
const selectedModel = ref('deepseek-r1:8b');
const models = ref<any[]>([]);
const userInput = ref('');
const isTyping = ref(false);
const currentResponse = ref('');
const messagesContainer = ref<HTMLElement>();
const sidebarCollapsed = ref(false);
const settingsExpanded = ref(false);
const systemPrompt = ref('');

// 對話管理狀態
const conversations = ref<Conversation[]>([]);
const currentConversationId = ref<string | null>(null);

// 編輯標題狀態
const editingConversation = ref<Conversation | null>(null);
const editingTitle = ref('');
const editTitleInput = ref<HTMLInputElement>();

// 模型下拉選單狀態
const showModelDropdown = ref(false);

// 圖片上傳狀態
const uploadedImages = ref<UploadedImage[]>([]);
const fileInput = ref<HTMLInputElement>();
const previewImageUrl = ref<string | null>(null);
const messageInput = ref<HTMLTextAreaElement>();

// 編輯訊息狀態
const isEditingMessage = ref(false);
const editingImages = ref<string[]>([]); // 編輯時保留的原有圖片（base64）

// 語音輸入狀態
const isRecording = ref(false);
const speechRecognition = ref<any>(null);
const speechSupported = ref(false);

// 預設提示詞範本
const promptTemplates = [
  { name: '繁體中文', prompt: '請總是使用繁體中文回應所有訊息。' },
  { name: '簡潔回答', prompt: '請簡潔扼要地回答問題，避免冗長的解釋。' },
  { name: '詳細解釋', prompt: '請詳細解釋每個概念，並提供相關範例。' },
  { name: '程式專家', prompt: '你是一位資深程式開發者，請提供專業的程式建議和最佳實踐。使用繁體中文回應。' },
  { name: '友善助手', prompt: '你是一位友善且有耐心的助手，請用輕鬆的語氣回應。使用繁體中文。' },
  { name: '學習導師', prompt: '你是一位耐心的學習導師，請用淺顯易懂的方式解釋概念，適時提問以確認理解。使用繁體中文。' },
];

// 計算屬性
const currentConversation = computed(() => {
  return conversations.value.find(c => c.id === currentConversationId.value) || null;
});

const messages = computed(() => {
  return currentConversation.value?.messages || [];
});

// 是否有內容可發送
const hasContent = computed(() => {
  return userInput.value.trim() || 
         uploadedImages.value.length > 0 || 
         editingImages.value.length > 0;
});

// 輸入框 placeholder
const getInputPlaceholder = computed(() => {
  if (isEditingMessage.value) {
    return '編輯訊息後按 Enter 重新發送，Esc 取消';
  }
  if (isRecording.value) {
    return '正在聆聽...';
  }
  return '輸入訊息... (Enter 發送, Shift+Enter 換行)';
});

// 生命週期
onMounted(async () => {
  await loadModels();
  loadSavedData();
  initSpeechRecognition();
});

// 監聽模型變更
watch(selectedModel, (newModel) => {
  localStorage.setItem('selectedModel', newModel);
  if (currentConversation.value) {
    currentConversation.value.model = newModel;
    saveConversations();
  }
});

// ========== 資料載入與儲存 ==========

function loadSavedData() {
  // 載入對話列表
  const savedConversations = localStorage.getItem(STORAGE_KEY);
  if (savedConversations) {
    try {
      conversations.value = JSON.parse(savedConversations);
      // 按更新時間排序（最新的在前）
      conversations.value.sort((a, b) => b.updatedAt - a.updatedAt);
    } catch (e) {
      console.error('載入對話失敗:', e);
      conversations.value = [];
    }
  }

  // 載入當前對話 ID
  const savedCurrentId = localStorage.getItem(CURRENT_CONV_KEY);
  if (savedCurrentId && conversations.value.some(c => c.id === savedCurrentId)) {
    currentConversationId.value = savedCurrentId;
  } else if (conversations.value.length > 0) {
    currentConversationId.value = conversations.value[0].id;
  }

  // 載入系統提示詞
  const savedPrompt = localStorage.getItem('systemPrompt');
  if (savedPrompt) {
    systemPrompt.value = savedPrompt;
  }

  // 載入模型選擇
  const savedModel = localStorage.getItem('selectedModel');
  if (savedModel) {
    selectedModel.value = savedModel;
  }
}

function saveConversations() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations.value));
}

function saveCurrentConversationId() {
  if (currentConversationId.value) {
    localStorage.setItem(CURRENT_CONV_KEY, currentConversationId.value);
  } else {
    localStorage.removeItem(CURRENT_CONV_KEY);
  }
}

// ========== 圖片上傳 ==========

function triggerImageUpload() {
  fileInput.value?.click();
}

async function handleImageUpload(event: Event) {
  const input = event.target as HTMLInputElement;
  if (!input.files) return;
  
  for (const file of Array.from(input.files)) {
    if (file.type.startsWith('image/')) {
      await addImage(file);
    }
  }
  
  // 清空 input 以便重複選擇同一檔案
  input.value = '';
}

async function handlePaste(event: ClipboardEvent) {
  const items = event.clipboardData?.items;
  if (!items) return;
  
  for (const item of Array.from(items)) {
    if (item.type.startsWith('image/')) {
      event.preventDefault();
      const file = item.getAsFile();
      if (file) {
        await addImage(file);
      }
    }
  }
}

async function addImage(file: File) {
  // 限制最多 4 張圖片
  if (uploadedImages.value.length >= 4) {
    alert('最多只能上傳 4 張圖片');
    return;
  }
  
  // 限制檔案大小 (10MB)
  if (file.size > 10 * 1024 * 1024) {
    alert('圖片大小不能超過 10MB');
    return;
  }
  
  const base64 = await fileToBase64(file);
  const preview = URL.createObjectURL(file);
  
  uploadedImages.value.push({
    file,
    preview,
    base64
  });
}

// ========== 語音輸入 ==========

function initSpeechRecognition() {
  // 檢查瀏覽器是否支援語音識別
  const SpeechRecognitionAPI = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  
  if (!SpeechRecognitionAPI) {
    speechSupported.value = false;
    console.log('此瀏覽器不支援語音識別');
    return;
  }
  
  speechSupported.value = true;
  
  const recognition = new SpeechRecognitionAPI();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'zh-TW'; // 預設繁體中文
  
  recognition.onresult = (event: SpeechRecognitionEvent) => {
    let finalTranscript = '';
    let interimTranscript = '';
    
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        finalTranscript += transcript;
      } else {
        interimTranscript += transcript;
      }
    }
    
    // 將識別到的文字加入輸入框
    if (finalTranscript) {
      userInput.value += finalTranscript;
    }
  };
  
  recognition.onerror = (event: any) => {
    console.error('語音識別錯誤:', event.error);
    isRecording.value = false;
    
    if (event.error === 'not-allowed') {
      alert('請允許麥克風存取權限以使用語音輸入功能');
    } else if (event.error === 'no-speech') {
      // 沒有偵測到語音，靜默處理
    } else {
      alert(`語音識別錯誤: ${event.error}`);
    }
  };
  
  recognition.onend = () => {
    // 如果仍在錄音狀態，重新啟動（continuous 模式有時會自動停止）
    if (isRecording.value) {
      try {
        recognition.start();
      } catch (e) {
        isRecording.value = false;
      }
    }
  };
  
  speechRecognition.value = recognition;
}

function toggleSpeechRecognition() {
  if (!speechRecognition.value) {
    alert('您的瀏覽器不支援語音輸入功能');
    return;
  }
  
  if (isRecording.value) {
    // 停止錄音
    speechRecognition.value.stop();
    isRecording.value = false;
  } else {
    // 開始錄音
    try {
      speechRecognition.value.start();
      isRecording.value = true;
    } catch (e) {
      console.error('無法啟動語音識別:', e);
      alert('無法啟動語音識別，請檢查麥克風權限');
    }
  }
}

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      // 移除 data:image/xxx;base64, 前綴
      const base64 = result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function removeUploadedImage(index: number) {
  const img = uploadedImages.value[index];
  URL.revokeObjectURL(img.preview);
  uploadedImages.value.splice(index, 1);
}

function clearUploadedImages() {
  uploadedImages.value.forEach(img => URL.revokeObjectURL(img.preview));
  uploadedImages.value = [];
}

function previewImage(url: string) {
  previewImageUrl.value = url;
}

function removeEditingImage(index: number) {
  editingImages.value.splice(index, 1);
}

// ========== 編輯訊息功能 ==========

// 判斷訊息是否可以編輯（只有最後一組對話的使用者訊息可以編輯）
function canEditMessage(idx: number): boolean {
  if (isTyping.value || isEditingMessage.value) return false;
  
  const msgs = messages.value;
  if (msgs.length === 0) return false;
  
  // 找到最後一個使用者訊息的索引
  let lastUserIdx = -1;
  for (let i = msgs.length - 1; i >= 0; i--) {
    if (msgs[i].role === 'user') {
      lastUserIdx = i;
      break;
    }
  }
  
  return idx === lastUserIdx;
}

// 開始編輯最後一則訊息
function editLastMessage() {
  const conv = currentConversation.value;
  if (!conv || conv.messages.length === 0) return;
  
  // 找到最後一個使用者訊息
  let lastUserIdx = -1;
  for (let i = conv.messages.length - 1; i >= 0; i--) {
    if (conv.messages[i].role === 'user') {
      lastUserIdx = i;
      break;
    }
  }
  
  if (lastUserIdx === -1) return;
  
  const lastUserMessage = conv.messages[lastUserIdx];
  
  // 設定編輯狀態
  isEditingMessage.value = true;
  userInput.value = lastUserMessage.content;
  
  // 保留原有圖片
  if (lastUserMessage.images && lastUserMessage.images.length > 0) {
    editingImages.value = [...lastUserMessage.images];
  } else {
    editingImages.value = [];
  }
  
  // 清空新上傳的圖片
  clearUploadedImages();
  
  // 聚焦到輸入框
  nextTick(() => {
    messageInput.value?.focus();
    // 將游標移到文字末尾
    if (messageInput.value) {
      messageInput.value.selectionStart = messageInput.value.value.length;
      messageInput.value.selectionEnd = messageInput.value.value.length;
    }
  });
}

// 取消編輯
function cancelEditMessage() {
  if (!isEditingMessage.value) return;
  
  isEditingMessage.value = false;
  userInput.value = '';
  editingImages.value = [];
  clearUploadedImages();
}

// ========== 模型載入 ==========

async function loadModels() {
  try {
    const response = await fetch(`${API_BASE}/models`);
    const data = await response.json();
    models.value = data.models || [];
    
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

// ========== 模型選擇 ==========

function toggleModelDropdown() {
  showModelDropdown.value = !showModelDropdown.value;
}

function selectModel(modelName: string) {
  selectedModel.value = modelName;
  showModelDropdown.value = false;
  
  // 更新當前對話的模型
  if (currentConversation.value) {
    currentConversation.value.model = modelName;
    currentConversation.value.updatedAt = Date.now();
    saveConversations();
  }
}

// ========== 對話管理 ==========

function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

function createNewConversation() {
  const newConversation: Conversation = {
    id: generateId(),
    title: '新對話',
    messages: [],
    createdAt: Date.now(),
    updatedAt: Date.now(),
    model: selectedModel.value,
    systemPrompt: systemPrompt.value
  };
  
  conversations.value.unshift(newConversation);
  currentConversationId.value = newConversation.id;
  
  saveConversations();
  saveCurrentConversationId();
}

function switchConversation(id: string) {
  currentConversationId.value = id;
  saveCurrentConversationId();
  
  // 載入對話的模型設定
  const conv = conversations.value.find(c => c.id === id);
  if (conv?.model) {
    selectedModel.value = conv.model;
  }
}

function deleteConversation(id: string) {
  if (!confirm('確定要刪除這個對話嗎？')) return;
  
  const index = conversations.value.findIndex(c => c.id === id);
  if (index !== -1) {
    conversations.value.splice(index, 1);
    
    // 如果刪除的是當前對話，切換到第一個對話或清空
    if (currentConversationId.value === id) {
      currentConversationId.value = conversations.value[0]?.id || null;
    }
    
    saveConversations();
    saveCurrentConversationId();
  }
}

// ========== 標題編輯 ==========

function startEditTitle(conv: Conversation) {
  editingConversation.value = conv;
  editingTitle.value = conv.title;
  nextTick(() => {
    editTitleInput.value?.focus();
    editTitleInput.value?.select();
  });
}

function saveEditTitle() {
  if (editingConversation.value && editingTitle.value.trim()) {
    editingConversation.value.title = editingTitle.value.trim();
    editingConversation.value.updatedAt = Date.now();
    saveConversations();
  }
  cancelEditTitle();
}

function cancelEditTitle() {
  editingConversation.value = null;
  editingTitle.value = '';
}

// ========== 訊息發送 ==========

async function sendMessage() {
  if (!hasContent.value || isTyping.value) return;

  // 如果沒有當前對話，創建一個新的
  if (!currentConversationId.value) {
    createNewConversation();
  }

  const conv = currentConversation.value;
  if (!conv) return;

  // 處理編輯模式
  if (isEditingMessage.value) {
    await resendEditedMessage(conv);
    return;
  }

  // 停止語音輸入
  if (isRecording.value && speechRecognition.value) {
    speechRecognition.value.stop();
    isRecording.value = false;
  }

  // 收集圖片
  const currentImages = uploadedImages.value.map(img => img.base64);
  
  // 決定預設訊息
  const defaultMessage = currentImages.length > 0 ? '請描述這張圖片' : '';
  const userMessage = userInput.value.trim() || defaultMessage;
  
  if (!userMessage && currentImages.length === 0) return;
  
  const newMessage: Message = {
    role: 'user',
    content: userMessage,
    timestamp: Date.now(),
    images: currentImages.length > 0 ? currentImages : undefined
  };
  
  conv.messages.push(newMessage);
  
  // 如果是第一則訊息，用它作為對話標題
  if (conv.messages.length === 1) {
    const prefix = currentImages.length > 0 ? '📷 ' : '';
    const titleText = prefix + userMessage;
    conv.title = titleText.slice(0, 30) + (titleText.length > 30 ? '...' : '');
  }
  
  userInput.value = '';
  clearUploadedImages();
  isTyping.value = true;
  currentResponse.value = '';
  conv.updatedAt = Date.now();
  
  // 重新排序對話列表
  conversations.value.sort((a, b) => b.updatedAt - a.updatedAt);
  saveConversations();

  try {
    // 構建要發送的訊息
    const messagesToSend: any[] = [];
    
    if (systemPrompt.value.trim()) {
      messagesToSend.push({ role: 'system', content: systemPrompt.value.trim() });
    }
    
    // 發送 role、content 和 images
    messagesToSend.push(...conv.messages.map(m => {
      const msg: any = { role: m.role, content: m.content };
      if (m.images && m.images.length > 0) {
        msg.images = m.images;
      }
      return msg;
    }));

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

    const assistantMessage: Message = {
      role: 'assistant',
      content: currentResponse.value,
      timestamp: Date.now()
    };
    conv.messages.push(assistantMessage);
    currentResponse.value = '';
    
  } catch (error) {
    console.error('發送訊息失敗:', error);
    conv.messages.push({
      role: 'assistant',
      content: '抱歉，發生錯誤，請稍後再試。',
      timestamp: Date.now()
    });
  } finally {
    isTyping.value = false;
    conv.updatedAt = Date.now();
    saveConversations();
  }
}

// 重新發送編輯後的訊息
async function resendEditedMessage(conv: Conversation) {
  // 找到最後一個使用者訊息的索引
  let lastUserIdx = -1;
  for (let i = conv.messages.length - 1; i >= 0; i--) {
    if (conv.messages[i].role === 'user') {
      lastUserIdx = i;
      break;
    }
  }
  
  if (lastUserIdx === -1) {
    cancelEditMessage();
    return;
  }
  
  // 移除最後一個使用者訊息及其後的所有訊息（包括 AI 回應）
  conv.messages.splice(lastUserIdx);
  
  // 合併編輯中的圖片和新上傳的圖片
  const allImages = [
    ...editingImages.value,
    ...uploadedImages.value.map(img => img.base64)
  ];
  
  // 決定預設訊息
  const defaultMessage = allImages.length > 0 ? '請描述這張圖片' : '';
  const userMessage = userInput.value.trim() || defaultMessage;
  
  if (!userMessage && allImages.length === 0) {
    cancelEditMessage();
    return;
  }
  
  // 創建新的使用者訊息
  const newMessage: Message = {
    role: 'user',
    content: userMessage,
    timestamp: Date.now(),
    images: allImages.length > 0 ? allImages : undefined
  };
  
  conv.messages.push(newMessage);
  
  // 重置編輯狀態
  isEditingMessage.value = false;
  editingImages.value = [];
  userInput.value = '';
  clearUploadedImages();
  
  isTyping.value = true;
  currentResponse.value = '';
  conv.updatedAt = Date.now();
  
  conversations.value.sort((a, b) => b.updatedAt - a.updatedAt);
  saveConversations();
  
  try {
    const messagesToSend: any[] = [];
    
    if (systemPrompt.value.trim()) {
      messagesToSend.push({ role: 'system', content: systemPrompt.value.trim() });
    }
    
    messagesToSend.push(...conv.messages.map(m => {
      const msg: any = { role: m.role, content: m.content };
      if (m.images && m.images.length > 0) {
        msg.images = m.images;
      }
      return msg;
    }));

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

    const assistantMessage: Message = {
      role: 'assistant',
      content: currentResponse.value,
      timestamp: Date.now()
    };
    conv.messages.push(assistantMessage);
    currentResponse.value = '';
    
  } catch (error) {
    console.error('重新發送訊息失敗:', error);
    conv.messages.push({
      role: 'assistant',
      content: '抱歉，發生錯誤，請稍後再試。',
      timestamp: Date.now()
    });
  } finally {
    isTyping.value = false;
    conv.updatedAt = Date.now();
    saveConversations();
  }
}

// ========== 工具函式 ==========

function formatMarkdown(text: string) {
  return marked(text);
}

async function scrollToBottom() {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
}

function formatDate(timestamp: number): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) {
    return '今天';
  } else if (diffDays === 1) {
    return '昨天';
  } else if (diffDays < 7) {
    return `${diffDays} 天前`;
  } else {
    return date.toLocaleDateString('zh-TW');
  }
}

function formatTime(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString('zh-TW', {
    hour: '2-digit',
    minute: '2-digit'
  });
}

// ========== 系統提示詞 ==========

function saveSystemPrompt() {
  localStorage.setItem('systemPrompt', systemPrompt.value);
  if (currentConversation.value) {
    currentConversation.value.systemPrompt = systemPrompt.value;
    saveConversations();
  }
  alert('系統提示詞已儲存！');
}

function clearSystemPrompt() {
  systemPrompt.value = '';
  localStorage.removeItem('systemPrompt');
}

function applyTemplate(prompt: string) {
  systemPrompt.value = prompt;
}

// ========== 資料清除 ==========

function clearAllData() {
  if (!confirm('確定要清除所有對話和設定嗎？此操作無法復原。')) return;
  
  conversations.value = [];
  currentConversationId.value = null;
  systemPrompt.value = '';
  
  localStorage.removeItem(STORAGE_KEY);
  localStorage.removeItem(CURRENT_CONV_KEY);
  localStorage.removeItem('systemPrompt');
  
  alert('所有資料已清除！');
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
  background: #1a1a2e;
  color: white;
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
  border-bottom: 1px solid #333;
}

.sidebar-header h2 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 500;
}

.toggle-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  padding: 0.5rem;
  color: #888;
}

.toggle-btn:hover {
  color: white;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
}

/* 新增對話按鈕 */
.btn-new-chat {
  width: 100%;
  padding: 0.75rem;
  background: #16213e;
  color: white;
  border: 1px dashed #444;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.95rem;
  margin-bottom: 1rem;
  transition: all 0.2s;
}

.btn-new-chat:hover {
  background: #1f3460;
  border-color: #007bff;
}

/* 對話列表 */
.conversation-list {
  flex: 1;
  overflow-y: auto;
}

.conversation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 0.5rem;
  transition: background 0.2s;
}

.conversation-item:hover {
  background: #16213e;
}

.conversation-item.active {
  background: #1f3460;
  border-left: 3px solid #007bff;
}

.conversation-info {
  flex: 1;
  min-width: 0;
}

.conversation-title {
  display: block;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 0.25rem;
}

.conversation-date {
  font-size: 0.75rem;
  color: #888;
}

.conversation-actions {
  display: flex;
  gap: 0.25rem;
  opacity: 0;
  transition: opacity 0.2s;
}

.conversation-item:hover .conversation-actions {
  opacity: 1;
}

.action-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  font-size: 0.8rem;
  border-radius: 4px;
  transition: background 0.2s;
}

.action-btn:hover {
  background: rgba(255,255,255,0.1);
}

.no-conversations {
  text-align: center;
  color: #666;
  padding: 2rem;
  font-size: 0.9rem;
}

/* 分隔線 */
.divider {
  border: none;
  border-top: 1px solid #333;
  margin: 1rem 0;
}

/* 設定區塊 */
.settings-section {
  margin-top: auto;
}

.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  margin: 0;
}

.section-title:hover {
  background: #16213e;
}

.expand-icon {
  font-size: 0.7rem;
  color: #888;
}

.settings-content {
  padding-top: 0.5rem;
}

.setting-group {
  margin-bottom: 1rem;
}

.setting-group label {
  display: block;
  font-size: 0.8rem;
  color: #aaa;
  margin-bottom: 0.5rem;
}

.setting-group select,
.setting-group textarea {
  width: 100%;
  padding: 0.5rem;
  background: #16213e;
  border: 1px solid #333;
  border-radius: 4px;
  color: white;
  font-family: inherit;
  font-size: 0.85rem;
}

.setting-group select:focus,
.setting-group textarea:focus {
  outline: none;
  border-color: #007bff;
}

.setting-group textarea {
  resize: vertical;
  min-height: 80px;
}

.prompt-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.btn-secondary {
  flex: 1;
  padding: 0.4rem;
  background: #333;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
}

.btn-secondary:hover {
  background: #444;
}

.btn-danger {
  width: 100%;
  padding: 0.5rem;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
}

.btn-danger:hover {
  background: #c82333;
}

.template-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.template-btn {
  padding: 0.3rem 0.6rem;
  background: #333;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 0.75rem;
  color: #ccc;
  transition: all 0.2s;
}

.template-btn:hover {
  background: #007bff;
  color: white;
}

/* 對話框 Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  width: 90%;
  max-width: 400px;
}

.modal h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
}

.modal input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  margin-bottom: 1rem;
}

.modal input:focus {
  outline: none;
  border-color: #007bff;
}

.modal-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.btn-primary {
  padding: 0.5rem 1rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-primary:hover {
  background: #0056b3;
}

/* 主聊天區域 */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
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
  font-size: 1.3rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 400px;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-shrink: 0;
}

/* 模型選擇器 */
.model-selector {
  position: relative;
}

.model-badge {
  background: #e9ecef;
  padding: 0.3rem 0.8rem;
  border-radius: 20px;
  font-size: 0.8rem;
  color: #495057;
  border: none;
}

.model-badge.clickable {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  transition: all 0.2s;
}

.model-badge.clickable:hover {
  background: #007bff;
  color: white;
}

.dropdown-arrow {
  font-size: 0.6rem;
  transition: transform 0.2s;
}

.model-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.5rem;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  min-width: 200px;
  max-height: 300px;
  overflow-y: auto;
  z-index: 1001;
}

.model-option {
  padding: 0.6rem 1rem;
  cursor: pointer;
  font-size: 0.85rem;
  transition: background 0.2s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.model-option:hover {
  background: #f0f0f0;
}

.model-option.active {
  background: #e3f2fd;
  color: #007bff;
  font-weight: 500;
}

.model-option:first-child {
  border-radius: 8px 8px 0 0;
}

.model-option:last-child {
  border-radius: 0 0 8px 8px;
}

.dropdown-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
}

.system-prompt-indicator {
  font-size: 0.8rem;
  color: #28a745;
}

.message-count {
  font-size: 0.8rem;
  color: #888;
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

.message-time {
  font-size: 0.75rem;
  color: #999;
}

/* 編輯訊息按鈕 */
.edit-message-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.8rem;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  opacity: 0;
  transition: all 0.2s;
}

.message:hover .edit-message-btn {
  opacity: 0.6;
}

.edit-message-btn:hover {
  opacity: 1 !important;
  background: rgba(0, 0, 0, 0.1);
}

.message.user .edit-message-btn:hover {
  background: rgba(255, 255, 255, 0.2);
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

.message.user .message-time {
  color: rgba(255,255,255,0.6);
}

/* 訊息中的圖片 */
.message-images {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.message-image {
  max-width: 200px;
  max-height: 200px;
  border-radius: 4px;
  cursor: pointer;
  transition: transform 0.2s;
  object-fit: cover;
}

.message-image:hover {
  transform: scale(1.02);
}

.message.user .message-image {
  border: 2px solid rgba(255,255,255,0.3);
}

/* 輸入區域 */
.input-area {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem 2rem;
  background: white;
  border-top: 1px solid #e0e0e0;
}

/* 編輯模式提示 */
.editing-indicator {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 4px;
  font-size: 0.85rem;
  color: #856404;
}

.cancel-edit-btn {
  background: none;
  border: none;
  color: #856404;
  cursor: pointer;
  font-size: 0.8rem;
  text-decoration: underline;
  padding: 0;
}

.cancel-edit-btn:hover {
  color: #533f03;
}

/* 語音輸入狀態 */
.speech-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: #ffe6e6;
  border: 1px solid #ff6b6b;
  border-radius: 4px;
  font-size: 0.85rem;
  color: #c92a2a;
}

.recording-dot {
  width: 10px;
  height: 10px;
  background: #ff0000;
  border-radius: 50%;
  animation: recording-pulse 1s ease-in-out infinite;
}

@keyframes recording-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.2); }
}

.upload-btn.recording {
  background: #ffe6e6;
  border: 2px solid #ff6b6b;
  animation: recording-btn-pulse 1s ease-in-out infinite;
}

@keyframes recording-btn-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(255, 107, 107, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(255, 107, 107, 0); }
}

.input-row {
  display: flex;
  gap: 0.5rem;
  align-items: flex-end;
}

.upload-btn {
  padding: 0.75rem;
  background: #e9ecef;
  color: #495057;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1.2rem;
  transition: all 0.2s;
  flex-shrink: 0;
}

.upload-btn:hover:not(:disabled) {
  background: #dee2e6;
}

.upload-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 上傳圖片預覽 */
.uploaded-images-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.uploaded-image-item {
  position: relative;
  width: 80px;
  height: 80px;
}

.uploaded-image-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.uploaded-image-item.editing img {
  border: 2px solid #ffc107;
}

/* 移除媒體按鈕 */
.remove-media-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #dc3545;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 0.7rem;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.remove-media-btn:hover {
  background: #c82333;
}

.uploaded-audio-item .remove-media-btn {
  position: static;
  margin-left: 0.25rem;
}

.input-area textarea {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: none;
  font-family: inherit;
  min-height: 60px;
  background: white;
  color: #333;
}

.input-area textarea:focus {
  outline: none;
  border-color: #007bff;
}

.input-row > button:last-child {
  padding: 0.75rem 2rem;
  background: #007bff;
  white-space: nowrap;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
  flex-shrink: 0;
}

.input-row > button:last-child:hover:not(:disabled) {
  background: #0056b3;
}

.input-row > button:last-child:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-row > button.resend-btn {
  background: #28a745;
}

.input-row > button.resend-btn:hover:not(:disabled) {
  background: #218838;
}

/* 圖片預覽對話框 */
.image-preview-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  cursor: pointer;
}

.image-preview-modal img {
  max-width: 90%;
  max-height: 90%;
  object-fit: contain;
  border-radius: 4px;
  cursor: default;
}

.close-preview-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-preview-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* 響應式設計 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100%;
    z-index: 100;
    box-shadow: 2px 0 10px rgba(0,0,0,0.3);
  }
  
  .sidebar.collapsed {
    width: 0;
    padding: 0;
    overflow: hidden;
  }
  
  .chat-container {
    width: 100%;
  }
  
  .header h1 {
    max-width: 200px;
    font-size: 1.1rem;
  }
}
</style>
