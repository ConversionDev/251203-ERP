"""
FastAPI 서버를 사용한 YOLO 얼굴 디텍션 API
uvicorn으로 실행: uvicorn app.yolo.yolo_main:app --host 0.0.0.0 --port 8000

모든 파일 처리(업로드, 디텍션, 삭제, 조회)가 이 서버에서 수행됩니다.
"""

import os
import sys
from pathlib import Path

# 현재 파일의 디렉토리를 sys.path에 추가하여 yolo_detection 모듈을 import할 수 있도록 함
current_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(current_dir))

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from yolo_detection import detect_faces
from yolo_segmentation import detect_faces_and_segment
from yolo_poze import detect_faces_and_pose
from yolo_classification import classify_dogs_and_cats

# 데이터 디렉토리 경로 (전역)
APP_DIR = Path(__file__).resolve().parent.parent  # app/yolo -> app
DATA_DIR = APP_DIR / "data" / "yolo"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".jfif"}

# FastAPI 앱 생성
app = FastAPI(
    title="YOLO 얼굴 디텍션 API",
    description="YOLO 얼굴 전용 모델을 사용한 얼굴 디텍션 API",
    version="1.0.0",
)


def cleanup_uploaded_images():
    """업로드된 이미지 파일들을 삭제하는 함수"""
    try:
        if not DATA_DIR.exists():
            print("데이터 디렉토리가 존재하지 않습니다.")
            return

        # 디렉토리 내 모든 파일 확인
        deleted_count = 0
        for file_path in DATA_DIR.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS:
                try:
                    file_path.unlink()  # 파일 삭제
                    deleted_count += 1
                    print(f"삭제된 파일: {file_path.name}")
                except Exception as e:
                    print(f"파일 삭제 실패: {file_path.name} - {str(e)}")

        if deleted_count > 0:
            print(f"총 {deleted_count}개의 이미지 파일이 삭제되었습니다.")
        else:
            print("삭제할 이미지 파일이 없습니다.")

    except Exception as e:
        print(f"이미지 정리 중 오류 발생: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 실행되는 이벤트 핸들러"""
    print("\n" + "=" * 60)
    print("서버 종료 중... 업로드된 이미지 파일을 삭제합니다.")
    print("=" * 60)
    cleanup_uploaded_images()
    print("=" * 60)


# CORS 설정 (프론트엔드에서 접근 가능하도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:4000",  # Next.js 대체 포트
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 요청 모델
class DetectRequest(BaseModel):
    filename: str


# 응답 모델
class DetectResponse(BaseModel):
    success: bool
    message: str
    file: dict


class SegmentResponse(BaseModel):
    success: bool
    message: str
    file: dict


class PoseResponse(BaseModel):
    success: bool
    message: str
    file: dict


class ClassificationResponse(BaseModel):
    success: bool
    message: str
    file: dict


@app.get("/")
async def root():
    """헬스 체크 엔드포인트"""
    return {"message": "YOLO 얼굴 디텍션 API", "status": "running", "version": "1.0.0"}


@app.get("/health")
async def health():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy"}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    이미지 파일을 업로드하는 API 엔드포인트

    Args:
        file: 업로드할 파일 (멀티파트)

    Returns:
        업로드 결과
    """
    try:
        # 파일 확장자 확인
        file_ext = Path(file.filename).suffix.lower() if file.filename else ""
        if file_ext not in IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(IMAGE_EXTENSIONS)}",
            )

        # 파일 크기 제한 (100MB)
        max_size = 100 * 1024 * 1024
        contents = await file.read()
        if len(contents) > max_size:
            raise HTTPException(
                status_code=400, detail="파일 크기는 100MB를 초과할 수 없습니다."
            )

        # 디렉토리가 없으면 생성
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # 파일 저장
        file_path = DATA_DIR / file.filename
        with open(file_path, "wb") as f:
            f.write(contents)

        print(f"✓ 파일 업로드 완료: {file.filename}")

        return {
            "success": True,
            "message": "파일이 성공적으로 업로드되었습니다.",
            "file": {
                "name": file.filename,
                "size": len(contents),
                "type": file.content_type,
                "path": str(file_path),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ 파일 업로드 실패: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"파일 업로드 중 오류가 발생했습니다: {str(e)}"
        )


@app.get("/api/images")
async def list_images():
    """
    업로드된 이미지 목록을 조회하는 API 엔드포인트

    Returns:
        이미지 파일 목록
    """
    try:
        if not DATA_DIR.exists():
            return {"success": True, "images": []}

        images = []
        for file_path in DATA_DIR.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS:
                images.append(
                    {
                        "name": file_path.name,
                        "size": file_path.stat().st_size,
                        "isDetected": "_detected" in file_path.stem,
                    }
                )

        return {"success": True, "images": images}

    except Exception as e:
        print(f"✗ 이미지 목록 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"이미지 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@app.get("/api/images/{filename}")
async def get_image(filename: str):
    """
    이미지 파일을 조회하는 API 엔드포인트

    Args:
        filename: 조회할 파일명

    Returns:
        이미지 파일
    """
    try:
        file_path = DATA_DIR / filename

        if not file_path.exists():
            raise HTTPException(
                status_code=404, detail=f"파일을 찾을 수 없습니다: {filename}"
            )

        # 이미지 파일인지 확인
        if file_path.suffix.lower() not in IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=400, detail="이미지 파일만 조회할 수 있습니다."
            )

        return FileResponse(file_path)

    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ 이미지 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"이미지 조회 중 오류가 발생했습니다: {str(e)}"
        )


@app.delete("/api/delete/{filename}")
async def delete_file(filename: str):
    """
    업로드된 이미지 파일을 삭제하는 API 엔드포인트

    Args:
        filename: 삭제할 파일명 (URL 디코딩됨)

    Returns:
        삭제 결과
    """
    try:
        from urllib.parse import unquote

        # URL 인코딩된 파일명 디코딩
        decoded_filename = unquote(filename)
        print(f"파일 삭제 요청: {decoded_filename} (원본: {filename})")

        # 파일 경로 생성
        file_path = DATA_DIR / decoded_filename

        # 파일 존재 확인
        if not file_path.exists():
            print(f"파일을 찾을 수 없음: {file_path}")
            raise HTTPException(
                status_code=404, detail=f"파일을 찾을 수 없습니다: {decoded_filename}"
            )

        # 이미지 파일인지 확인
        if file_path.suffix.lower() not in IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=400, detail="이미지 파일만 삭제할 수 있습니다."
            )

        # 원본 파일 삭제
        file_path.unlink()
        print(f"✓ 파일 삭제 완료: {decoded_filename}")

        # 디텍션된 이미지도 함께 삭제 (있는 경우)
        if "_detected" not in file_path.stem:
            # 원본 파일이면 디텍션된 파일도 찾아서 삭제
            name_without_ext = file_path.stem
            ext = file_path.suffix
            detected_file_path = DATA_DIR / f"{name_without_ext}_detected{ext}"
            if detected_file_path.exists():
                detected_file_path.unlink()
                print(f"✓ 디텍션 파일 삭제 완료: {detected_file_path.name}")
            else:
                print(f"디텍션 파일이 없음: {detected_file_path}")

        return {
            "success": True,
            "message": f"파일이 삭제되었습니다: {decoded_filename}",
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ 파일 삭제 실패: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"파일 삭제 중 오류가 발생했습니다: {str(e)}"
        )


@app.delete("/api/delete-all")
async def delete_all_files():
    """
    업로드된 모든 이미지 파일을 삭제하는 API 엔드포인트

    Returns:
        삭제 결과
    """
    try:
        if not DATA_DIR.exists():
            return {
                "success": True,
                "message": "삭제할 파일이 없습니다.",
                "deletedCount": 0,
            }

        # 디렉토리 내 모든 이미지 파일 삭제
        deleted_count = 0
        for file_path in DATA_DIR.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    print(f"✓ 파일 삭제 완료: {file_path.name}")
                except Exception as e:
                    print(f"✗ 파일 삭제 실패: {file_path.name} - {str(e)}")

        return {
            "success": True,
            "message": f"총 {deleted_count}개의 파일이 삭제되었습니다.",
            "deletedCount": deleted_count,
        }

    except Exception as e:
        print(f"✗ 전체 파일 삭제 실패: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"파일 삭제 중 오류가 발생했습니다: {str(e)}"
        )


@app.post("/api/detect", response_model=DetectResponse)
async def detect_faces_api(request: DetectRequest):
    """
    이미지 파일에 대해 얼굴 디텍션을 수행하는 API 엔드포인트

    Args:
        request: DetectRequest 모델 (filename 포함)

    Returns:
        DetectResponse: 디텍션 결과 (detectedImage, faceCount)
    """
    try:
        filename = request.filename

        if not filename:
            raise HTTPException(status_code=400, detail="파일명이 제공되지 않았습니다.")

        # 파일 경로 생성
        file_path = DATA_DIR / filename

        # 파일 존재 확인
        if not file_path.exists():
            raise HTTPException(
                status_code=404, detail=f"파일을 찾을 수 없습니다: {filename}"
            )

        # 이미지 파일인지 확인
        if file_path.suffix.lower() not in IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=400, detail="이미지 파일만 디텍션할 수 있습니다."
            )

        # 디텍션 이미지가 아닌지 확인 (무한 루프 방지)
        if "_detected" in file_path.stem:
            raise HTTPException(status_code=400, detail="이미 디텍션된 이미지입니다.")

        # 얼굴 디텍션 수행
        print(f"얼굴 디텍션 시작: {filename}")
        output_path, face_count = detect_faces(str(file_path))

        # 결과 이미지 파일명만 추출
        detected_image_filename = os.path.basename(output_path)

        print(f"✓ 디텍션 완료!")
        print(f"  원본: {filename}")
        print(f"  결과: {detected_image_filename}")
        print(f"  탐지된 얼굴 수: {face_count}개")

        return DetectResponse(
            success=True,
            message="디텍션이 완료되었습니다.",
            file={
                "name": filename,
                "detectedImage": detected_image_filename,
                "faceCount": face_count,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ 디텍션 실패: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"디텍션 중 오류가 발생했습니다: {str(e)}"
        )


@app.post("/api/segment", response_model=SegmentResponse)
async def segment_faces_api(request: DetectRequest):
    """
    이미지 파일에 대해 얼굴 디텍션 및 세그먼테이션을 수행하는 API 엔드포인트

    Args:
        request: DetectRequest 모델 (filename 포함)

    Returns:
        SegmentResponse: 세그먼테이션 결과 (segmentedImage, faceCount)
    """
    try:
        filename = request.filename

        if not filename:
            raise HTTPException(status_code=400, detail="파일명이 제공되지 않았습니다.")

        # 파일 경로 생성
        file_path = DATA_DIR / filename

        # 파일 존재 확인
        if not file_path.exists():
            raise HTTPException(
                status_code=404, detail=f"파일을 찾을 수 없습니다: {filename}"
            )

        # 이미지 파일인지 확인
        if file_path.suffix.lower() not in IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=400, detail="이미지 파일만 세그먼테이션할 수 있습니다."
            )

        # 세그먼트 이미지가 아닌지 확인 (무한 루프 방지)
        if "_segmented" in file_path.stem:
            raise HTTPException(status_code=400, detail="이미 세그먼트된 이미지입니다.")

        # 기존 세그먼트 파일이 있으면 삭제 (재생성을 위해)
        image_name = os.path.basename(filename)
        name_without_ext = os.path.splitext(image_name)[0]
        ext = os.path.splitext(image_name)[1]
        existing_segmented = DATA_DIR / f"{name_without_ext}_segmented{ext}"
        if existing_segmented.exists():
            print(f"기존 세그먼트 파일 삭제: {existing_segmented.name}")
            existing_segmented.unlink()

        # 얼굴 디텍션 및 세그먼테이션 수행
        print(f"얼굴 디텍션 및 세그먼테이션 시작: {filename}")
        output_path, face_count, avg_confidence = detect_faces_and_segment(
            str(file_path)
        )

        # 결과 이미지 파일명만 추출
        segmented_image_filename = os.path.basename(output_path)

        print(f"✓ 세그먼테이션 완료!")
        print(f"  원본: {filename}")
        print(f"  결과: {segmented_image_filename}")
        print(f"  탐지된 얼굴 수: {face_count}개")
        print(f"  평균 confidence: {avg_confidence:.2f}")

        return SegmentResponse(
            success=True,
            message="세그먼테이션이 완료되었습니다.",
            file={
                "name": filename,
                "segmentedImage": segmented_image_filename,
                "faceCount": face_count,
                "confidence": avg_confidence,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ 세그먼테이션 실패: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"세그먼테이션 중 오류가 발생했습니다: {str(e)}"
        )


@app.post("/api/pose", response_model=PoseResponse)
async def pose_estimation_api(request: DetectRequest):
    """
    이미지 파일에 대해 얼굴 디텍션 및 포즈 추정을 수행하는 API 엔드포인트

    Args:
        request: DetectRequest 모델 (filename 포함)

    Returns:
        PoseResponse: 포즈 추정 결과 (poseImage, faceCount)
    """
    try:
        filename = request.filename

        if not filename:
            raise HTTPException(status_code=400, detail="파일명이 제공되지 않았습니다.")

        # 파일 경로 생성
        file_path = DATA_DIR / filename

        # 파일 존재 확인
        if not file_path.exists():
            raise HTTPException(
                status_code=404, detail=f"파일을 찾을 수 없습니다: {filename}"
            )

        # 이미지 파일인지 확인
        if file_path.suffix.lower() not in IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=400, detail="이미지 파일만 포즈 추정할 수 있습니다."
            )

        # 포즈 이미지가 아닌지 확인 (무한 루프 방지)
        if "_pose" in file_path.stem:
            raise HTTPException(
                status_code=400, detail="이미 포즈 추정된 이미지입니다."
            )

        # 기존 포즈 파일이 있으면 삭제 (재생성을 위해)
        image_name = os.path.basename(filename)
        name_without_ext = os.path.splitext(image_name)[0]
        ext = os.path.splitext(image_name)[1]
        existing_pose = DATA_DIR / f"{name_without_ext}_pose{ext}"
        if existing_pose.exists():
            print(f"기존 포즈 파일 삭제: {existing_pose.name}")
            existing_pose.unlink()

        # 얼굴 디텍션 및 포즈 추정 수행
        print(f"얼굴 디텍션 및 포즈 추정 시작: {filename}")
        output_path, face_count, avg_confidence = detect_faces_and_pose(str(file_path))

        # 결과 이미지 파일명만 추출
        pose_image_filename = os.path.basename(output_path)

        print(f"✓ 포즈 추정 완료!")
        print(f"  원본: {filename}")
        print(f"  결과: {pose_image_filename}")
        print(f"  탐지된 얼굴 수: {face_count}개")
        print(f"  평균 confidence: {avg_confidence:.2f}")

        return PoseResponse(
            success=True,
            message="포즈 추정이 완료되었습니다.",
            file={
                "name": filename,
                "poseImage": pose_image_filename,
                "faceCount": face_count,
                "confidence": avg_confidence,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ 포즈 추정 실패: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"포즈 추정 중 오류가 발생했습니다: {str(e)}"
        )


@app.post("/api/classify", response_model=ClassificationResponse)
async def classify_image_api(request: DetectRequest):
    """
    이미지 파일에 대해 개와 고양이 분류를 수행하는 API 엔드포인트

    Args:
        request: DetectRequest 모델 (filename 포함)

    Returns:
        ClassificationResponse: 분류 결과 (classifiedImage, predictedClass, confidence)
    """
    try:
        filename = request.filename

        if not filename:
            raise HTTPException(status_code=400, detail="파일명이 제공되지 않았습니다.")

        # 파일 경로 생성
        file_path = DATA_DIR / filename

        # 파일 존재 확인
        if not file_path.exists():
            raise HTTPException(
                status_code=404, detail=f"파일을 찾을 수 없습니다: {filename}"
            )

        # 이미지 파일인지 확인
        if file_path.suffix.lower() not in IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=400, detail="이미지 파일만 분류할 수 있습니다."
            )

        # 분류 이미지가 아닌지 확인 (무한 루프 방지)
        if "_classified" in file_path.stem:
            raise HTTPException(status_code=400, detail="이미 분류된 이미지입니다.")

        # 기존 분류 파일이 있으면 삭제 (재생성을 위해)
        image_name = os.path.basename(filename)
        name_without_ext = os.path.splitext(image_name)[0]
        ext = os.path.splitext(image_name)[1]
        existing_classified = DATA_DIR / f"{name_without_ext}_classified{ext}"
        if existing_classified.exists():
            print(f"기존 분류 파일 삭제: {existing_classified.name}")
            existing_classified.unlink()

        # 개와 고양이 분류 수행
        print(f"개와 고양이 분류 시작: {filename}")
        output_path, classification_result = classify_dogs_and_cats(str(file_path))

        # 결과 이미지 파일명만 추출
        classified_image_filename = os.path.basename(output_path)

        print(f"✓ 분류 완료!")
        print(f"  원본: {filename}")
        print(f"  결과: {classified_image_filename}")
        print(f"  개: {classification_result.get('dog_count', 0)}마리")
        print(f"  고양이: {classification_result.get('cat_count', 0)}마리")
        print(f"  총: {classification_result.get('total_count', 0)}마리")
        print(
            f"  평균 Confidence: {classification_result.get('average_confidence', 0.0):.2f}"
        )

        return ClassificationResponse(
            success=True,
            message="분류가 완료되었습니다.",
            file={
                "name": filename,
                "classifiedImage": classified_image_filename,
                "dogCount": classification_result.get("dog_count", 0),
                "catCount": classification_result.get("cat_count", 0),
                "totalCount": classification_result.get("total_count", 0),
                "confidence": classification_result.get("average_confidence", 0.0),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ 분류 실패: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"분류 중 오류가 발생했습니다: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("YOLO 얼굴 디텍션 API 서버 시작")
    print("=" * 60)
    print(f"서버 주소: http://localhost:8000")
    print(f"API 문서: http://localhost:8000/docs")
    print("=" * 60)
    print("\n종료하려면 Ctrl+C를 누르세요.\n")

    uvicorn.run(
        "yolo_main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
