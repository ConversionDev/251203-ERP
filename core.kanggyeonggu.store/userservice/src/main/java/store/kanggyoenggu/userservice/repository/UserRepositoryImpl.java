package store.kanggyoenggu.userservice.repository;

import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

/**
 * UserRepository 커스텀 구현체
 * 시퀀스 리셋 등의 커스텀 메서드 구현
 */
@Repository
public class UserRepositoryImpl implements UserRepositoryCustom {

    @PersistenceContext
    private EntityManager entityManager;

    @Override
    @Transactional
    public void resetSequence() {
        // PostgreSQL 시퀀스 리셋
        entityManager.createNativeQuery("ALTER SEQUENCE users_id_seq RESTART WITH 1")
                .executeUpdate();
    }
}

