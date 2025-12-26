import os
import cv2
from pathlib import Path
from typing import Optional, Tuple


def detect_faces_and_pose(
    image_path: str, output_path: Optional[str] = None
) -> Tuple[str, int, float]:
    """
    YOLO 얼굴 전용 모델로 얼굴을 감지하고, 감지된 얼굴 영역에 대해 YOLO pose estimation을 수행하는 함수

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

        # Pose 모델 경로 (yolo11n-pose.pt 사용)
        pose_model_path = project_root / "yolo11n-pose.pt"

        # 모델 파일 존재 확인
        if not face_model_path.exists():
            raise FileNotFoundError(
                f"얼굴 전용 모델을 찾을 수 없습니다: {face_model_path}\n"
                f"yolov8n-face-lindevs.pt 파일을 프로젝트 루트에 배치해주세요."
            )

        if not pose_model_path.exists():
            raise FileNotFoundError(
                f"Pose 모델을 찾을 수 없습니다: {pose_model_path}\n"
                f"yolo11n-pose.pt 파일을 프로젝트 루트에 배치해주세요."
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
                output_path = os.path.join(image_dir, f"{name_without_ext}_pose{ext}")

            cv2.imwrite(output_path, img)
            print(f"결과 이미지 저장: {output_path}")
            return output_path, 0, 0.0

        # 2단계: Pose Estimation 수행 (전체 이미지에서 전체 신체 포즈 추정)
        print("\n" + "=" * 60)
        print("2단계: Pose Estimation 시작 (전체 신체 포즈 추정)")
        print("=" * 60)
        pose_model = YOLO(str(pose_model_path))
        print("Pose 모델 사용: yolo11n-pose.pt")

        # 전체 이미지에서 pose estimation 수행
        pose_results = pose_model(image_path, conf=0.25, task="pose")

        # 결과 이미지 준비
        annotated_img = img.copy()

        # 전체 confidence 추적
        all_confidences = []

        # 전체 이미지에서 전체 신체 포즈 키포인트 찾기 및 표시
        for result in pose_results:
            # Pose 키포인트가 있는 경우
            if result.keypoints is not None and len(result.keypoints) > 0:
                keypoints_data = result.keypoints.data.cpu().numpy()

                # boxes에서 confidence 추출
                boxes_data = result.boxes if result.boxes is not None else None

                for kp_idx, keypoints in enumerate(keypoints_data):
                    # 해당 포즈의 confidence 추출
                    pose_confidence = 0.0
                    if boxes_data is not None and len(boxes_data) > kp_idx:
                        pose_confidence = float(boxes_data[kp_idx].conf[0])
                        all_confidences.append(pose_confidence)
                        print(
                            f"  - 포즈 {kp_idx + 1} confidence: {pose_confidence:.2f}"
                        )

                    # 모든 키포인트 그리기 (전체 신체)
                    for kp in keypoints:
                        if len(kp) >= 2:
                            kp_x = int(kp[0])
                            kp_y = int(kp[1])
                            kp_conf = kp[2] if len(kp) >= 3 else 1.0

                            # confidence가 0.5 이상인 키포인트만 표시
                            if kp_conf > 0.5:
                                # 이미지 경계 내로 제한
                                kp_x = max(0, min(kp_x, img_width - 1))
                                kp_y = max(0, min(kp_y, img_height - 1))

                                # 키포인트 그리기 (초록색 원)
                                cv2.circle(
                                    annotated_img, (kp_x, kp_y), 5, (0, 255, 0), -1
                                )

                    # COCO 포즈의 전체 연결선 그리기 (17개 키포인트)
                    if len(keypoints) >= 17:
                        # COCO 포즈 연결선 정의 (전체 신체)
                        connections = [
                            (0, 1),  # nose - left_eye
                            (0, 2),  # nose - right_eye
                            (1, 3),  # left_eye - left_ear
                            (2, 4),  # right_eye - right_ear
                            (5, 6),  # left_shoulder - right_shoulder
                            (5, 7),  # left_shoulder - left_elbow
                            (7, 9),  # left_elbow - left_wrist
                            (6, 8),  # right_shoulder - right_elbow
                            (8, 10),  # right_elbow - right_wrist
                            (5, 11),  # left_shoulder - left_hip
                            (6, 12),  # right_shoulder - right_hip
                            (11, 12),  # left_hip - right_hip
                            (11, 13),  # left_hip - left_knee
                            (13, 15),  # left_knee - left_ankle
                            (12, 14),  # right_hip - right_knee
                            (14, 16),  # right_knee - right_ankle
                        ]

                        # 모든 연결선 그리기
                        for start_idx, end_idx in connections:
                            if start_idx < len(keypoints) and end_idx < len(keypoints):
                                start_kp = keypoints[start_idx]
                                end_kp = keypoints[end_idx]

                                if (
                                    len(start_kp) >= 3
                                    and len(end_kp) >= 3
                                    and start_kp[2] > 0.5
                                    and end_kp[2] > 0.5
                                ):
                                    start_x = int(start_kp[0])
                                    start_y = int(start_kp[1])
                                    end_x = int(end_kp[0])
                                    end_y = int(end_kp[1])

                                    # 이미지 경계 내로 제한
                                    start_x = max(0, min(start_x, img_width - 1))
                                    start_y = max(0, min(start_y, img_height - 1))
                                    end_x = max(0, min(end_x, img_width - 1))
                                    end_y = max(0, min(end_y, img_height - 1))

                                    # 연결선 그리기 (파란색)
                                    cv2.line(
                                        annotated_img,
                                        (start_x, start_y),
                                        (end_x, end_y),
                                        (255, 0, 0),
                                        2,
                                    )

                    # 탐지된 키포인트 수 출력
                    detected_kp_count = sum(
                        1 for kp in keypoints if len(kp) >= 3 and kp[2] > 0.5
                    )
                    if detected_kp_count > 0:
                        print(
                            f"  - 전체 신체 포즈 키포인트 {detected_kp_count}개 적용됨"
                        )

        # 결과 이미지 경로 설정
        if output_path is None:
            image_dir = os.path.dirname(image_path)
            image_name = os.path.basename(image_path)
            name_without_ext = os.path.splitext(image_name)[0]
            ext = os.path.splitext(image_name)[1]
            output_path = os.path.join(image_dir, f"{name_without_ext}_pose{ext}")
            print(f"\nPose 결과 이미지 저장 경로: {output_path}")

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
        raise Exception(f"얼굴 감지 및 Pose Estimation 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    # 테스트 코드
    current_dir = Path(__file__).parent.resolve()
    app_dir = current_dir.parent
    data_dir = app_dir / "data" / "yolo"

    # 테스트 이미지 경로
    test_image = data_dir / "카리나.jpg"

    if test_image.exists():
        print(f"테스트 이미지: {test_image}")
        output_path, face_count, avg_confidence = detect_faces_and_pose(str(test_image))
        print(f"결과 이미지: {output_path}")
        print(f"탐지된 얼굴 수: {face_count}")
        print(f"평균 confidence: {avg_confidence:.2f}")
    else:
        print(f"테스트 이미지를 찾을 수 없습니다: {test_image}")
        print(f"사용 가능한 이미지 파일:")
        for img_file in data_dir.glob("*.jpg"):
            print(f"  - {img_file}")
