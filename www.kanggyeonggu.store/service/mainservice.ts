// 소셜 로그인 핸들러 함수들 (IIFE 패턴)

import { getAccessToken, clearAccessToken } from '@/store/authStore';

// API URL 헬퍼 함수
const getApiBaseUrl = () => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'localhost:8080';
    // 이미 프로토콜이 있으면 그대로 사용, 없으면 추가
    if (baseUrl.startsWith('http://') || baseUrl.startsWith('https://')) {
        return baseUrl;
    }
    // localhost면 http, 아니면 https
    return baseUrl.includes('localhost') ? `http://${baseUrl}` : `https://${baseUrl}`;
};

export const createSocialLoginHandlers = (() => {
    // IIFE 내부: 공통 설정 및 변수 (private 스코프)
    const gatewayUrl = getApiBaseUrl();

    // 공통 로그인 처리 로직 (private 헬퍼 함수)
    async function handleLogin(
        provider: 'google' | 'kakao' | 'naver',
        setIsLoading: (loading: boolean) => void,
        setError: (error: string) => void
    ) {
        try {
            setIsLoading(true);
            setError('');

            // 디버깅: API URL 확인
            const apiUrl = `${gatewayUrl}/auth/${provider}/login`;
            console.log(`🔍 [${provider}] 로그인 요청 URL:`, apiUrl);
            console.log(`🔍 API URL 환경 변수:`, process.env.NEXT_PUBLIC_API_URL || '설정되지 않음 (기본값: localhost:8080)');

            // Gateway의 /auth/{provider}/login 엔드포인트 호출하여 로그인 URL 받기
            const response = await fetch(apiUrl, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (response.ok) {
                const data = await response.json();
                // 응답에서 authUrl을 받아 로그인 페이지로 리다이렉트
                // LoginResponse.success(authUrl) 형식: { success: true, message: "...", authUrl: "..." }
                if (data.success && data.authUrl) {
                    window.location.href = data.authUrl; // 받은 URL로 리다이렉트
                } else {
                    const providerName = provider === 'google' ? '구글' : provider === 'kakao' ? '카카오' : '네이버';
                    setError(`${providerName} 로그인 URL을 받아올 수 없습니다.`);
                    setIsLoading(false);
                }
            } else {
                const errorData = await response.json().catch(() => ({
                    message: `${provider === 'google' ? '구글' : provider === 'kakao' ? '카카오' : '네이버'} 로그인 준비에 실패했습니다.`
                }));
                setError(errorData.message || `${provider === 'google' ? '구글' : provider === 'kakao' ? '카카오' : '네이버'} 로그인 준비에 실패했습니다.`);
                setIsLoading(false);
            }
        } catch (err) {
            console.error(`❌ ${provider} 로그인 오류:`, err);
            console.error(`❌ 오류 상세:`, {
                message: err instanceof Error ? err.message : String(err),
                gatewayUrl: gatewayUrl,
                apiUrl: `${gatewayUrl}/auth/${provider}/login`,
                envVar: process.env.NEXT_PUBLIC_API_URL || '설정되지 않음'
            });

            // 더 구체적인 에러 메시지
            if (err instanceof TypeError && err.message === 'Failed to fetch') {
                setError(`서버에 연결할 수 없습니다. API URL을 확인해주세요: ${gatewayUrl}`);
            } else {
                setError('서버 연결에 실패했습니다.');
            }
            setIsLoading(false);
        }
    }

    // 이메일/비밀번호 로그인 처리 로직 (private 헬퍼 함수)
    async function handleEmailLogin(
        email: string,
        password: string,
        setIsLoading: (loading: boolean) => void,
        setError: (error: string) => void,
        onSuccess: () => void
    ) {
        try {
            setIsLoading(true);
            setError('');

            const response = await fetch(`${gatewayUrl}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({ email, password }),
            });

            if (response.ok) {
                onSuccess();
            } else {
                const data = await response.json();
                setError(data.message || '로그인에 실패했습니다.');
            }
        } catch (err) {
            setError('서버 연결에 실패했습니다.');
        } finally {
            setIsLoading(false);
        }
    }

    // 로그아웃 처리 로직 (private 헬퍼 함수)
    // 통합 로그아웃 API 사용 (/api/auth/logout)
    // - Refresh Token 쿠키 삭제 (백엔드에서 처리)
    // - Access Token 삭제 (Zustand에서 처리)
    async function handleLogout(
        token: string,
        onSuccess: () => void,
        onError?: (error: string) => void
    ) {
        try {
            console.log('🔄 로그아웃 시도...');

            // 통합 로그아웃 API 호출 (Refresh Token 쿠키 삭제)
            const response = await fetch(`${gatewayUrl}/api/auth/logout`, {
                method: 'POST',
                credentials: 'include', // HttpOnly 쿠키 전송
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    console.log('✅ 로그아웃 성공');
                }
            } else {
                console.warn('⚠️ 로그아웃 API 응답 오류:', response.status);
            }

            // Access Token 삭제 (Zustand 메모리에서)
            clearAccessToken();
            console.log('✅ Access Token 삭제 완료');

            onSuccess();

        } catch (err) {
            // 에러가 발생해도 토큰은 삭제하고 로그인 페이지로 이동
            console.warn('⚠️ 로그아웃 처리 중 오류:', err);
            clearAccessToken();
            onSuccess(); // 로그인 페이지로 이동
        }
    }

    // 팩토리 함수 반환 (public API)
    return (
        setIsGoogleLoading: (loading: boolean) => void,
        setIsKakaoLoading: (loading: boolean) => void,
        setIsNaverLoading: (loading: boolean) => void,
        setIsLoading: (loading: boolean) => void,
        setError: (error: string) => void
    ) => {
        // 구글 로그인 핸들러 (이너 함수 - 함수 선언식)
        function handleGoogleLogin() {
            handleLogin('google', setIsGoogleLoading, setError);
        }

        // 카카오 로그인 핸들러 (이너 함수 - 함수 선언식)
        function handleKakaoLogin() {
            handleLogin('kakao', setIsKakaoLoading, setError);
        }

        // 네이버 로그인 핸들러 (이너 함수 - 함수 선언식)
        function handleNaverLogin() {
            handleLogin('naver', setIsNaverLoading, setError);
        }

        // 이메일/비밀번호 로그인 핸들러 (이너 함수 - 함수 선언식)
        function handleEmailPasswordLogin(email: string, password: string, onSuccess: () => void) {
            handleEmailLogin(email, password, setIsLoading, setError, onSuccess);
        }

        // 로그아웃 핸들러 (이너 함수 - 함수 선언식)
        function handleLogoutRequest(onSuccess: () => void, onError?: (error: string) => void) {
            // Zustand 스토어에서 토큰 조회 (메모리)
            const token = getAccessToken();
            if (!token) {
                // 토큰이 없으면 바로 성공 처리 (이미 로그아웃된 상태)
                onSuccess();
                return;
            }
            handleLogout(token, onSuccess, onError);
        }

        // 이너 함수들을 객체로 반환
        return {
            handleGoogleLogin,
            handleKakaoLogin,
            handleNaverLogin,
            handleEmailPasswordLogin,
            handleLogout: handleLogoutRequest,
        };
    };
})();
