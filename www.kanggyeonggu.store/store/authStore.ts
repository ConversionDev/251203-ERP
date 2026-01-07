/**
 * Auth Store (Zustand + Next.js 16 + 덕스패턴)
 * 
 * 보안 원칙:
 * - Access Token은 브라우저 메모리(Zustand state)에만 저장
 * - localStorage/sessionStorage 사용 금지 (XSS 취약)
 * - Refresh Token은 HttpOnly 쿠키로 백엔드에서 관리
 */

import { createStore } from 'zustand';
import type { AuthStore } from './types';

// ========================================
// 스토어 팩토리 함수
// Provider에서 요청별 독립 인스턴스 생성에 사용
// ========================================
export const createAuthStore = () => {
    return createStore<AuthStore>((set, get) => ({
        // 상태
        accessToken: null,

        // 액션
        setAccessToken: (token) => {
            console.log('🔐 [Zustand] 토큰 저장:', token ? token.substring(0, 20) + '...' : 'null');
            set({ accessToken: token });
        },

        clearAccessToken: () => {
            console.log('🗑️ [Zustand] 토큰 삭제');
            set({ accessToken: null });
        },

        isAuthenticated: () => !!get().accessToken,
    }));
};

// ========================================
// 스토어 타입 export
// ========================================
export type AuthStoreApi = ReturnType<typeof createAuthStore>;
