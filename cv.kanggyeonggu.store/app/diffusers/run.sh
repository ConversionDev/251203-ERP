#!/bin/bash
# Diffusion 서버 실행 스크립트
cd "$(dirname "$0")/../.."  # cv.kanggyeonggu.store로 이동
uvicorn app.diffusers.main:app --host 0.0.0.0 --port 8000 --reload

