const express = require('express');
const cors = require('cors');
const axios = require('axios');

const app = express();
app.use(cors());
app.use(express.json());

const OLLAMA_API = 'http://localhost:11434/api';

// 對話 API
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

// 取得可用模型列表
app.get('/api/models', async (req, res) => {
  try {
    const response = await axios.get(`${OLLAMA_API}/tags`);
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

const PORT = 3001;
const HOST = '0.0.0.0';
app.listen(PORT, HOST, () => {
  console.log(`Server running on http://${HOST}:${PORT}`);
});
