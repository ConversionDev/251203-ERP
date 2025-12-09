package store.kanggyoenggu.userservice.listener;

import jakarta.persistence.PostRemove;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeansException;
import org.springframework.context.ApplicationContext;
import org.springframework.context.ApplicationContextAware;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;
import store.kanggyoenggu.userservice.entity.User;
import store.kanggyoenggu.userservice.repository.UserRepository;

/**
 * User 엔티티의 생명주기 이벤트를 처리하는 리스너
 * 삭제 후 시퀀스를 자동으로 리셋
 * 
 * 주의: 개발/테스트 환경에서만 활성화됩니다.
 * 프로덕션 환경에서는 ID 재사용을 방지하기 위해 비활성화됩니다.
 */
@Slf4j
@Component
@Profile({"dev", "test", "local"}) // 개발/테스트 환경에서만 활성화
public class UserEntityListener implements ApplicationContextAware {

    private static ApplicationContext applicationContext;

    @Override
    public void setApplicationContext(ApplicationContext applicationContext) throws BeansException {
        UserEntityListener.applicationContext = applicationContext;
    }

    /**
     * User 엔티티 삭제 후 호출되는 메서드
     * 모든 사용자가 삭제되면 시퀀스를 1로 리셋
     */
    @PostRemove
    public void afterUserRemoved(User user) {
        try {
            if (applicationContext == null) {
                log.warn("ApplicationContext가 설정되지 않아 시퀀스 리셋을 건너뜁니다.");
                return;
            }

            UserRepository userRepository = applicationContext.getBean(UserRepository.class);
            
            // 남은 사용자 수 확인 (삭제되지 않은 사용자만)
            long remainingCount = userRepository.countByDeletedFalse();
            
            log.info("User 삭제됨: ID={}, 닉네임={}, 남은 활성 사용자 수={}", 
                    user.getId(), user.getNickname(), remainingCount);
            
            // 모든 활성 사용자가 삭제되었으면 시퀀스 리셋 (개발 환경에서만)
            if (remainingCount == 0) {
                log.info("모든 활성 사용자가 삭제되어 시퀀스를 1로 리셋합니다. (개발 환경 전용)");
                // UserRepositoryCustom으로 캐스팅하여 resetSequence 호출
                if (userRepository instanceof store.kanggyoenggu.userservice.repository.UserRepositoryCustom) {
                    ((store.kanggyoenggu.userservice.repository.UserRepositoryCustom) userRepository).resetSequence();
                }
            }
        } catch (Exception e) {
            log.error("시퀀스 리셋 중 오류 발생: {}", e.getMessage(), e);
            // 시퀀스 리셋 실패해도 삭제는 정상적으로 완료되도록 예외를 던지지 않음
        }
    }
}

