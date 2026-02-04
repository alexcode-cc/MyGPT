"""
Faster-Whisper 語音轉錄服務
使用 FastAPI 提供 REST API 接口
"""
import os
import re
import tempfile
import logging
import unicodedata
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from faster_whisper import WhisperModel

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def detect_languages_in_text(text: str) -> List[str]:
    """
    分析文字中包含的語言
    基於 Unicode 字符範圍判斷
    """
    languages = set()
    
    if not text:
        return []
    
    # 定義字符範圍對應的語言
    for char in text:
        if char.isspace() or char in '.,!?;:\'"()[]{}0123456789-':
            continue
            
        # 取得字符的 Unicode 名稱
        try:
            name = unicodedata.name(char, '')
        except ValueError:
            continue
        
        # 日語（平假名、片假名）
        if 'HIRAGANA' in name or 'KATAKANA' in name:
            languages.add('ja')
        # 中文（CJK 漢字）- 注意日語也使用漢字
        elif 'CJK' in name:
            # 如果已有日語，則漢字可能是日語的一部分
            if 'ja' not in languages:
                languages.add('zh')
        # 韓語
        elif 'HANGUL' in name:
            languages.add('ko')
        # 阿拉伯語
        elif 'ARABIC' in name:
            languages.add('ar')
        # 泰語
        elif 'THAI' in name:
            languages.add('th')
        # 俄語（西里爾字母）
        elif 'CYRILLIC' in name:
            languages.add('ru')
        # 拉丁字母（英語、法語、德語等）
        elif 'LATIN' in name:
            languages.add('en')  # 預設為英語，實際可能是其他歐洲語言
    
    # 如果同時有中文和日語標記，且有假名，則移除中文（因為是日語中的漢字）
    if 'ja' in languages and 'zh' in languages:
        languages.discard('zh')
    
    return sorted(list(languages))

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
    task: str = Form("transcribe"),  # transcribe 或 translate
    vad_filter: bool = Form(False),  # 預設關閉 VAD（對音樂更友好）
    word_timestamps: bool = Form(False)
):
    """
    轉錄音檔為文字
    
    - **audio**: 音訊檔案 (MP3, WAV, M4A, FLAC, OGG 等)
    - **language**: 語言代碼 (可選，如 'zh', 'en', 'ja')，不指定則自動偵測
    - **task**: 任務類型，'transcribe' 轉錄或 'translate' 翻譯成英文
    - **vad_filter**: 是否啟用 VAD 過濾（音樂建議關閉）
    - **word_timestamps**: 是否返回單詞級時間戳
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
        
        logger.info(f"開始轉錄: {audio.filename}, 大小: {len(content)} bytes, VAD: {vad_filter}")
        
        # 執行轉錄 - 針對音樂和多語言優化
        segments, info = model.transcribe(
            tmp_path,
            language=language,
            task=task,
            beam_size=5,
            best_of=5,
            # VAD 設定 - 對音樂關閉以避免過濾掉歌聲
            vad_filter=vad_filter,
            vad_parameters=dict(
                min_silence_duration_ms=300,  # 更短的靜音判定
                speech_pad_ms=400,  # 語音前後保留更多
                threshold=0.3  # 更低的閾值，更容易判定為語音
            ) if vad_filter else None,
            # 條件設定 - 提高轉錄品質
            condition_on_previous_text=True,  # 使用上下文提高一致性
            compression_ratio_threshold=2.4,
            log_prob_threshold=-1.0,
            no_speech_threshold=0.6,
            # 時間戳
            word_timestamps=word_timestamps,
            # 允許更長的初始時間戳（對音樂很重要）
            max_initial_timestamp=2.0,
        )
        
        # 收集所有片段
        text_segments = []
        full_text = []
        
        for segment in segments:
            seg_data = {
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": segment.text.strip()
            }
            if word_timestamps and segment.words:
                seg_data["words"] = [
                    {
                        "word": w.word,
                        "start": round(w.start, 2),
                        "end": round(w.end, 2),
                        "probability": round(w.probability, 3)
                    }
                    for w in segment.words
                ]
            text_segments.append(seg_data)
            full_text.append(segment.text.strip())
        
        result_text = " ".join(full_text)
        
        # 分析文字中包含的語言
        detected_languages = detect_languages_in_text(result_text)
        
        logger.info(f"轉錄完成: Whisper偵測={info.language}, 文字分析語言={detected_languages}, "
                   f"時長={info.duration:.1f}秒, 片段數={len(text_segments)}")
        
        return {
            "text": result_text,
            "language": info.language,  # Whisper 偵測的主要語言
            "languages": detected_languages,  # 文字中實際包含的語言
            "language_probability": round(info.language_probability, 3),
            "duration": round(info.duration, 2),
            "duration_after_vad": round(info.duration_after_vad, 2),
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
