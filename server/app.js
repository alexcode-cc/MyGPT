const express = require('express');
const cors = require('cors');
const axios = require('axios');
const multer = require('multer');
const FormData = require('form-data');
const fs = require('fs');

const app = express();
app.use(cors());
app.use(express.json({ limit: '50mb' })); // 增加 body 大小限制以支援圖片

const OLLAMA_API = 'http://localhost:11434/api';
const WHISPER_API = process.env.WHISPER_API || 'http://localhost:8001';

// 設定檔案上傳
const upload = multer({ 
  dest: '/tmp/uploads/',
  limits: { fileSize: 50 * 1024 * 1024 } // 50MB 限制
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

// 音訊轉錄 API - 轉發到 faster-whisper 服務
app.post('/api/transcribe', upload.single('audio'), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: '未提供音訊檔案' });
  }

  const filePath = req.file.path;
  const originalName = req.file.originalname;
  const language = req.body.language || null;

  try {
    // 建立 FormData 轉發到 Whisper 服務
    const formData = new FormData();
    formData.append('audio', fs.createReadStream(filePath), {
      filename: originalName,
      contentType: req.file.mimetype
    });
    
    if (language) {
      formData.append('language', language);
    }
    formData.append('task', 'transcribe');
    // 預設關閉 VAD，避免音樂歌詞被過濾
    formData.append('vad_filter', req.body.vad_filter || 'false');

    console.log(`轉發音檔到 Whisper 服務: ${originalName}`);
    
    const response = await axios.post(`${WHISPER_API}/transcribe`, formData, {
      headers: {
        ...formData.getHeaders()
      },
      timeout: 300000, // 5 分鐘超時
      maxContentLength: Infinity,
      maxBodyLength: Infinity
    });

    // 清理暫存檔案
    fs.unlinkSync(filePath);

    console.log(`轉錄完成: 語言=${response.data.language}, 時長=${response.data.duration}秒`);
    
    res.json(response.data);

  } catch (error) {
    // 清理暫存檔案
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
    }

    console.error('Transcribe API Error:', error.response?.data || error.message);
    
    if (error.code === 'ECONNREFUSED') {
      return res.status(503).json({ 
        error: 'Whisper 服務未啟動',
        detail: '請先啟動 whisper-server 服務',
        suggestion: 'cd whisper-server && ./start.sh'
      });
    }
    
    if (error.response?.data) {
      return res.status(error.response.status || 500).json(error.response.data);
    }
    
    res.status(500).json({ error: error.message });
  }
});

// 檢查 Whisper 服務狀態
app.get('/api/whisper/health', async (req, res) => {
  try {
    const response = await axios.get(`${WHISPER_API}/health`, { timeout: 5000 });
    res.json({
      available: true,
      ...response.data
    });
  } catch (error) {
    res.json({
      available: false,
      error: error.code === 'ECONNREFUSED' ? 'Whisper 服務未啟動' : error.message
    });
  }
});

// 取得 Whisper 模型資訊
app.get('/api/whisper/models', async (req, res) => {
  try {
    const response = await axios.get(`${WHISPER_API}/models`, { timeout: 5000 });
    res.json(response.data);
  } catch (error) {
    res.status(503).json({ 
      error: 'Whisper 服務不可用',
      detail: error.message 
    });
  }
});

const PORT = 3001;
const HOST = '0.0.0.0';
app.listen(PORT, HOST, () => {
  console.log(`Server running on http://${HOST}:${PORT}`);
  console.log(`Whisper API: ${WHISPER_API}`);
});
