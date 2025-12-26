# 패션 MNIST 구현하는 코드입니다.
import os

# OpenMP 라이브러리 충돌 문제 해결 (Windows 환경)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import matplotlib.pyplot as plt
import numpy as np


class MnistTest:
    def __init__(self):
        self.class_names = [
            "T-shirt/top",
            "Trouser",
            "Pullover",
            "Dress",
            "Coat",
            "Sandal",
            "Shirt",
            "Sneaker",
            "Bag",
            "Ankle boot",
        ]

    def create_model(self):
        # Fashion-MNIST 데이터셋 로드
        transform = transforms.Compose([transforms.ToTensor()])

        # 현재 스크립트 위치 기준으로 데이터 경로 설정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(current_dir, "data", "fashion-mnist")

        train_dataset = datasets.FashionMNIST(
            root=data_dir, train=True, download=True, transform=transform
        )
        test_dataset = datasets.FashionMNIST(
            root=data_dir, train=False, download=True, transform=transform
        )

        train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

        # 데이터를 numpy 배열로 변환 (시각화용)
        # 학습 데이터의 처음 25개 이미지 시각화
        train_images_np = []
        train_labels_np = []
        for i, (img, label) in enumerate(train_dataset):
            if i < 25:
                train_images_np.append(img.squeeze().numpy())
                train_labels_np.append(label)
            else:
                break

        train_images_np = np.array(train_images_np)
        train_labels_np = np.array(train_labels_np)

        # 시각화: 처음 25개 이미지 표시
        plt.figure(figsize=(10, 10))
        for i in range(25):
            plt.subplot(5, 5, i + 1)
            plt.xticks([])
            plt.yticks([])
            plt.grid(False)
            plt.imshow(train_images_np[i], cmap=plt.cm.binary)
            plt.xlabel(self.class_names[train_labels_np[i]])
        # plt.show()  # 주석 해제하면 이미지 표시

        # 모델 정의
        """
        relu (Rectified Linear Unit 정류한 선형 유닛)
        미분 가능한 0과 1사이의 값을 갖도록 하는 알고리즘
        softmax
        nn (neural network)의 최상위층에서 사용되며 classification을 위한 function
        결과를 확률값으로 해석하기 위한 알고리즘
        """
        model = FashionNet()

        # 손실 함수 및 옵티마이저
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters())

        # 학습
        model.train()
        num_epochs = 5
        for epoch in range(num_epochs):
            running_loss = 0.0
            for batch_images, batch_labels in train_loader:
                optimizer.zero_grad()
                outputs = model(batch_images)
                loss = criterion(outputs, batch_labels)
                loss.backward()
                optimizer.step()
                running_loss += loss.item()

            print(
                f"Epoch {epoch + 1}/{num_epochs}, Loss: {running_loss / len(train_loader):.4f}"
            )

        # 테스트
        model.eval()
        correct = 0
        total = 0
        test_loss = 0.0

        all_predictions = []
        all_labels = []
        all_images = []

        with torch.no_grad():
            for batch_images, batch_labels in test_loader:
                outputs = model(batch_images)
                loss = criterion(outputs, batch_labels)
                test_loss += loss.item()

                _, predicted = torch.max(outputs.data, 1)
                total += batch_labels.size(0)
                correct += (predicted == batch_labels).sum().item()

                # 예측 결과 저장 (시각화용)
                all_predictions.extend(outputs.cpu().numpy())
                all_labels.extend(batch_labels.cpu().numpy())
                all_images.extend(batch_images.cpu().numpy())

        test_acc = correct / total
        avg_test_loss = test_loss / len(test_loader)

        print(f"\n테스트 손실: {avg_test_loss:.4f}")
        print(f"테스트 정확도: {test_acc:.4f}")

        # 예측 결과 확인 (softmax 적용하여 확률값으로 변환)
        predictions = np.array(all_predictions)
        # softmax 적용
        predictions = torch.softmax(torch.from_numpy(predictions), dim=1).numpy()
        print("\n테스트 이미지 3번째 예측 확률:")
        print(predictions[3])

        # 10개 클래스에 대한 예측을 그래프화
        arr = [predictions, np.array(all_labels), np.array(all_images)]
        return arr

    def plot_image(self, i, predictions_array, true_label, img):
        print(" === plot_image 로 진입 ===")
        predictions_array, true_label, img = (
            predictions_array[i],
            true_label[i],
            img[i],
        )
        plt.grid(False)
        plt.xticks([])
        plt.yticks([])

        plt.imshow(img.squeeze(), cmap=plt.cm.binary)
        # plt.show()  # 주석 해제하면 이미지 표시

        predicted_label = np.argmax(predictions_array)
        if predicted_label == true_label:
            color = "blue"
        else:
            color = "red"

        plt.xlabel(
            "{} {:2.0f}% ({})".format(
                self.class_names[predicted_label],
                100 * np.max(predictions_array),
                self.class_names[true_label],
            ),
            color=color,
        )

    @staticmethod
    def plot_value_array(i, predictions_array, true_label):
        predictions_array, true_label = predictions_array[i], true_label[i]
        plt.grid(False)
        plt.xticks([])
        plt.yticks([])
        thisplot = plt.bar(range(10), predictions_array, color="#777777")
        plt.ylim([0, 1])
        predicted_label = np.argmax(predictions_array)

        thisplot[predicted_label].set_color("red")
        thisplot[true_label].set_color("blue")


# 신경망 모델 정의
class FashionNet(nn.Module):
    def __init__(self):
        super(FashionNet, self).__init__()
        # Flatten은 view(-1, 784)로 처리
        # Dense(128, activation='relu')
        self.fc1 = nn.Linear(28 * 28, 128)
        self.relu = nn.ReLU()
        # Dense(10, activation='softmax')
        # PyTorch의 CrossEntropyLoss는 softmax를 포함하므로 마지막 레이어는 softmax 없이
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        # Flatten: (batch_size, 1, 28, 28) -> (batch_size, 784)
        x = x.view(-1, 28 * 28)
        # Dense(128, activation='relu')
        x = self.relu(self.fc1(x))
        # Dense(10) - softmax는 CrossEntropyLoss에서 처리
        x = self.fc2(x)
        return x


if __name__ == "__main__":
    mnist_test = MnistTest()
    predictions, test_labels, test_images = mnist_test.create_model()

    # 예시: 첫 번째 이미지 시각화
    mnist_test.plot_image(0, predictions, test_labels, test_images)
    plt.show()

    # 예시: 첫 번째 이미지의 예측 확률 분포
    plt.figure(figsize=(6, 3))
    plt.subplot(1, 2, 1)
    mnist_test.plot_image(0, predictions, test_labels, test_images)
    plt.subplot(1, 2, 2)
    mnist_test.plot_value_array(0, predictions, test_labels)
    plt.show()
