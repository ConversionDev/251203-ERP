import os

try:
    from ultralytics import YOLO
    from ultralytics.utils import ASSETS
    import cv2

    print("헬로우 욜로")
    print("YOLO 설치 확인 완료!")

    # 현재 스크립트 위치 기준으로 경로 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # YOLO 기본 샘플 이미지 사용
    # ASSETS는 ultralytics의 기본 샘플 이미지 경로
    image_path = str(ASSETS / "bus.jpg")  # 기본 샘플 이미지 (버스 이미지)

    # 이미지가 없으면 다운로드
    if not os.path.exists(image_path):
        print("샘플 이미지를 다운로드합니다...")
        # ultralytics가 자동으로 다운로드하거나, 직접 URL에서 다운로드
        import urllib.request

        url = "https://ultralytics.com/images/bus.jpg"
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        urllib.request.urlretrieve(url, image_path)

    print(f"사용할 이미지: {image_path}")

    # YOLO11 모델 로드 (nano 모델 - 가장 작고 빠름)
    print("YOLO11 모델 로딩 중...")
    model = YOLO("yolo11n.pt")

    # 객체 탐지 수행
    print("객체 탐지 중...")
    results = model(image_path)

    # 결과 이미지 표시
    for result in results:
        # 탐지 결과가 포함된 이미지 가져오기
        annotated_img = result.plot()

        # 이미지 표시
        cv2.imshow("헬로우 욜로 - YOLO11 객체 탐지 결과", annotated_img)
        print("이미지를 표시합니다. 아무 키나 누르면 종료됩니다.")
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        # 결과 이미지 저장
        output_path = os.path.join(current_dir, "hello_yolo_result.jpg")
        cv2.imwrite(output_path, annotated_img)
        print(f"결과 이미지 저장: {output_path}")

        # 탐지된 객체 정보 출력
        print(f"\n탐지된 객체 수: {len(result.boxes)}")
        for box in result.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            name = model.names[cls]
            print(f"  - {name}: {conf:.2f}")

except ImportError as e:
    print("YOLO가 설치되지 않았습니다. pip install ultralytics를 실행하세요.")
    print(f"오류: {e}")
except Exception as e:
    print(f"오류 발생: {e}")
    import traceback

    traceback.print_exc()
