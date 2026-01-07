'use client';

/**
 * Store Provider (Zustand + Next.js 16)
 * 
 * React Context를 사용하여 Zustand 스토어를 React 트리에 제공
 * SSR 환경에서 요청별 독립된 스토어 인스턴스 보장
 */

import { createContext, useContext, useRef, useEffect, type ReactNode } from 'react';
import { useStore } from 'zustand';
import { createAuthStore, type AuthStoreApi } from './authStore';
import type { AuthStore } from './types';

// ========================================
// 컴포넌트 외부에서 스토어 접근용 전역 변수
// (mainservice.ts 등에서 사용)
// ========================================
let globalStore: AuthStoreApi | null = null;

// ========================================
// Context 생성
// ========================================
const AuthStoreContext = createContext<AuthStoreApi | null>(null);

// ========================================
// Provider Props
// ========================================
interface StoreProviderProps {
    children: ReactNode;
}

// ========================================
// Store Provider 컴포넌트
// ========================================
export function StoreProvider({ children }: StoreProviderProps) {
    const storeRef = useRef<AuthStoreApi | null>(null);

    // 스토어 인스턴스가 없으면 생성 (한 번만)
    if (!storeRef.current) {
        storeRef.current = createAuthStore();
        // 전역 스토어 설정 (컴포넌트 외부에서 접근용)
        globalStore = storeRef.current;
    }

    // SSR/hydration 후에도 전역 스토어 동기화
    useEffect(() => {
        if (storeRef.current) {
            globalStore = storeRef.current;
        }
    }, []);

    return (
        <AuthStoreContext.Provider value={storeRef.current}>
            {children}
        </AuthStoreContext.Provider>
    );
}

// ========================================
// Custom Hook: useAuthStore
// 컴포넌트에서 스토어 접근에 사용
// ========================================
export function useAuthStore<T>(selector: (state: AuthStore) => T): T {
    const store = useContext(AuthStoreContext);

    if (!store) {
        throw new Error('useAuthStore must be used within StoreProvider');
    }

    return useStore(store, selector);
}

// ========================================
// 전체 스토어 접근 Hook
// ========================================
export function useAuthStoreApi(): AuthStoreApi {
    const store = useContext(AuthStoreContext);

    if (!store) {
        throw new Error('useAuthStoreApi must be used within StoreProvider');
    }

    return store;
}

// ========================================
// 헬퍼 함수들 (컴포넌트 외부용)
// mainservice.ts 등에서 사용
// ========================================
export const getAccessToken = () => globalStore?.getState().accessToken ?? null;
export const setAccessToken = (token: string | null) => globalStore?.getState().setAccessToken(token);
export const clearAccessToken = () => globalStore?.getState().clearAccessToken();

