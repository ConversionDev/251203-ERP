# 머신러닝 학습의 Hello World 와 같은 MNIST(손글씨 숫자 인식) 문제를 신경망으로 풀어봅니다.
import os

# OpenMP 라이브러리 충돌 문제 해결 (Windows 환경)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

# MNIST 데이터를 다운로드하고 로드합니다.
# transforms.ToTensor()는 이미지를 텐서로 변환하고 0~1 사이의 값으로 정규화합니다.
transform = transforms.Compose([transforms.ToTensor()])

# 현재 스크립트 위치 기준으로 데이터 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, "data", "mnist")

# 학습 데이터셋 로드
train_dataset = datasets.MNIST(
    root=data_dir, train=True, download=True, transform=transform
)
# 테스트 데이터셋 로드
test_dataset = datasets.MNIST(
    root=data_dir, train=False, download=True, transform=transform
)

# 데이터 로더 생성 (배치 크기 100)
train_loader = DataLoader(train_dataset, batch_size=100, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=100, shuffle=False)


#########
# 신경망 모델 구성
######
# 입력 값의 차원은 [배치크기, 특성값] 으로 되어 있습니다.
# 손글씨 이미지는 28x28 픽셀로 이루어져 있고, 이를 784개의 특성값으로 정합니다.
# 결과는 0~9 의 10 가지 분류를 가집니다.
# 신경망의 레이어는 다음처럼 구성합니다.
# 784(입력 특성값)
#   -> 256 (히든레이어 뉴런 갯수) -> 256 (히든레이어 뉴런 갯수)
#   -> 10 (결과값 0~9 분류)
class MNISTNet(nn.Module):
    def __init__(self):
        super(MNISTNet, self).__init__()
        # 첫 번째 레이어: 784 -> 256
        self.fc1 = nn.Linear(784, 256)
        # 두 번째 레이어: 256 -> 256
        self.fc2 = nn.Linear(256, 256)
        # 세 번째 레이어: 256 -> 10
        self.fc3 = nn.Linear(256, 10)
        # ReLU 활성화 함수
        self.relu = nn.ReLU()

    def forward(self, x):
        # 입력 이미지를 1차원 벡터로 변환 (배치 크기, 784)
        x = x.view(-1, 784)
        # 첫 번째 레이어에 가중치를 곱하고 ReLU 함수를 적용합니다.
        x = self.relu(self.fc1(x))
        # 두 번째 레이어에 가중치를 곱하고 ReLU 함수를 적용합니다.
        x = self.relu(self.fc2(x))
        # 최종 모델의 출력값은 fc3 레이어를 통과해 10개의 분류를 가지게 됩니다.
        x = self.fc3(x)
        return x


# 모델 인스턴스 생성
model = MNISTNet()

# 손실 함수: CrossEntropyLoss (softmax + cross entropy를 포함)
criterion = nn.CrossEntropyLoss()

# 옵티마이저: Adam (학습률 0.001)
optimizer = optim.Adam(model.parameters(), lr=0.001)


#########
# 신경망 모델 학습
######
def train_model():
    model.train()  # 학습 모드로 설정
    total_batch = len(train_loader)

    for epoch in range(15):
        total_cost = 0

        for batch_xs, batch_ys in train_loader:
            # 옵티마이저의 그래디언트 초기화
            optimizer.zero_grad()

            # 모델의 예측값 계산
            outputs = model(batch_xs)

            # 손실 계산
            loss = criterion(outputs, batch_ys)

            # 역전파 및 가중치 업데이트
            loss.backward()
            optimizer.step()

            total_cost += loss.item()

        print(
            "Epoch:",
            "%04d" % (epoch + 1),
            "Avg. cost =",
            "{:.3f}".format(total_cost / total_batch),
        )

    print("최적화 완료!")


#########
# 결과 확인
######
def evaluate_model():
    model.eval()  # 평가 모드로 설정
    correct = 0
    total = 0

    with torch.no_grad():  # 그래디언트 계산 비활성화
        for batch_xs, batch_ys in test_loader:
            # 모델의 예측값 계산
            outputs = model(batch_xs)

            # 가장 높은 값을 가진 인덱스를 예측 레이블로 선택
            _, predicted = torch.max(outputs.data, 1)

            total += batch_ys.size(0)
            correct += (predicted == batch_ys).sum().item()

    accuracy = 100 * correct / total
    print("정확도:", "{:.2f}%".format(accuracy))
    return accuracy


if __name__ == "__main__":
    # 모델 학습
    train_model()

    # 모델 평가
    evaluate_model()
