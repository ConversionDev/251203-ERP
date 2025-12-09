package store.kanggyoenggu.oauthservice.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import store.kanggyoenggu.oauthservice.entity.User;
import store.kanggyoenggu.oauthservice.repository.UserRepository;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.concurrent.TimeUnit;

/**
 * 사용자 관리 서비스
 * - DB Upsert (생성 또는 업데이트)
 * - Upstash Redis 저장
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;
    private final RedisTemplate<String, Object> redisTemplate;

    /**
     * OAuth 로그인 시 사용자 정보를 DB와 Redis에 저장
     * 
     * @param provider OAuth 제공자 (kakao, google, naver)
     * @param providerId OAuth 제공자의 사용자 ID
     * @param nickname 닉네임
     * @param profileImageUrl 프로필 이미지 URL (선택)
     * @return 저장된 User 엔티티
     */
    @Transactional
    public User upsertUser(String provider, String providerId, String nickname, String profileImageUrl) {
        log.info("🔄 사용자 Upsert 시작: provider={}, providerId={}", provider, providerId);

        // 1. DB에서 기존 사용자 조회
        Optional<User> existingUser = userRepository
                .findByProviderAndProviderIdAndDeletedFalse(provider, providerId);

        User user;
        if (existingUser.isPresent()) {
            // 기존 사용자 업데이트
            user = existingUser.get();
            log.info("✅ 기존 사용자 발견: id={}, nickname={}", user.getId(), user.getNickname());
            
            user.setNickname(nickname);
            user.setProfileImageUrl(profileImageUrl);
            user.setLastLoginAt(LocalDateTime.now());
            
            log.info("📝 사용자 정보 업데이트 완료");
        } else {
            // 신규 사용자 생성
            user = User.builder()
                    .provider(provider)
                    .providerId(providerId)
                    .nickname(nickname)
                    .profileImageUrl(profileImageUrl)
                    .enabled(true)
                    .deleted(false)
                    .build();
            
            log.info("🆕 신규 사용자 생성");
        }

        // 2. DB 저장 (Neon PostgreSQL)
        user = userRepository.save(user);
        log.info("💾 Neon DB 저장 완료: id={}", user.getId());

        // 3. Redis 저장 (Upstash Redis)
        saveToRedis(user);

        return user;
    }

    /**
     * Upstash Redis에 사용자 정보 저장
     * 키 형식: user:{userId}
     * 
     * @param user 저장할 사용자 정보
     */
    private void saveToRedis(User user) {
        try {
            String key = "user:" + user.getId();
            
            // Redis에 JSON 형태로 저장
            redisTemplate.opsForValue().set(key, user);
            
            // 만료 시간 설정 (24시간)
            redisTemplate.expire(key, 24, TimeUnit.HOURS);
            
            log.info("✅ Upstash Redis 저장 완료: key={}", key);
        } catch (Exception e) {
            log.error("❌ Redis 저장 실패: {}", e.getMessage(), e);
            // Redis 저장 실패해도 로그인은 진행 (DB에는 저장됨)
        }
    }

    /**
     * Redis에서 사용자 정보 조회
     * 
     * @param userId 사용자 ID
     * @return 사용자 정보 (Optional)
     */
    public Optional<User> getUserFromRedis(Long userId) {
        try {
            String key = "user:" + userId;
            Object value = redisTemplate.opsForValue().get(key);
            
            if (value instanceof User) {
                log.info("✅ Redis에서 사용자 조회 성공: userId={}", userId);
                return Optional.of((User) value);
            }
            
            log.info("⚠️ Redis에 사용자 없음: userId={}", userId);
            return Optional.empty();
        } catch (Exception e) {
            log.error("❌ Redis 조회 실패: {}", e.getMessage(), e);
            return Optional.empty();
        }
    }

    /**
     * Redis에서 사용자 정보 삭제
     * 
     * @param userId 사용자 ID
     */
    public void deleteFromRedis(Long userId) {
        try {
            String key = "user:" + userId;
            redisTemplate.delete(key);
            log.info("✅ Redis에서 사용자 삭제 완료: userId={}", userId);
        } catch (Exception e) {
            log.error("❌ Redis 삭제 실패: {}", e.getMessage(), e);
        }
    }

    /**
     * DB에서 사용자 조회 (Redis 캐시 미스 시 사용)
     * 
     * @param userId 사용자 ID
     * @return 사용자 정보 (Optional)
     */
    public Optional<User> getUserFromDB(Long userId) {
        return userRepository.findById(userId);
    }

    /**
     * 사용자 조회 (Redis → DB 순서)
     * 
     * @param userId 사용자 ID
     * @return 사용자 정보 (Optional)
     */
    public Optional<User> getUser(Long userId) {
        // 1. Redis에서 먼저 조회 (빠름)
        Optional<User> userFromRedis = getUserFromRedis(userId);
        if (userFromRedis.isPresent()) {
            return userFromRedis;
        }

        // 2. Redis에 없으면 DB에서 조회
        Optional<User> userFromDB = getUserFromDB(userId);
        if (userFromDB.isPresent()) {
            // DB에서 조회한 데이터를 Redis에 저장 (캐시 워밍)
            saveToRedis(userFromDB.get());
        }

        return userFromDB;
    }
}

