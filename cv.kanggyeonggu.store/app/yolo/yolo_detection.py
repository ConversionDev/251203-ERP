import os
import cv2
from pathlib import Path
from typing import Optional, Tuple


def detect_faces(image_path: str, output_path: Optional[str] = None) -> Tuple[str, int]:
    """
    YOLO 얼굴 전용 모델을 사용하여 이미지에서 얼굴을 직접 디텍션하는 함수

    Args:
        image_path: 입력 이미지 경로
        output_path: 결과 이미지 저장 경로 (None이면 자동 생성)

    Returns:
        Tuple[str, int]: (결과 이미지 경로, 탐지된 얼굴 수)
    """
    try:
        from ultralytics import YOLO

        # 현재 스크립트 위치 기준으로 경로 설정
        current_dir = Path(__file__).parent.resolve()

        # 프로젝트 루트로 이동하여 모델 경로 찾기
        # current_dir.parent = cv.kanggyeonggu.store/app
        # current_dir.parent.parent = cv.kanggyeonggu.store
        project_root = current_dir.parent.parent

        # 얼굴 전용 모델만 사용
        face_model_path = project_root / "yolov8n-face-lindevs.pt"

        # 얼굴 모델이 없으면 오류
        if not face_model_path.exists():
            raise FileNotFoundError(
                f"얼굴 전용 모델을 찾을 수 없습니다: {face_model_path}\n"
                f"yolov8n-face-lindevs.pt 파일을 프로젝트 루트에 배치해주세요."
            )

        # YOLO 얼굴 전용 모델 로드
        model = YOLO(str(face_model_path))
        print("얼굴 전용 모델 사용: yolov8n-face-lindevs.pt")

        # 이미지 파일 존재 확인
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

        # 이미지 로드
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"이미지를 읽을 수 없습니다: {image_path}")

        # 얼굴 탐지 수행
        print("얼굴 탐지 중...")
        results = model(image_path, conf=0.25)  # 얼굴 직접 탐지

        # 결과 이미지 경로 설정 (원본 이미지와 같은 디렉토리에 저장)
        if output_path is None:
            image_dir = os.path.dirname(image_path)
            image_name = os.path.basename(image_path)
            name_without_ext = os.path.splitext(image_name)[0]
            ext = os.path.splitext(image_name)[1]
            # 원본 파일명에 _detected를 추가하여 같은 디렉토리(app/data/yolo)에 저장
            # 예: "다운로드.jfif" -> "다운로드_detected.jfif"
            # 예: "1766717096673-다운로드.jfif" -> "1766717096673-다운로드_detected.jfif"
            output_path = os.path.join(image_dir, f"{name_without_ext}_detected{ext}")
            print(f"디텍션 결과 이미지 저장 경로: {output_path}")

        # 결과 처리 - 얼굴 직접 탐지 및 정확도 표시
        face_count = 0
        annotated_img = img.copy()  # 원본 이미지 복사

        for result in results:
            if len(result.boxes) > 0:
                # YOLO가 탐지한 얼굴들 직접 사용
                for box in result.boxes:
                    # 바운딩 박스 좌표 추출 (얼굴)
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                    # YOLO 신뢰도
                    conf = float(box.conf[0])

                    # 바운딩 박스 그리기 (얼굴)
                    color = (0, 255, 0)  # 초록색
                    thickness = 3
                    cv2.rectangle(
                        annotated_img,
                        (x1, y1),
                        (x2, y2),
                        color,
                        thickness,
                    )

                    # 라벨과 정확도 표시 (소수점 형식)
                    label = f"face {conf:.2f}"
                    label_size, _ = cv2.getTextSize(
                        label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
                    )
                    label_y = max(y1 - 10, label_size[1] + 10)

                    # 라벨 배경 그리기
                    cv2.rectangle(
                        annotated_img,
                        (x1, label_y - label_size[1] - 5),
                        (x1 + label_size[0], label_y + 5),
                        color,
                        -1,
                    )

                    # 라벨 텍스트 그리기
                    cv2.putText(
                        annotated_img,
                        label,
                        (x1, label_y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 255, 255),
                        2,
                    )

                    face_count += 1
                    print(f"  - 얼굴 탐지: {conf:.2f} (좌표: {x1}, {y1}, {x2}, {y2})")

        # 탐지 정보 출력
        print(f"\n탐지된 얼굴 수: {face_count}")

        # 결과 이미지 저장
        cv2.imwrite(output_path, annotated_img)
        print(f"결과 이미지 저장: {output_path}")

        return output_path, face_count

    except ImportError:
        raise ImportError(
            "YOLO가 설치되지 않았습니다. pip install ultralytics를 실행하세요."
        )
    except Exception as e:
        raise Exception(f"얼굴 디텍션 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    # 테스트 코드
    current_dir = Path(__file__).parent.resolve()
    app_dir = current_dir.parent
    data_dir = app_dir / "data" / "yolo"

    # 테스트 이미지 경로
    test_image = data_dir / "family.jpg"

    if test_image.exists():
        print(f"테스트 이미지: {test_image}")
        output_path, face_count = detect_faces(str(test_image))
        print(f"결과 이미지: {output_path}")
        print(f"탐지된 얼굴 수: {face_count}")
    else:
        print(f"테스트 이미지를 찾을 수 없습니다: {test_image}")
