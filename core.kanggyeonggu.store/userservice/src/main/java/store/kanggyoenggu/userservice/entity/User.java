package store.kanggyoenggu.userservice.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import store.kanggyoenggu.userservice.listener.UserEntityListener;

import java.time.LocalDateTime;

/**
 * 소셜 로그인 사용자 정보를 저장하는 Entity
 */
@Entity
@Table(name = "users", uniqueConstraints = {
    @UniqueConstraint(columnNames = {"provider", "provider_id"})
})
@EntityListeners(UserEntityListener.class)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * OAuth 제공자 (kakao, naver, google)
     */
    @Column(name = "provider", nullable = false, length = 20)
    private String provider;

    /**
     * OAuth 제공자에서 제공하는 사용자 ID
     */
    @Column(name = "provider_id", nullable = false, length = 255)
    private String providerId;

    /**
     * 사용자 닉네임
     */
    @Column(name = "nickname", length = 100)
    private String nickname;

    /**
     * 사용자 이름
     */
    @Column(name = "name", length = 100)
    private String name;

    /**
     * 프로필 이미지 URL
     */
    @Column(name = "profile_image_url", length = 500)
    private String profileImageUrl;

    /**
     * 이메일 (제공되는 경우)
     */
    @Column(name = "email", length = 255)
    private String email;

    /**
     * 계정 생성 시간
     */
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    /**
     * 마지막 로그인 시간
     */
    @Column(name = "last_login_at")
    private LocalDateTime lastLoginAt;

    /**
     * 계정 활성화 여부
     */
    @Column(name = "enabled", nullable = false)
    @Builder.Default
    private Boolean enabled = true;

    /**
     * 삭제 여부 (Soft Delete)
     */
    @Column(name = "deleted", nullable = false)
    @Builder.Default
    private Boolean deleted = false;

    /**
     * 삭제 시간
     */
    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        if (lastLoginAt == null) {
            lastLoginAt = LocalDateTime.now();
        }
    }

    @PreUpdate
    protected void onUpdate() {
        lastLoginAt = LocalDateTime.now();
    }

    /**
     * Soft Delete 실행
     */
    public void softDelete() {
        this.deleted = true;
        this.deletedAt = LocalDateTime.now();
    }

    /**
     * Soft Delete 복구
     */
    public void restore() {
        this.deleted = false;
        this.deletedAt = null;
    }
}

