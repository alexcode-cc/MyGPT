"""
Faster-Whisper 語音轉錄服務
使用 FastAPI 提供 REST API 接口
"""
import os
import tempfile
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from faster_whisper import WhisperModel

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全域模型實例
model: Optional[WhisperModel] = None

# 模型設定
MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "large-v3")
DEVICE = os.getenv("WHISPER_DEVICE", "cuda")  # cuda 或 cpu
COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "float16")  # float16, int8_float16, int8


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    global model
    
    logger.info(f"正在載入 Whisper 模型: {MODEL_SIZE}")
    logger.info(f"裝置: {DEVICE}, 計算類型: {COMPUTE_TYPE}")
    
    try:
        model = WhisperModel(
            MODEL_SIZE,
            device=DEVICE,
            compute_type=COMPUTE_TYPE
        )
        logger.info("Whisper 模型載入完成")
    except Exception as e:
        logger.error(f"模型載入失敗: {e}")
        # 嘗試使用 CPU 作為備用
        if DEVICE == "cuda":
            logger.info("嘗試使用 CPU 作為備用...")
            model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
            logger.info("已使用 CPU 模式載入模型")
    
    yield
    
    # 清理資源
    logger.info("關閉 Whisper 服務")


app = FastAPI(
    title="Faster-Whisper 語音轉錄服務",
    description="使用 faster-whisper 進行語音轉文字",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """健康檢查"""
    return {
        "status": "ok",
        "service": "faster-whisper",
        "model": MODEL_SIZE,
        "device": DEVICE
    }


@app.get("/health")
async def health():
    """健康檢查端點"""
    if model is None:
        raise HTTPException(status_code=503, detail="模型未載入")
    return {"status": "healthy", "model_loaded": True}


@app.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None),
    task: str = Form("transcribe")  # transcribe 或 translate
):
    """
    轉錄音檔為文字
    
    - **audio**: 音訊檔案 (MP3, WAV, M4A, FLAC, OGG 等)
    - **language**: 語言代碼 (可選，如 'zh', 'en', 'ja')，不指定則自動偵測
    - **task**: 任務類型，'transcribe' 轉錄或 'translate' 翻譯成英文
    """
    if model is None:
        raise HTTPException(status_code=503, detail="模型未載入")
    
    # 檢查檔案類型
    content_type = audio.content_type or ""
    if not content_type.startswith("audio/") and not audio.filename.endswith(
        ('.mp3', '.wav', '.m4a', '.flac', '.ogg', '.webm', '.mp4')
    ):
        raise HTTPException(status_code=400, detail="請上傳音訊檔案")
    
    # 儲存到暫存檔案
    suffix = os.path.splitext(audio.filename)[1] if audio.filename else ".wav"
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        logger.info(f"開始轉錄: {audio.filename}, 大小: {len(content)} bytes")
        
        # 執行轉錄
        segments, info = model.transcribe(
            tmp_path,
            language=language,
            task=task,
            beam_size=5,
            vad_filter=True,  # 使用 VAD 過濾靜音
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        # 收集所有片段
        text_segments = []
        full_text = []
        
        for segment in segments:
            text_segments.append({
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": segment.text.strip()
            })
            full_text.append(segment.text.strip())
        
        result_text = " ".join(full_text)
        
        logger.info(f"轉錄完成: 偵測語言={info.language}, 機率={info.language_probability:.2f}")
        
        return {
            "text": result_text,
            "language": info.language,
            "language_probability": round(info.language_probability, 3),
            "duration": round(info.duration, 2),
            "segments": text_segments
        }
        
    except Exception as e:
        logger.error(f"轉錄失敗: {e}")
        raise HTTPException(status_code=500, detail=f"轉錄失敗: {str(e)}")
    
    finally:
        # 清理暫存檔案
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.get("/models")
async def list_models():
    """列出可用的模型大小"""
    return {
        "available_models": [
            {"name": "tiny", "parameters": "39M", "vram": "~1GB"},
            {"name": "base", "parameters": "74M", "vram": "~1GB"},
            {"name": "small", "parameters": "244M", "vram": "~2GB"},
            {"name": "medium", "parameters": "769M", "vram": "~5GB"},
            {"name": "large-v2", "parameters": "1550M", "vram": "~10GB"},
            {"name": "large-v3", "parameters": "1550M", "vram": "~10GB"},
            {"name": "turbo", "parameters": "809M", "vram": "~6GB"},
        ],
        "current_model": MODEL_SIZE,
        "device": DEVICE,
        "compute_type": COMPUTE_TYPE
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("WHISPER_PORT", "8001"))
    host = os.getenv("WHISPER_HOST", "0.0.0.0")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
