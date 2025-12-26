import cv2
import os
import numpy as np


class WinterDetect:
    def __init__(self):
        # 현재 스크립트 위치 기준으로 데이터 경로 설정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(current_dir, "..", "data", "opencv")

        self._winter = os.path.join(data_dir, "winter.png")

    def read_file(self):
        img = cv2.imread(self._winter)

        # 이미지가 제대로 로드되었는지 확인
        if img is None:
            print(f"이미지를 로드할 수 없습니다: {self._winter}")
            return

        print(f"이미지 크기: {img.shape}")

        # 전략 5: 딥러닝 기반 얼굴 탐지 (MTCNN 사용)
        print("\n=== MTCNN 딥러닝 기반 얼굴 탐지 ===")
        faces = self._try_mtcnn(img)

        # MTCNN 실패 시 face_recognition 시도
        if len(faces) == 0:
            print("\n=== face_recognition 라이브러리 시도 ===")
            faces = self._try_face_recognition(img)

        if len(faces) == 0:
            print("\n얼굴을 찾을 수 없습니다.")
            # 이미지를 표시하여 확인
            cv2.imshow("winter", img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            return

        print(f"\n성공! {len(faces)}개의 얼굴을 찾았습니다.")
        for idx, (x, y, w, h) in enumerate(faces):
            print("얼굴인식 인덱스: ", idx)
            print("얼굴인식 좌표: ", x, y, w, h)
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cv2.imwrite("winter_detect.jpg", img)
        cv2.imshow("winter", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def _try_mtcnn(self, img):
        """MTCNN을 사용한 얼굴 탐지"""
        try:
            from mtcnn import MTCNN

            # MTCNN은 RGB 형식을 사용
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            print("  MTCNN 모델 로딩 중...")
            detector = MTCNN()
            results = detector.detect_faces(rgb_img)

            if len(results) > 0:
                print(f"  ✓ MTCNN으로 {len(results)}개 얼굴 탐지 성공!")
                faces = []
                for result in results:
                    box = result["box"]  # [x, y, width, height]
                    faces.append(box)
                return np.array(faces)
            else:
                print("  ✗ MTCNN: 얼굴을 찾지 못했습니다.")
        except ImportError as e:
            print(f"  ✗ MTCNN 라이브러리가 설치되지 않았습니다: {e}")
            print("     설치: pip install mtcnn")
        except Exception as e:
            print(f"  ✗ MTCNN 오류: {type(e).__name__}: {e}")
            import traceback

            traceback.print_exc()

        return []

    def _try_face_recognition(self, img):
        """face_recognition 라이브러리를 사용한 얼굴 탐지"""
        try:
            import face_recognition

            # face_recognition은 RGB 형식을 사용
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # 얼굴 위치 탐지 (HOG 기반, 더 빠름)
            print("  HOG 모델로 탐지 시도 중...")
            face_locations = face_recognition.face_locations(rgb_img, model="hog")

            if len(face_locations) == 0:
                # HOG 실패 시 CNN 모델 시도 (더 정확하지만 느림)
                print("  HOG 모델 실패, CNN 모델 시도 중...")
                face_locations = face_recognition.face_locations(rgb_img, model="cnn")

            if len(face_locations) > 0:
                print(
                    f"  ✓ face_recognition으로 {len(face_locations)}개 얼굴 탐지 성공!"
                )
                # face_recognition은 (top, right, bottom, left) 형식
                # OpenCV는 (x, y, w, h) 형식이므로 변환
                faces = []
                for top, right, bottom, left in face_locations:
                    x = left
                    y = top
                    w = right - left
                    h = bottom - top
                    faces.append([x, y, w, h])
                return np.array(faces)
            else:
                print("  ✗ face_recognition: 탐지 실패")
        except ImportError:
            print("  ✗ face_recognition 라이브러리가 설치되지 않았습니다.")
            print("     설치: pip install face-recognition")
            print("     (주의: Windows에서는 dlib 설치가 어려울 수 있습니다)")
        except Exception as e:
            print(f"  ✗ face_recognition 오류: {e}")

        return []


if __name__ == "__main__":
    winter_detect = WinterDetect()
    winter_detect.read_file()
    