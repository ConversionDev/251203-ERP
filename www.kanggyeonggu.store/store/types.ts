/**
 * Auth Store 타입 정의 (덕스패턴)
 * 
 * 보안 원칙:
 * - Access Token: Zustand 메모리 저장 (XSS 방어)
 * - Refresh Token: HttpOnly 쿠키 (백엔드 관리)
 */

// ========================================
// 상태 타입
// ========================================
export interface AuthState {
    accessToken: string | null;
}

// ========================================
// 액션 타입
// ========================================
export interface AuthActions {
    setAccessToken: (token: string | null) => void;
    clearAccessToken: () => void;
    isAuthenticated: () => boolean;
}

// ========================================
// 스토어 타입 (상태 + 액션)
// ========================================
export type AuthStore = AuthState & AuthActions;

