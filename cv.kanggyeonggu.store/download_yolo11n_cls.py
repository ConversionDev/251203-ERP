"""
YOLO11n Classification 모델 다운로드 스크립트
yolo11n-cls.pt 파일을 프로젝트 루트에 다운로드합니다.
"""

import shutil
from pathlib import Path

try:
    from ultralytics import YOLO

    # 현재 스크립트 위치 기준으로 프로젝트 루트 찾기
    current_dir = Path(__file__).parent.resolve()
    project_root = current_dir
    target_path = project_root / "yolo11n-cls.pt"

    print("=" * 60)
    print("YOLO11n Classification 모델 다운로드 시작")
    print("=" * 60)

    # 이미 파일이 존재하는지 확인
    if target_path.exists():
        print(f"✓ 모델 파일이 이미 존재합니다: {target_path}")
        print("다운로드를 건너뜁니다.")
    else:
        print(f"모델 다운로드 중... (저장 위치: {target_path})")

        # Ultralytics 캐시 디렉토리에서 모델 파일 찾기
        # 일반적으로 ~/.ultralytics/weights/ 또는 ultralytics 홈 디렉토리에 저장됨

        # ultralytics 홈 디렉토리 찾기
        ultralytics_home = Path.home() / ".ultralytics"
        weights_dir = ultralytics_home / "weights"

        # 모델 파일 찾기
        model_file = None
        if weights_dir.exists():
            model_file = weights_dir / "yolo11n-cls.pt"
            if not model_file.exists():
                # 다른 가능한 위치 확인
                for possible_file in weights_dir.glob("yolo11n-cls*.pt"):
                    model_file = possible_file
                    break

        # 모델 파일을 프로젝트 루트로 복사
        if model_file and model_file.exists():
            print(f"다운로드된 모델 파일 발견: {model_file}")
            print(f"프로젝트 루트로 복사 중...")

            # 복사 시도 (권한 오류 대비)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    shutil.copy2(model_file, target_path)
                    print(f"✓ 모델 파일 복사 완료: {target_path}")
                    break
                except PermissionError as e:
                    if attempt < max_retries - 1:
                        print(
                            f"권한 오류 발생, 재시도 중... ({attempt + 1}/{max_retries})"
                        )
                        import time

                        time.sleep(1)
                    else:
                        raise e
        else:
            # 직접 다운로드 시도
            print("캐시에서 모델 파일을 찾을 수 없습니다. 직접 다운로드 시도...")
            try:
                # 모델을 로드하면 자동으로 다운로드됨
                _ = YOLO("yolo11n-cls.pt")
                # 다시 캐시에서 찾기
                if weights_dir.exists():
                    model_file = weights_dir / "yolo11n-cls.pt"
                    if model_file.exists():
                        shutil.copy2(model_file, target_path)
                        print(f"✓ 모델 파일 복사 완료: {target_path}")
                    else:
                        print("경고: 모델 파일을 찾을 수 없습니다.")
                        print("수동으로 다운로드가 필요할 수 있습니다.")
                else:
                    print("경고: Ultralytics 캐시 디렉토리를 찾을 수 없습니다.")
            except Exception as e:
                print(f"다운로드 중 오류 발생: {str(e)}")
                print("\n수동 다운로드 방법:")
                print(
                    "1. https://github.com/ultralytics/ultralytics 에서 모델 다운로드"
                )
                print(f"2. 다운로드한 파일을 {target_path}에 저장")

    print("=" * 60)
    print("다운로드 완료!")
    print(f"모델 파일 위치: {target_path}")
    print("=" * 60)

except ImportError:
    print("오류: ultralytics가 설치되지 않았습니다.")
    print("다음 명령어로 설치하세요: pip install ultralytics")
except Exception as e:
    print(f"오류 발생: {str(e)}")
    import traceback

    traceback.print_exc()
