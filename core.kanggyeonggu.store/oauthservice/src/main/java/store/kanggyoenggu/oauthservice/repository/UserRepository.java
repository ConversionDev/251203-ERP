package store.kanggyoenggu.oauthservice.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import store.kanggyoenggu.oauthservice.entity.User;

import java.util.Optional;

/**
 * 사용자 정보를 관리하는 Repository
 */
@Repository
public interface UserRepository extends JpaRepository<User, Long>, UserRepositoryCustom {

    /**
     * OAuth 제공자와 제공자 ID로 사용자 조회 (삭제되지 않은 사용자만)
     * 
     * @param provider OAuth 제공자 (kakao, naver, google)
     * @param providerId OAuth 제공자에서 제공하는 사용자 ID
     * @return 사용자 정보 (Optional)
     */
    Optional<User> findByProviderAndProviderIdAndDeletedFalse(String provider, String providerId);

    /**
     * OAuth 제공자와 제공자 ID로 사용자 조회 (삭제된 사용자 포함)
     * 
     * @param provider OAuth 제공자 (kakao, naver, google)
     * @param providerId OAuth 제공자에서 제공하는 사용자 ID
     * @return 사용자 정보 (Optional)
     */
    Optional<User> findByProviderAndProviderId(String provider, String providerId);

    /**
     * 이메일로 사용자 조회 (삭제되지 않은 사용자만)
     * 
     * @param email 이메일 주소
     * @return 사용자 정보 (Optional)
     */
    Optional<User> findByEmailAndDeletedFalse(String email);

    /**
     * 이메일로 사용자 조회 (삭제된 사용자 포함)
     * 
     * @param email 이메일 주소
     * @return 사용자 정보 (Optional)
     */
    Optional<User> findByEmail(String email);

    /**
     * 삭제되지 않은 사용자 수 조회
     * 
     * @return 삭제되지 않은 사용자 수
     */
    long countByDeletedFalse();
}

