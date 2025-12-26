#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
이미지 파일 경로를 받아서 얼굴 디텍션을 수행하는 스크립트
명령줄 인자로 이미지 경로를 받음
"""
import sys
import os
from pathlib import Path

# 현재 스크립트의 디렉토리를 sys.path에 추가
current_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(current_dir))

from yolo_detection import detect_faces

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("ERROR:Image path required")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"ERROR:File not found: {image_path}")
        sys.exit(1)
    
    try:
        output_path, face_count = detect_faces(image_path)
        print(f"DETECTED:{output_path}:{face_count}")
    except Exception as e:
        print(f"ERROR:{str(e)}")
        sys.exit(1)

