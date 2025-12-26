import cv2
import os


class FaceDetect:
    def __init__(self):
        # 현재 스크립트 위치 기준으로 데이터 경로 설정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(current_dir, "..", "data", "opencv")

        self._cascade = os.path.join(data_dir, "haarcascade_frontalface_alt.xml")
        self._girl = os.path.join(data_dir, "girl.jpg")

    def read_file(self):
        cascade = cv2.CascadeClassifier(self._cascade)
        img = cv2.imread(self._girl)
        face = cascade.detectMultiScale(img, minSize=(150, 150))
        if len(face) == 0:
            print("얼굴을 찾을 수 없습니다.")
            quit()
        for idx, (x, y, w, h) in enumerate(face):
            print("얼굴인식 인덱스: ", idx)
            print("얼굴인식 좌표: ", x, y, w, h)
            img = self.mosaic(img, (x, y, x + w, y + h), 10)
        cv2.imwrite("face_mosaic.jpg", img)
        cv2.imshow("face", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    @staticmethod
    def mosaic(img, rect, size):
        (x1, y1, x2, y2) = rect
        w = x2 - x1
        h = y2 - y1
        i_rect = img[y1:y2, x1:x2]
        i_small = cv2.resize(i_rect, (size, size))
        i_mos = cv2.resize(i_small, (w, h), interpolation=cv2.INTER_AREA)
        img2 = img.copy()
        img2[y1:y2, x1:x2] = i_mos
        return img2

if __name__ == "__main__":
    face_detect = FaceDetect()
    face_detect.read_file()
