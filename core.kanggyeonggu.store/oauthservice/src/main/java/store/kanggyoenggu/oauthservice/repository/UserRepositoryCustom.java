package store.kanggyoenggu.oauthservice.repository;

/**
 * UserRepository 커스텀 인터페이스
 * 시퀀스 리셋 등의 커스텀 메서드 정의
 */
public interface UserRepositoryCustom {

    /**
     * 시퀀스를 1로 리셋
     */
    void resetSequence();
}
