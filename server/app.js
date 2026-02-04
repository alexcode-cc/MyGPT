const express = require('express');
const cors = require('cors');
const axios = require('axios');
const multer = require('multer');
const fs = require('fs');
const path = require('path');
const FormData = require('form-data');

const app = express();
app.use(cors());
app.use(express.json({ limit: '50mb' })); // 增加 body 大小限制以支援圖片

const OLLAMA_API = 'http://localhost:11434/api';

// 設定檔案上傳
const upload = multer({ 
  dest: '/tmp/uploads/',
  limits: { fileSize: 25 * 1024 * 1024 } // 25MB 限制
});

// 對話 API（支援圖片）
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
    console.error('Chat API Error:', error.response?.data || error.message);
    res.status(500).json({ error: error.message });
  }
});

// 取得可用模型列表
app.get('/api/models', async (req, res) => {
  try {
    const response = await axios.get(`${OLLAMA_API}/tags`);
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 音訊轉錄 API - 使用 Whisper 模型
app.post('/api/transcribe', upload.single('audio'), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: '未提供音訊檔案' });
  }

  const filePath = req.file.path;
  const whisperModel = req.body.model || 'whisper'; // 預設使用 whisper 模型

  try {
    // 讀取音訊檔案並轉為 base64
    const audioBuffer = fs.readFileSync(filePath);
    const audioBase64 = audioBuffer.toString('base64');

    // 使用 Ollama 的多模態功能（如果支援 whisper 模型）
    // 嘗試使用 generate API 與 whisper 模型
    try {
      const response = await axios.post(`${OLLAMA_API}/generate`, {
        model: whisperModel,
        prompt: '請將這段音訊轉錄為文字。',
        images: [audioBase64], // Whisper 模型可能使用 images 欄位處理音訊
        stream: false
      }, { timeout: 120000 }); // 2 分鐘超時

      // 清理暫存檔案
      fs.unlinkSync(filePath);

      res.json({ 
        text: response.data.response || '',
        model: whisperModel
      });
    } catch (whisperError) {
      // 如果 whisper 模型不可用，嘗試使用其他支援音訊的模型
      console.log('Whisper 模型不可用，嘗試使用 qwen2-audio...');
      
      try {
        const response = await axios.post(`${OLLAMA_API}/generate`, {
          model: 'qwen2-audio',
          prompt: '請將這段音訊轉錄為文字，只輸出轉錄結果，不要添加任何其他說明。',
          images: [audioBase64],
          stream: false
        }, { timeout: 120000 });

        fs.unlinkSync(filePath);
        res.json({ 
          text: response.data.response || '',
          model: 'qwen2-audio'
        });
      } catch (audioModelError) {
        // 清理檔案
        fs.unlinkSync(filePath);
        
        // 返回錯誤訊息
        res.status(503).json({ 
          error: '音訊轉錄服務不可用',
          detail: '本地 Ollama 未安裝支援音訊的模型（如 whisper 或 qwen2-audio）',
          suggestion: '請安裝音訊模型：ollama pull whisper 或 ollama pull qwen2-audio'
        });
      }
    }
  } catch (error) {
    // 確保清理檔案
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
    }
    console.error('Transcribe API Error:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// 檢查音訊模型是否可用
app.get('/api/audio-models', async (req, res) => {
  try {
    const response = await axios.get(`${OLLAMA_API}/tags`);
    const models = response.data.models || [];
    
    // 尋找支援音訊的模型
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

const PORT = 3001;
const HOST = '0.0.0.0';
app.listen(PORT, HOST, () => {
  console.log(`Server running on http://${HOST}:${PORT}`);
});
