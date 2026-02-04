#!/bin/bash
# Faster-Whisper 服務啟動腳本

# 切換到腳本所在目錄
cd "$(dirname "$0")"

# 啟動虛擬環境
source .venv/bin/activate

# CUDA 函式庫路徑（cuBLAS、cuDNN）
export LD_LIBRARY_PATH="/usr/local/lib/ollama/cuda_v12:${LD_LIBRARY_PATH:-}"

# 環境變數設定（可依需求調整）
export WHISPER_MODEL_SIZE="${WHISPER_MODEL_SIZE:-large-v3}"
export WHISPER_DEVICE="${WHISPER_DEVICE:-cuda}"
export WHISPER_COMPUTE_TYPE="${WHISPER_COMPUTE_TYPE:-float16}"
export WHISPER_PORT="${WHISPER_PORT:-8001}"
export WHISPER_HOST="${WHISPER_HOST:-0.0.0.0}"

echo "=========================================="
echo "Faster-Whisper 語音轉錄服務"
echo "=========================================="
echo "模型: $WHISPER_MODEL_SIZE"
echo "裝置: $WHISPER_DEVICE"
echo "計算類型: $WHISPER_COMPUTE_TYPE"
echo "服務位址: http://$WHISPER_HOST:$WHISPER_PORT"
echo "=========================================="

# 啟動服務
python main.py
