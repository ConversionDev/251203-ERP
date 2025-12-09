# 빌드 단계
FROM gradle:8.5-jdk21 AS builder
WORKDIR /build
COPY . .
RUN gradle build -x test

# 실행 단계 (slim 버전 사용)
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=builder /build/build/libs/*.jar app.jar
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75.0", "-jar", "app.jar"]

