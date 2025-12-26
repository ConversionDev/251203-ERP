import os
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple


def detect_faces_and_segment(
    image_path: str, output_path: Optional[str] = None
) -> Tuple[str, int, float]:
    """
    YOLO 얼굴 전용 모델로 얼굴을 감지하고, 감지된 얼굴 영역에 대해 YOLO segmentation을 수행하는 함수

    Args:
        image_path: 입력 이미지 경로
        output_path: 결과 이미지 저장 경로 (None이면 자동 생성)

    Returns:
        Tuple[str, int, float]: (결과 이미지 경로, 탐지된 얼굴 수, 평균 confidence)
    """
    try:
        from ultralytics import YOLO

        # 현재 스크립트 위치 기준으로 경로 설정
        current_dir = Path(__file__).parent.resolve()
        project_root = current_dir.parent.parent  # cv.kanggyeonggu.store

        # 얼굴 전용 모델 경로
        face_model_path = project_root / "yolov8n-face-lindevs.pt"

        # Segmentation 모델 경로 (yolo11n-seg.pt 사용)
        seg_model_path = project_root / "yolo11n-seg.pt"

        # 모델 파일 존재 확인
        if not face_model_path.exists():
            raise FileNotFoundError(
                f"얼굴 전용 모델을 찾을 수 없습니다: {face_model_path}\n"
                f"yolov8n-face-lindevs.pt 파일을 프로젝트 루트에 배치해주세요."
            )

        if not seg_model_path.exists():
            raise FileNotFoundError(
                f"Segmentation 모델을 찾을 수 없습니다: {seg_model_path}\n"
                f"yolo11n-seg.pt 파일을 프로젝트 루트에 배치해주세요."
            )

        # 이미지 파일 존재 확인
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

        # 이미지 로드
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"이미지를 읽을 수 없습니다: {image_path}")

        img_height, img_width = img.shape[:2]

        # 1단계: 얼굴 감지
        print("=" * 60)
        print("1단계: 얼굴 감지 시작")
        print("=" * 60)
        face_model = YOLO(str(face_model_path))
        print("얼굴 전용 모델 사용: yolov8n-face-lindevs.pt")

        face_results = face_model(image_path, conf=0.25)

        # 얼굴 영역 추출
        face_regions = []
        face_count = 0

        for result in face_results:
            if len(result.boxes) > 0:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    conf = float(box.conf[0])

                    # 이미지 경계 내로 제한
                    x1 = max(0, min(x1, img_width))
                    y1 = max(0, min(y1, img_height))
                    x2 = max(0, min(x2, img_width))
                    y2 = max(0, min(y2, img_height))

                    face_regions.append({"bbox": (x1, y1, x2, y2), "conf": conf})
                    face_count += 1
                    print(f"  - 얼굴 탐지: {conf:.2f} (좌표: {x1}, {y1}, {x2}, {y2})")

        print(f"\n탐지된 얼굴 수: {face_count}")

        if face_count == 0:
            print("얼굴이 탐지되지 않았습니다. 원본 이미지만 저장합니다.")
            # 결과 이미지 경로 설정
            if output_path is None:
                image_dir = os.path.dirname(image_path)
                image_name = os.path.basename(image_path)
                name_without_ext = os.path.splitext(image_name)[0]
                ext = os.path.splitext(image_name)[1]
                output_path = os.path.join(
                    image_dir, f"{name_without_ext}_segmented{ext}"
                )

            cv2.imwrite(output_path, img)
            print(f"결과 이미지 저장: {output_path}")
            return output_path, 0, 0.0

        # 2단계: Segmentation 수행 (얼굴 영역에만)
        print("\n" + "=" * 60)
        print("2단계: Segmentation 시작 (얼굴 영역에만 적용)")
        print("=" * 60)
        seg_model = YOLO(str(seg_model_path))
        print("Segmentation 모델 사용: yolo11n-seg.pt")

        # 결과 이미지 준비
        annotated_img = img.copy()

        # 전체 confidence 추적
        all_confidences = []

        # 각 얼굴 영역에 대해 segmentation 수행
        for face_idx, face_region in enumerate(face_regions):
            x1, y1, x2, y2 = face_region["bbox"]
            face_conf = face_region["conf"]

            print(f"\n얼굴 {face_idx + 1} 처리 중... (좌표: {x1}, {y1}, {x2}, {y2})")

            # 얼굴 영역만 crop (약간의 여유 공간 추가)
            padding = 20
            crop_x1 = max(0, x1 - padding)
            crop_y1 = max(0, y1 - padding)
            crop_x2 = min(img_width, x2 + padding)
            crop_y2 = min(img_height, y2 + padding)

            face_crop = img[crop_y1:crop_y2, crop_x1:crop_x2]

            if face_crop.size == 0:
                print(f"  - 얼굴 {face_idx + 1} 영역이 유효하지 않습니다. 건너뜁니다.")
                continue

            # 얼굴 영역에만 segmentation 수행
            seg_results = seg_model(face_crop, conf=0.25, task="segment")

            # 얼굴 영역 내에서 segmentation 마스크 찾기
            for result in seg_results:
                # Segmentation 마스크가 있는 경우
                if result.masks is not None and len(result.masks) > 0:
                    masks_data = result.masks.data.cpu().numpy()

                    # boxes에서 confidence 추출
                    boxes_data = result.boxes if result.boxes is not None else None

                    for mask_idx, mask in enumerate(masks_data):
                        # 해당 마스크의 confidence 추출
                        seg_confidence = 0.0
                        if boxes_data is not None and len(boxes_data) > mask_idx:
                            seg_confidence = float(boxes_data[mask_idx].conf[0])
                            all_confidences.append(seg_confidence)
                            print(
                                f"  - 마스크 {mask_idx + 1} confidence: {seg_confidence:.2f}"
                            )
                        # 마스크를 얼굴 crop 영역 크기로 변환
                        crop_height, crop_width = face_crop.shape[:2]
                        if mask.shape != (crop_height, crop_width):
                            mask_crop = cv2.resize(
                                mask,
                                (crop_width, crop_height),
                                interpolation=cv2.INTER_NEAREST,
                            )
                        else:
                            mask_crop = mask

                        # 마스크를 얼굴 영역 크기로 리사이즈 (crop 영역에서 얼굴 영역만 추출)
                        # crop 영역 내에서 얼굴 영역의 상대적 위치 계산
                        face_in_crop_x1 = x1 - crop_x1
                        face_in_crop_y1 = y1 - crop_y1
                        face_in_crop_x2 = x2 - crop_x1
                        face_in_crop_y2 = y2 - crop_y1

                        # 얼굴 영역만 추출
                        face_mask_crop = mask_crop[
                            max(0, face_in_crop_y1) : min(crop_height, face_in_crop_y2),
                            max(0, face_in_crop_x1) : min(crop_width, face_in_crop_x2),
                        ]

                        # 얼굴 영역 크기로 리사이즈
                        face_height = y2 - y1
                        face_width = x2 - x1
                        if face_mask_crop.shape != (face_height, face_width):
                            face_mask_resized = cv2.resize(
                                face_mask_crop,
                                (face_width, face_height),
                                interpolation=cv2.INTER_NEAREST,
                            )
                        else:
                            face_mask_resized = face_mask_crop

                        # 얼굴 영역 내에서만 마스크 적용 (정확한 얼굴 영역만)
                        mask_coverage = np.sum(face_mask_resized > 0.5) / (
                            face_mask_resized.size + 1e-6
                        )

                        if (
                            mask_coverage > 0.1
                        ):  # 얼굴 영역의 10% 이상이 마스크로 커버되는 경우
                            # 얼굴 영역에만 segmentation 마스크 그리기
                            mask_binary = (face_mask_resized > 0.5).astype(
                                np.uint8
                            ) * 255

                            # 마스크의 윤곽선만 추출 (사각형이 아닌 실제 얼굴 윤곽만)
                            contours, _ = cv2.findContours(
                                mask_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                            )

                            # 컬러 마스크 생성 (반투명 오버레이) - 얼굴 윤곽만
                            color_mask = np.zeros_like(annotated_img)

                            # 윤곽선 내부만 색상 마스크 적용
                            if len(contours) > 0:
                                # 가장 큰 윤곽선 찾기 (얼굴)
                                largest_contour = max(contours, key=cv2.contourArea)

                                # 얼굴 영역 내에서만 마스크 적용
                                face_mask_filled = np.zeros(
                                    (face_height, face_width), dtype=np.uint8
                                )
                                cv2.fillPoly(face_mask_filled, [largest_contour], 255)

                                # 얼굴 영역에만 색상 마스크 적용 (윤곽선 내부만)
                                for y in range(face_height):
                                    for x in range(face_width):
                                        if face_mask_filled[y, x] > 0:
                                            # 얼굴 영역 내 좌표로 변환
                                            img_y = y1 + y
                                            img_x = x1 + x
                                            if (
                                                0 <= img_y < img_height
                                                and 0 <= img_x < img_width
                                            ):
                                                color_mask[img_y, img_x] = [
                                                    0,
                                                    255,
                                                    255,
                                                ]  # 노란색

                            # 얼굴 영역에만 오버레이 적용
                            overlay = annotated_img[y1:y2, x1:x2].copy()
                            color_face = color_mask[y1:y2, x1:x2]
                            if np.sum(color_face) > 0:
                                cv2.addWeighted(
                                    overlay,
                                    0.7,
                                    color_face,
                                    0.3,
                                    0,
                                    annotated_img[y1:y2, x1:x2],
                                )

                            print(
                                f"  - 얼굴 {face_idx + 1}에 segmentation 마스크 적용됨 (커버리지: {mask_coverage:.2%}, confidence: {seg_confidence:.2f})"
                            )

            # 세그먼테이션 결과에는 바운딩 박스와 라벨을 그리지 않음
            # 세그먼테이션은 얼굴 윤곽만 반영되어야 하므로 마스크만 표시

        # 결과 이미지 경로 설정
        if output_path is None:
            image_dir = os.path.dirname(image_path)
            image_name = os.path.basename(image_path)
            name_without_ext = os.path.splitext(image_name)[0]
            ext = os.path.splitext(image_name)[1]
            output_path = os.path.join(image_dir, f"{name_without_ext}_segmented{ext}")
            print(f"\nSegmentation 결과 이미지 저장 경로: {output_path}")

        # 결과 이미지 저장
        cv2.imwrite(output_path, annotated_img)

        # 평균 confidence 계산
        avg_confidence = (
            sum(all_confidences) / len(all_confidences)
            if len(all_confidences) > 0
            else 0.0
        )

        print(f"✓ 결과 이미지 저장 완료: {output_path}")
        print(f"✓ 처리된 얼굴 수: {face_count}개")
        print(f"✓ 평균 confidence: {avg_confidence:.2f}")

        return output_path, face_count, avg_confidence

    except ImportError:
        raise ImportError(
            "YOLO가 설치되지 않았습니다. pip install ultralytics를 실행하세요."
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise Exception(f"얼굴 감지 및 Segmentation 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    # 테스트 코드
    current_dir = Path(__file__).parent.resolve()
    app_dir = current_dir.parent
    data_dir = app_dir / "data" / "yolo"

    # 테스트 이미지 경로
    test_image = data_dir / "카리나.jpg"

    if test_image.exists():
        print(f"테스트 이미지: {test_image}")
        output_path, face_count, avg_confidence = detect_faces_and_segment(
            str(test_image)
        )
        print(f"결과 이미지: {output_path}")
        print(f"탐지된 얼굴 수: {face_count}")
        print(f"평균 confidence: {avg_confidence:.2f}")
    else:
        print(f"테스트 이미지를 찾을 수 없습니다: {test_image}")
        print(f"사용 가능한 이미지 파일:")
        for img_file in data_dir.glob("*.jpg"):
            print(f"  - {img_file.name}")
