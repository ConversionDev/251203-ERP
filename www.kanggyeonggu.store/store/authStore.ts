/**
 * Access Token 저장소 (Zustand)
 * 
 * 보안 원칙:
 * - Access Token은 브라우저 메모리(Zustand state)에만 저장
 * - localStorage/sessionStorage 사용 금지 (XSS 취약)
 * - 페이지 새로고침 시 Refresh Token(HttpOnly 쿠키)으로 갱신
 * 
 * 토큰 전략:
 * - Access Token: Zustand 메모리 저장 (짧은 수명, 5~15분)
 * - Refresh Token: HttpOnly 쿠키 (백엔드에서 설정, 긴 수명, 7일)
 */

import { create } from 'zustand';

interface AuthState {
    // 상태
    accessToken: string | null;
    isRefreshing: boolean;

    // 액션
    setAccessToken: (token: string | null) => void;
    clearAccessToken: () => void;
    isAuthenticated: () => boolean;
    refreshAccessToken: () => Promise<boolean>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
    accessToken: null,
    isRefreshing: false,

    setAccessToken: (token) => {
        console.log('🔐 [Zustand] 토큰 저장:', token ? token.substring(0, 20) + '...' : 'null');
        set({ accessToken: token });
    },

    clearAccessToken: () => {
        console.log('🗑️ [Zustand] 토큰 삭제');
        set({ accessToken: null });
    },

    isAuthenticated: () => !!get().accessToken,

    /**
     * Refresh Token으로 Access Token 갱신
     * 
     * HttpOnly 쿠키에 저장된 Refresh Token을 사용하여
     * 새 Access Token을 발급받습니다.
     * 
     * @returns 갱신 성공 여부
     */
    refreshAccessToken: async () => {
        // 이미 갱신 중이면 중복 요청 방지
        if (get().isRefreshing) {
            console.log('⏳ [Zustand] 이미 토큰 갱신 중...');
            return false;
        }

        set({ isRefreshing: true });

        try {
            // API URL 생성
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'localhost:8080';
            const gatewayUrl = baseUrl.startsWith('http://') || baseUrl.startsWith('https://')
                ? baseUrl
                : (baseUrl.includes('localhost') ? `http://${baseUrl}` : `https://${baseUrl}`);
            console.log('🔄 [Zustand] Access Token 갱신 시도... API URL:', gatewayUrl);

            const response = await fetch(`${gatewayUrl}/api/auth/refresh`, {
                method: 'POST',
                credentials: 'include', // HttpOnly 쿠키 자동 전송
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success && data.accessToken) {
                    set({ accessToken: data.accessToken });
                    console.log('✅ [Zustand] Access Token 갱신 성공');
                    return true;
                }
            }

            console.log('❌ [Zustand] Access Token 갱신 실패:', response.status);
            return false;

        } catch (error) {
            console.error('❌ [Zustand] Token refresh 오류:', error);
            return false;
        } finally {
            set({ isRefreshing: false });
        }
    },
}));

// ========================================
// 컴포넌트 외부에서 사용 (mainservice.ts 등)
// React 훅이 아닌 일반 함수에서 상태 접근 시 사용
// ========================================
export const getAccessToken = () => useAuthStore.getState().accessToken;
export const setAccessToken = (token: string | null) => useAuthStore.getState().setAccessToken(token);
export const clearAccessToken = () => useAuthStore.getState().clearAccessToken();
export const refreshAccessToken = () => useAuthStore.getState().refreshAccessToken();
