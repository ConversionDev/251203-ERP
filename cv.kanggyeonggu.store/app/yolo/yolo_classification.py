"""
YOLO 하이브리드 방식: Detection + Classification
1단계: yolo11n.pt로 객체 위치 탐지 (박스만 추출)
2단계: yolo11n-cls.pt로 각 박스 영역을 정확하게 분류
"""

import os
import cv2
from pathlib import Path
from typing import Optional, Tuple, Dict


# ImageNet 클래스 중 개와 고양이 관련 클래스 ID 범위
# 참고: https://gist.github.com/yrevar/942d3a0ac09ec9e5eb3a
DOG_CLASS_RANGE = range(151, 269)  # 개 품종들 (151-268)
CAT_CLASS_RANGE = range(281, 286)  # 고양이 품종들 (281-285)


def is_dog_class(class_id: int, class_name: str) -> bool:
    """ImageNet 클래스가 개인지 확인"""
    class_name_lower = class_name.lower()
    # 클래스 ID로 확인
    if class_id in DOG_CLASS_RANGE:
        return True
    # 클래스 이름에 dog 관련 키워드 포함 확인
    dog_keywords = [
        "dog",
        "puppy",
        "hound",
        "terrier",
        "retriever",
        "spaniel",
        "poodle",
        "bulldog",
        "shepherd",
        "collie",
        "beagle",
        "boxer",
        "husky",
        "corgi",
        "pug",
        "dalmatian",
        "chihuahua",
        "labrador",
    ]
    return any(keyword in class_name_lower for keyword in dog_keywords)


def is_cat_class(class_id: int, class_name: str) -> bool:
    """ImageNet 클래스가 고양이인지 확인"""
    class_name_lower = class_name.lower()
    # 클래스 ID로 확인
    if class_id in CAT_CLASS_RANGE:
        return True
    # 클래스 이름에 cat 관련 키워드 포함 확인
    cat_keywords = [
        "cat",
        "kitten",
        "tabby",
        "persian",
        "siamese",
        "egyptian_cat",
        "tiger_cat",
        "lynx",
    ]
    return any(keyword in class_name_lower for keyword in cat_keywords)


def classify_dogs_and_cats(
    image_path: str, output_path: Optional[str] = None
) -> Tuple[str, Dict[str, any]]:
    """
    YOLO 하이브리드 방식: Detection으로 위치 찾고, Classification으로 정확하게 분류

    Args:
        image_path: 입력 이미지 경로
        output_path: 결과 이미지 저장 경로 (None이면 자동 생성)

    Returns:
        Tuple[str, Dict]: (결과 이미지 경로, 분류 결과 딕셔너리)
    """
    try:
        from ultralytics import YOLO

        # 현재 스크립트 위치 기준으로 경로 설정
        current_dir = Path(__file__).parent.resolve()
        project_root = current_dir.parent.parent  # cv.kanggyeonggu.store

        # 모델 경로
        det_model_path = project_root / "yolo11n.pt"  # Detection 모델
        cls_model_path = project_root / "yolo11n-cls.pt"  # Classification 모델

        # 모델 파일 존재 확인
        if not det_model_path.exists():
            raise FileNotFoundError(
                f"Detection 모델을 찾을 수 없습니다: {det_model_path}\n"
                f"yolo11n.pt 파일을 프로젝트 루트에 배치해주세요."
            )

        if not cls_model_path.exists():
            raise FileNotFoundError(
                f"Classification 모델을 찾을 수 없습니다: {cls_model_path}\n"
                f"yolo11n-cls.pt 파일을 프로젝트 루트에 배치해주세요.\n"
                f"다운로드: python download_yolo11n_cls.py"
            )

        # 이미지 파일 존재 확인
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

        # 이미지 로드
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"이미지를 읽을 수 없습니다: {image_path}")

        img_height, img_width = img.shape[:2]

        # ========================================
        # 1단계: Detection 모델로 객체 위치 탐지
        # ========================================
        print("=" * 60)
        print("🔍 1단계: Detection 모델로 객체 위치 탐지")
        print("=" * 60)

        det_model = YOLO(str(det_model_path))
        print(f"Detection 모델: {det_model_path.name}")

        # 개(class 16)와 고양이(class 15)만 탐지
        det_results = det_model(
            image_path,
            conf=0.3,  # 낮은 confidence로 최대한 많이 탐지
            classes=[15, 16],  # cat=15, dog=16
            iou=0.5,
            agnostic_nms=True,
            max_det=10,
        )

        # 탐지된 박스 추출
        detected_boxes = []
        for result in det_results:
            if len(result.boxes) > 0:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    det_conf = float(box.conf[0])
                    det_class_id = int(box.cls[0])
                    det_class_name = result.names[det_class_id]

                    detected_boxes.append(
                        {
                            "bbox": (x1, y1, x2, y2),
                            "det_confidence": det_conf,
                            "det_class": det_class_name,
                        }
                    )
                    print(
                        f"  📦 탐지됨: {det_class_name} (conf: {det_conf:.2f}) at ({x1}, {y1}, {x2}, {y2})"
                    )

        print(f"\n  총 {len(detected_boxes)}개 객체 탐지됨")

        if len(detected_boxes) == 0:
            print("  ⚠️ 탐지된 객체가 없습니다.")
            # 빈 결과 반환
            annotated_img = img.copy()
            classification_result = {
                "dog_count": 0,
                "cat_count": 0,
                "total_count": 0,
                "average_confidence": 0.0,
                "detections": [],
            }
            # 결과 이미지 저장
            if output_path is None:
                image_dir = os.path.dirname(image_path)
                image_name = os.path.basename(image_path)
                name_without_ext = os.path.splitext(image_name)[0]
                ext = os.path.splitext(image_name)[1]
                output_path = os.path.join(
                    image_dir, f"{name_without_ext}_classified{ext}"
                )
            cv2.imwrite(output_path, annotated_img)
            return output_path, classification_result

        # ========================================
        # 2단계: Classification 모델로 각 박스 재분류
        # ========================================
        print("\n" + "=" * 60)
        print("🏷️ 2단계: Classification 모델로 정확한 분류")
        print("=" * 60)

        cls_model = YOLO(str(cls_model_path))
        print(f"Classification 모델: {cls_model_path.name}")

        # 결과 이미지 준비
        annotated_img = img.copy()

        # 분류 결과
        dog_count = 0
        cat_count = 0
        all_confidences = []
        detections = []

        for i, box_data in enumerate(detected_boxes):
            x1, y1, x2, y2 = box_data["bbox"]

            # 박스 영역 crop (약간의 마진 추가)
            margin = 10
            crop_x1 = max(0, x1 - margin)
            crop_y1 = max(0, y1 - margin)
            crop_x2 = min(img_width, x2 + margin)
            crop_y2 = min(img_height, y2 + margin)

            cropped_img = img[crop_y1:crop_y2, crop_x1:crop_x2]

            if cropped_img.size == 0:
                print(f"  ⚠️ 객체 {i + 1}: 유효하지 않은 crop 영역")
                continue

            # Classification 모델로 분류
            cls_results = cls_model(cropped_img, verbose=False)

            # 분류 결과 분석
            final_class = None
            final_confidence = 0.0

            for cls_result in cls_results:
                if hasattr(cls_result, "probs") and cls_result.probs is not None:
                    # 상위 5개 예측 확인
                    top5_indices = cls_result.probs.top5
                    top5_confs = cls_result.probs.top5conf

                    print(f"\n  🔎 객체 {i + 1} Classification 결과:")

                    # 상위 5개 중 개 또는 고양이 찾기
                    for idx, (cls_idx, conf) in enumerate(
                        zip(top5_indices, top5_confs)
                    ):
                        cls_name = cls_result.names[cls_idx]
                        conf_val = float(conf)

                        if idx < 3:  # 상위 3개만 출력
                            print(f"      {idx + 1}. {cls_name}: {conf_val:.2%}")

                        # 개 또는 고양이인지 확인
                        if final_class is None:
                            if is_dog_class(cls_idx, cls_name):
                                final_class = "dog"
                                final_confidence = conf_val
                            elif is_cat_class(cls_idx, cls_name):
                                final_class = "cat"
                                final_confidence = conf_val

            # 분류 결과가 없으면 Detection 결과 사용 (fallback)
            if final_class is None:
                det_class = box_data["det_class"].lower()
                if "dog" in det_class:
                    final_class = "dog"
                elif "cat" in det_class:
                    final_class = "cat"
                final_confidence = box_data["det_confidence"]
                print(
                    f"      ℹ️ Classification 실패, Detection 결과 사용: {final_class}"
                )

            if final_class is None:
                print(f"      ⚠️ 객체 {i + 1}: 개/고양이로 분류되지 않음")
                continue

            # 카운트 및 결과 저장
            if final_class == "dog":
                dog_count += 1
                color = (255, 100, 0)  # 파란색 (BGR)
            else:  # cat
                cat_count += 1
                color = (0, 165, 255)  # 주황색 (BGR)

            all_confidences.append(final_confidence)
            detections.append(
                {
                    "class": final_class,
                    "confidence": final_confidence,
                    "bbox": (x1, y1, x2, y2),
                }
            )

            label_text = f"{final_class} {final_confidence:.2f}"
            print(f"      ✅ 최종 분류: {label_text}")

            # 바운딩 박스 그리기
            thickness = 3
            cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, thickness)

            # 라벨 그리기
            label_size, baseline = cv2.getTextSize(
                label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
            )
            label_y = max(y1 - 10, label_size[1] + 10)

            # 라벨 배경
            cv2.rectangle(
                annotated_img,
                (x1, label_y - label_size[1] - 5),
                (x1 + label_size[0] + 10, label_y + 5),
                color,
                -1,
            )

            # 라벨 텍스트
            cv2.putText(
                annotated_img,
                label_text,
                (x1 + 5, label_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

        # ========================================
        # 3단계: 결과 정리
        # ========================================
        total_count = dog_count + cat_count
        avg_confidence = (
            sum(all_confidences) / len(all_confidences)
            if len(all_confidences) > 0
            else 0.0
        )

        print("\n" + "=" * 60)
        print("📊 최종 결과")
        print("=" * 60)
        print(f"  개: {dog_count}마리")
        print(f"  고양이: {cat_count}마리")
        print(f"  총: {total_count}마리")
        print(f"  평균 confidence: {avg_confidence:.2f}")

        classification_result = {
            "dog_count": dog_count,
            "cat_count": cat_count,
            "total_count": total_count,
            "average_confidence": avg_confidence,
            "detections": detections,
        }

        # 결과 이미지 저장
        if output_path is None:
            image_dir = os.path.dirname(image_path)
            image_name = os.path.basename(image_path)
            name_without_ext = os.path.splitext(image_name)[0]
            ext = os.path.splitext(image_name)[1]
            output_path = os.path.join(image_dir, f"{name_without_ext}_classified{ext}")

        cv2.imwrite(output_path, annotated_img)
        print(f"\n✓ 결과 이미지 저장: {output_path}")

        return output_path, classification_result

    except ImportError:
        raise ImportError(
            "YOLO가 설치되지 않았습니다. pip install ultralytics를 실행하세요."
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise Exception(f"Classification 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    # 테스트 코드
    current_dir = Path(__file__).parent.resolve()
    app_dir = current_dir.parent
    data_dir = app_dir / "data" / "yolo"

    # 테스트 이미지 경로
    test_image = data_dir / "test_dog_cat.jpg"

    if test_image.exists():
        print(f"테스트 이미지: {test_image}")
        output_path, result = classify_dogs_and_cats(str(test_image))
        print(f"\n결과 이미지: {output_path}")
        print(f"개: {result['dog_count']}마리")
        print(f"고양이: {result['cat_count']}마리")
        print(f"총: {result['total_count']}마리")
        print(f"평균 Confidence: {result['average_confidence']:.2f}")
    else:
        print(f"테스트 이미지를 찾을 수 없습니다: {test_image}")
        print("사용 가능한 이미지 파일:")
        for img_file in data_dir.glob("*.jpg"):
            print(f"  - {img_file}")
