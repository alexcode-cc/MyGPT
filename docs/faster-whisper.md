# Faster-Whisper 音檔轉錄服務

## 概述

Faster-Whisper 是一個獨立的 Python 微服務，提供高效能的語音轉文字（STT）功能。由於 Ollama 目前不支援音訊多模態輸入，因此採用外部 STT 服務來處理音檔。

### 為什麼選擇 Faster-Whisper？

| 特性 | 說明 |
|------|------|
| **高效能** | 使用 CTranslate2 引擎，比原版 Whisper 快 4 倍 |
| **低記憶體** | 相同模型使用更少的 VRAM |
| **GPU 加速** | 完整支援 CUDA，利用 GPU 加速轉錄 |
| **多語言** | 支援 99 種語言，可自動偵測 |
| **開源** | MIT 授權，可自由使用 |

## 架構

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Faster-Whisper 服務 (Port 8001)                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      │
│  │   FastAPI    │      │   Whisper    │      │   Unicode    │      │
│  │   REST API   │─────▶│    Model     │─────▶│   語言偵測   │      │
│  │              │      │  (large-v3)  │      │              │      │
│  └──────────────┘      └──────────────┘      └──────────────┘      │
│         │                     │                     │               │
│         │                     ▼                     │               │
│         │              ┌──────────────┐             │               │
│         │              │ CTranslate2  │             │               │
│         │              │  (GPU/CPU)   │             │               │
│         │              └──────────────┘             │               │
│         │                                           │               │
│         └───────────────────┬───────────────────────┘               │
│                             ▼                                       │
│                    ┌──────────────────┐                             │
│                    │   JSON Response  │                             │
│                    │   - text         │                             │
│                    │   - languages[]  │                             │
│                    │   - duration     │                             │
│                    │   - segments[]   │                             │
│                    └──────────────────┘                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 檔案結構

```
whisper-server/
├── main.py              # FastAPI 主程式
├── requirements.txt     # Python 依賴
├── start.sh             # 啟動腳本（含 CUDA 設定）
└── .venv/               # Python 虛擬環境
```

## 安裝與設定

### 前置需求

- Python 3.9+
- NVIDIA GPU（選用，可使用 CPU）
- CUDA 12（GPU 加速需要）
- 足夠的 VRAM（large-v3 需要約 10GB）

### 安裝步驟

```bash
# 1. 進入 whisper-server 目錄
cd whisper-server

# 2. 建立 Python 虛擬環境（使用 uv 或 venv）
uv venv
# 或
python -m venv .venv

# 3. 啟動虛擬環境
source .venv/bin/activate

# 4. 安裝依賴
uv pip install -r requirements.txt
# 或
pip install -r requirements.txt
```

### 依賴套件

```txt
faster-whisper>=1.0.0     # Whisper 推理引擎
fastapi>=0.100.0          # Web 框架
uvicorn>=0.23.0           # ASGI 伺服器
python-multipart>=0.0.6   # 檔案上傳支援
```

## 啟動服務

### 使用啟動腳本（推薦）

```bash
cd whisper-server
chmod +x start.sh
./start.sh
```

啟動腳本會自動：
1. 啟動虛擬環境
2. 設定 CUDA 函式庫路徑
3. 載入預設環境變數
4. 啟動 FastAPI 服務

### 手動啟動

```bash
cd whisper-server
source .venv/bin/activate

# 設定 CUDA 路徑（如需要）
export LD_LIBRARY_PATH="/usr/local/lib/ollama/cuda_v12:${LD_LIBRARY_PATH:-}"

# 啟動服務
python main.py
```

## 環境變數

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `WHISPER_MODEL_SIZE` | `large-v3` | Whisper 模型大小 |
| `WHISPER_DEVICE` | `cuda` | 執行裝置（cuda 或 cpu） |
| `WHISPER_COMPUTE_TYPE` | `float16` | 計算類型 |
| `WHISPER_PORT` | `8001` | 服務埠號 |
| `WHISPER_HOST` | `0.0.0.0` | 監聽地址 |

### 計算類型選項

| 類型 | 說明 | 適用場景 |
|------|------|----------|
| `float16` | 半精度浮點 | GPU（預設，最佳效能） |
| `int8_float16` | 混合精度 | GPU（較低 VRAM） |
| `int8` | 8 位元整數 | CPU 或低 VRAM |
| `float32` | 單精度浮點 | CPU 備用 |

## 可用模型

| 模型 | 參數量 | VRAM | 速度 | 品質 | 適用場景 |
|------|--------|------|------|------|----------|
| `tiny` | 39M | ~1GB | ⚡⚡⚡⚡⚡ | ★☆☆☆☆ | 快速測試 |
| `base` | 74M | ~1GB | ⚡⚡⚡⚡ | ★★☆☆☆ | 基本轉錄 |
| `small` | 244M | ~2GB | ⚡⚡⚡ | ★★★☆☆ | 一般使用 |
| `medium` | 769M | ~5GB | ⚡⚡ | ★★★★☆ | 較高品質 |
| `large-v3` | 1550M | ~10GB | ⚡ | ★★★★★ | 最高品質（預設） |
| `turbo` | 809M | ~6GB | ⚡⚡⚡ | ★★★★☆ | 速度與品質平衡 |

### 切換模型

```bash
# 使用較小模型（較快但品質較低）
WHISPER_MODEL_SIZE=base ./start.sh

# 使用 turbo 模型（平衡選擇）
WHISPER_MODEL_SIZE=turbo ./start.sh
```

## API 端點

### GET /

健康檢查與服務資訊。

**回應範例：**
```json
{
  "status": "ok",
  "service": "faster-whisper",
  "model": "large-v3",
  "device": "cuda"
}
```

### GET /health

檢查模型是否已載入。

**回應範例：**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

### POST /transcribe

轉錄音檔為文字。

**請求格式：** `multipart/form-data`

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `audio` | File | ✅ | 音訊檔案 |
| `language` | string | ❌ | 語言代碼（不指定則自動偵測） |
| `task` | string | ❌ | `transcribe`（轉錄）或 `translate`（翻譯為英文） |
| `vad_filter` | boolean | ❌ | VAD 過濾（預設 false，音樂建議關閉） |
| `word_timestamps` | boolean | ❌ | 是否返回單詞時間戳 |

**支援的音訊格式：**
- MP3、WAV、M4A、FLAC、OGG、WebM、MP4

**回應範例：**
```json
{
  "text": "You are always gonna be my love いつか誰かとまた恋に落ちても",
  "language": "ja",
  "languages": ["en", "ja"],
  "language_probability": 0.876,
  "duration": 35.42,
  "duration_after_vad": 35.42,
  "segments": [
    {
      "start": 0.0,
      "end": 5.12,
      "text": "You are always gonna be my love"
    },
    {
      "start": 5.12,
      "end": 10.24,
      "text": "いつか誰かとまた恋に落ちても"
    }
  ]
}
```

### GET /models

列出可用的模型資訊。

**回應範例：**
```json
{
  "available_models": [
    {"name": "tiny", "parameters": "39M", "vram": "~1GB"},
    {"name": "base", "parameters": "74M", "vram": "~1GB"},
    {"name": "large-v3", "parameters": "1550M", "vram": "~10GB"}
  ],
  "current_model": "large-v3",
  "device": "cuda",
  "compute_type": "float16"
}
```

## 核心實作

### 多語言偵測

Whisper 只會回傳一個主要語言，但實際音檔可能包含多種語言（如日英混合歌曲）。因此實作了基於 Unicode 字符分析的多語言偵測：

```python
def detect_languages_in_text(text: str) -> List[str]:
    """
    分析文字中包含的語言
    基於 Unicode 字符範圍判斷
    """
    languages = set()
    
    for char in text:
        # 取得字符的 Unicode 名稱
        name = unicodedata.name(char, '')
        
        # 日語（平假名、片假名）
        if 'HIRAGANA' in name or 'KATAKANA' in name:
            languages.add('ja')
        # 中文（CJK 漢字）
        elif 'CJK' in name:
            if 'ja' not in languages:
                languages.add('zh')
        # 拉丁字母（英語等）
        elif 'LATIN' in name:
            languages.add('en')
        # ... 其他語言
    
    # 如果有日語假名，則 CJK 漢字歸類為日語
    if 'ja' in languages and 'zh' in languages:
        languages.discard('zh')
    
    return sorted(list(languages))
```

**支援的語言偵測：**
- `en` - 英語（拉丁字母）
- `ja` - 日語（平假名、片假名）
- `zh` - 中文（CJK 漢字）
- `ko` - 韓語（韓文字母）
- `ar` - 阿拉伯語
- `th` - 泰語
- `ru` - 俄語（西里爾字母）

### 音樂轉錄優化

音樂和歌曲的轉錄需要特別處理，避免歌聲被當作非語音過濾掉：

```python
segments, info = model.transcribe(
    audio_path,
    # VAD 設定 - 音樂建議關閉
    vad_filter=False,  # 預設關閉，避免過濾歌聲
    vad_parameters=dict(
        min_silence_duration_ms=300,   # 更短的靜音判定
        speech_pad_ms=400,             # 語音前後保留更多
        threshold=0.3                  # 更低的閾值
    ) if vad_filter else None,
    
    # 品質設定
    condition_on_previous_text=True,   # 使用上下文提高一致性
    max_initial_timestamp=2.0,         # 允許更長的初始靜音
    
    # 搜尋設定
    beam_size=5,
    best_of=5,
)
```

**關鍵參數說明：**

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `vad_filter` | `False` | 語音活動偵測，音樂建議關閉 |
| `condition_on_previous_text` | `True` | 參考前文提高一致性 |
| `max_initial_timestamp` | `2.0` | 允許更長的開頭靜音 |
| `beam_size` | `5` | Beam search 寬度 |
| `best_of` | `5` | 選擇最佳結果數量 |

### 生命週期管理

使用 FastAPI 的 lifespan 管理模型載入：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    
    logger.info(f"正在載入 Whisper 模型: {MODEL_SIZE}")
    
    try:
        model = WhisperModel(
            MODEL_SIZE,
            device=DEVICE,
            compute_type=COMPUTE_TYPE
        )
    except Exception as e:
        # GPU 失敗時自動切換到 CPU
        if DEVICE == "cuda":
            model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    
    yield
    
    logger.info("關閉 Whisper 服務")
```

## CUDA 設定

### 問題：libcublas.so.12 not found

如果出現 CUDA 函式庫找不到的錯誤，需要設定 `LD_LIBRARY_PATH`：

```bash
# 方法 1：使用 Ollama 的 CUDA 函式庫
export LD_LIBRARY_PATH="/usr/local/lib/ollama/cuda_v12:${LD_LIBRARY_PATH:-}"

# 方法 2：使用系統 CUDA
export LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH:-}"
```

啟動腳本 `start.sh` 已包含此設定。

### 驗證 GPU 可用性

```bash
# 檢查 NVIDIA 驅動
nvidia-smi

# 檢查 Python 中的 CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

## 與主應用整合

### Express 後端整合

```javascript
// server/app.js
const WHISPER_API = process.env.WHISPER_API || 'http://localhost:8001';

// 音檔轉錄端點
app.post('/api/transcribe', upload.single('audio'), async (req, res) => {
  const formData = new FormData();
  formData.append('audio', fs.createReadStream(req.file.path), {
    filename: req.file.originalname,
    contentType: req.file.mimetype,
  });
  formData.append('vad_filter', 'false');

  const response = await axios.post(`${WHISPER_API}/transcribe`, formData, {
    headers: formData.getHeaders(),
  });
  
  res.json(response.data);
});
```

### 前端呼叫

```typescript
async function handleAudioUpload(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('audio', file);

  const response = await fetch('/api/transcribe', {
    method: 'POST',
    body: formData,
  });
  
  const result = await response.json();
  // result.text - 轉錄文字
  // result.languages - 偵測到的語言陣列
  // result.duration - 音檔時長
}
```

## 疑難排解

### 模型下載緩慢

首次使用時會下載模型檔案（large-v3 約 3GB），可能需要等待：

```
正在載入 Whisper 模型: large-v3
```

可以先使用較小的模型測試：

```bash
WHISPER_MODEL_SIZE=base ./start.sh
```

### 記憶體不足

如果 GPU VRAM 不足，可以：

1. 使用較小的模型
2. 使用 CPU 模式
3. 降低計算精度

```bash
# 使用 CPU
WHISPER_DEVICE=cpu WHISPER_COMPUTE_TYPE=int8 ./start.sh

# 使用較低精度
WHISPER_COMPUTE_TYPE=int8_float16 ./start.sh
```

### 轉錄結果不完整

對於音樂或歌曲，確保 `vad_filter=false`：

```bash
curl -X POST http://localhost:8001/transcribe \
  -F "audio=@song.mp3" \
  -F "vad_filter=false"
```

## 參考資料

- [faster-whisper GitHub](https://github.com/SYSTRAN/faster-whisper)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [CTranslate2](https://github.com/OpenNMT/CTranslate2)
- [FastAPI 文件](https://fastapi.tiangolo.com/)
