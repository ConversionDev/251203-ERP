'use client';

import { useState, useRef, useCallback, useEffect } from 'react';

interface UploadedFile {
    id: string;
    file: File;
    preview?: string;
    uploadTime: Date;
    serverPath?: string;
    detectedImage?: string | null;
    segmentedImage?: string | null;
    poseImage?: string | null;
    classifiedImage?: string | null;
    faceCount?: number;
    confidence?: number;
    dogCount?: number;
    catCount?: number;
    totalCount?: number;
    lastProcessedType?: 'detect' | 'segment' | 'pose' | 'classify' | null;
    lastProcessedTime?: Date | null;
}

interface FileUploadProps {
    onUploadComplete?: (file: File) => void;
    onUploadError?: (error: string) => void;
}

export default function FileUpload({ onUploadComplete, onUploadError }: FileUploadProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [isDragging, setIsDragging] = useState(false);
    const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
    const [uploadingIds, setUploadingIds] = useState<Set<string>>(new Set());
    const [portfolioFiles, setPortfolioFiles] = useState<UploadedFile[]>([]);
    const [detectingIds, setDetectingIds] = useState<Set<string>>(new Set());
    const [segmentingIds, setSegmentingIds] = useState<Set<string>>(new Set());
    const [posingIds, setPosingIds] = useState<Set<string>>(new Set());
    const [classifyingIds, setClassifyingIds] = useState<Set<string>>(new Set());
    const fileInputRef = useRef<HTMLInputElement>(null);

    const formatFileSize = (bytes: number): string => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
        return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
    };

    const isImageFile = (file: File): boolean => {
        return file.type.startsWith('image/');
    };

    const createPreview = (file: File): Promise<string> => {
        return new Promise((resolve) => {
            if (isImageFile(file)) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    resolve(e.target?.result as string);
                };
                reader.readAsDataURL(file);
            } else {
                resolve('');
            }
        });
    };

    const handleFileSelect = useCallback(async (files: FileList | null) => {
        if (!files || files.length === 0) return;

        const fileArray = Array.from(files);
        const newFiles: UploadedFile[] = [];

        for (const file of fileArray) {
            const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
            const preview = await createPreview(file);

            const uploadedFile: UploadedFile = {
                id,
                file,
                preview,
                uploadTime: new Date(),
            };

            newFiles.push(uploadedFile);
            setUploadedFiles(prev => [...prev, uploadedFile]);
            setUploadingIds(prev => new Set(prev).add(id));

            try {
                const formData = new FormData();
                formData.append('file', file);

                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData,
                });

                // 서버가 종료되었거나 연결할 수 없는 경우 (503 Service Unavailable)
                if (response.status === 503) {
                    const errorData = await response.json();
                    console.warn('FastAPI 서버가 실행되지 않았습니다.');
                    setUploadedFiles(prev => prev.filter(f => f.id !== id));
                    alert(`서버가 실행되지 않았습니다.\n\n${errorData.details || 'FastAPI 서버를 시작한 후 다시 시도해주세요.'}`);
                    return;
                }

                if (!response.ok) {
                    throw new Error('파일 업로드에 실패했습니다.');
                }

                const data = await response.json();
                uploadedFile.serverPath = data.file?.path;

                setUploadedFiles(prev => prev.map(f =>
                    f.id === id ? {
                        ...f,
                        serverPath: data.file?.path,
                    } : f
                ));

                onUploadComplete?.(file);
            } catch (error: any) {
                console.error('업로드 오류:', error);

                // 네트워크 오류나 서버 연결 실패 시
                if (error.message?.includes('fetch failed') ||
                    error.message?.includes('Failed to fetch') ||
                    error.message?.includes('NetworkError')) {
                    setUploadedFiles(prev => prev.filter(f => f.id !== id));
                    alert('서버에 연결할 수 없습니다.\n\nFastAPI 서버가 실행 중인지 확인해주세요.\n(python app/yolo/yolo_main.py)');
                    return;
                }

                const errorMessage = error instanceof Error ? error.message : '파일 업로드 중 오류가 발생했습니다.';
                onUploadError?.(errorMessage);
                setUploadedFiles(prev => prev.filter(f => f.id !== id));
            } finally {
                setUploadingIds(prev => {
                    const newSet = new Set(prev);
                    newSet.delete(id);
                    return newSet;
                });
            }
        }
    }, [onUploadComplete, onUploadError]);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            handleFileSelect(files);
        }
    }, [handleFileSelect]);

    const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        handleFileSelect(e.target.files);
        // 같은 파일을 다시 선택할 수 있도록 input 초기화
        if (e.target) {
            e.target.value = '';
        }
    }, [handleFileSelect]);

    const handleRemoveFile = useCallback(async (id: string) => {
        const file = uploadedFiles.find(f => f.id === id);
        if (!file) return;

        try {
            const fastApiUrl = process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000';

            // 백엔드에서 파일 삭제
            const filename = encodeURIComponent(file.file.name);
            console.log('파일 삭제 시도:', { filename: file.file.name, encoded: filename, url: `${fastApiUrl}/api/delete/${filename}` });

            const response = await fetch(`${fastApiUrl}/api/delete/${filename}`, {
                method: 'DELETE',
                headers: {
                    'Accept': 'application/json',
                },
            });

            console.log('삭제 응답 상태:', response.status, response.statusText);

            if (!response.ok) {
                let errorMessage = `파일 삭제 실패 (${response.status})`;

                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorMessage;
                    console.error('파일 삭제 실패 응답:', errorData);
                } catch (parseError) {
                    const text = await response.text();
                    console.error('파일 삭제 실패 (JSON 파싱 불가):', text);
                    errorMessage = text || errorMessage;
                }

                // 404는 파일이 이미 없을 수 있으므로 무시하고 프론트엔드에서만 삭제
                if (response.status === 404) {
                    console.warn('파일이 서버에 없습니다:', file.file.name);
                } else {
                    console.error('파일 삭제 실패:', {
                        status: response.status,
                        statusText: response.statusText,
                        message: errorMessage,
                        filename: file.file.name,
                    });
                    alert(`파일 삭제에 실패했습니다.\n\n상태: ${response.status}\n오류: ${errorMessage}\n\n브라우저 콘솔을 확인해주세요.`);
                    return; // 실패 시 프론트엔드에서도 삭제하지 않음
                }
            } else {
                const data = await response.json();
                console.log('파일 삭제 성공:', data.message);
            }

            // 디텍션된 이미지도 삭제 (있는 경우)
            if (file.detectedImage) {
                try {
                    const detectedFilename = encodeURIComponent(file.detectedImage);
                    const detectedResponse = await fetch(`${fastApiUrl}/api/delete/${detectedFilename}`, {
                        method: 'DELETE',
                    });

                    if (detectedResponse.ok) {
                        const detectedData = await detectedResponse.json();
                        console.log('디텍션 파일 삭제 성공:', detectedData.message);
                    } else {
                        console.warn('디텍션 파일 삭제 실패:', detectedResponse.status);
                    }
                } catch (error) {
                    console.warn('디텍션 파일 삭제 오류:', error);
                }
            }

            // 프론트엔드 상태에서 제거 (성공 또는 404인 경우만)
            setUploadedFiles(prev => prev.filter(f => f.id !== id));
            setPortfolioFiles(prev => prev.filter(f => f.id !== id));
        } catch (error: any) {
            console.error('파일 삭제 오류:', error);

            // 네트워크 오류 확인
            if (error.message?.includes('fetch failed') ||
                error.message?.includes('Failed to fetch') ||
                error.message?.includes('NetworkError') ||
                error.code === 'ECONNREFUSED') {
                alert('서버에 연결할 수 없습니다.\n\nFastAPI 서버가 실행 중인지 확인해주세요.\n\n(python app/yolo/yolo_main.py)');
                return; // 네트워크 오류 시 프론트엔드에서도 삭제하지 않음
            }

            // 기타 오류
            const errorMessage = error.message || '알 수 없는 오류';
            console.error('파일 삭제 상세 오류:', {
                error,
                filename: file.file.name,
                message: errorMessage,
            });
            alert(`파일 삭제 중 오류가 발생했습니다.\n\n${errorMessage}\n\n브라우저 콘솔을 확인해주세요.`);
            return; // 오류 시 프론트엔드에서도 삭제하지 않음
        }
    }, [uploadedFiles]);

    const handleDetect = useCallback(async () => {
        // 디텍션이 완료되지 않은 이미지 파일들을 찾아서 디텍션 수행
        const filesToDetect = uploadedFiles.filter(
            file => isImageFile(file.file) && !file.detectedImage && !detectingIds.has(file.id)
        );

        if (filesToDetect.length === 0) {
            alert('디텍션할 이미지가 없습니다.');
            return;
        }

        // 디텍션 수행
        for (const file of filesToDetect) {
            setDetectingIds(prev => new Set(prev).add(file.id));

            try {
                const response = await fetch('/api/detect', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ filename: file.file.name }),
                });

                // 서버가 종료되었거나 연결할 수 없는 경우 (503 Service Unavailable)
                if (response.status === 503) {
                    console.warn('FastAPI 서버가 실행되지 않았습니다. 상태를 초기화합니다.');
                    setUploadedFiles([]);
                    setPortfolioFiles([]);
                    setDetectingIds(new Set());
                    alert('서버가 실행되지 않았습니다. 서버를 시작한 후 다시 시도해주세요.');
                    return;
                }

                if (!response.ok) {
                    throw new Error('디텍션에 실패했습니다.');
                }

                const data = await response.json();

                // 업로드된 파일 목록 업데이트
                setUploadedFiles(prev => prev.map(f =>
                    f.id === file.id
                        ? {
                            ...f,
                            detectedImage: data.file?.detectedImage || null,
                            faceCount: data.file?.faceCount || 0,
                        }
                        : f
                ));
            } catch (error: any) {
                console.error('디텍션 오류:', error);

                // 네트워크 오류나 서버 연결 실패 시 상태 초기화
                if (error.message?.includes('fetch failed') ||
                    error.message?.includes('Failed to fetch') ||
                    error.message?.includes('NetworkError')) {
                    console.warn('서버 연결 실패. 상태를 초기화합니다.');
                    setUploadedFiles([]);
                    setPortfolioFiles([]);
                    setDetectingIds(new Set());
                    alert('서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.');
                    return;
                }

                alert(`파일 "${file.file.name}"의 디텍션에 실패했습니다.`);
            } finally {
                setDetectingIds(prev => {
                    const newSet = new Set(prev);
                    newSet.delete(file.id);
                    return newSet;
                });
            }
        }
    }, [uploadedFiles, detectingIds]);

    const handleSegment = useCallback(async () => {
        // 세그먼테이션할 이미지 파일들을 찾기 (디텍트 결과와 무관하게 원본 파일 사용)
        const filesToSegment = uploadedFiles.filter(
            file => isImageFile(file.file) && !file.segmentedImage && !segmentingIds.has(file.id)
        );

        if (filesToSegment.length === 0) {
            alert('세그먼테이션할 이미지가 없습니다.');
            return;
        }

        // 세그먼테이션 수행
        for (const file of filesToSegment) {
            setSegmentingIds(prev => new Set(prev).add(file.id));

            try {
                const response = await fetch('/api/segment', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ filename: file.file.name }),
                });

                // 서버가 종료되었거나 연결할 수 없는 경우 (503 Service Unavailable)
                if (response.status === 503) {
                    console.warn('FastAPI 서버가 실행되지 않았습니다. 상태를 초기화합니다.');
                    setUploadedFiles([]);
                    setPortfolioFiles([]);
                    setSegmentingIds(new Set());
                    alert('서버가 실행되지 않았습니다. 서버를 시작한 후 다시 시도해주세요.');
                    return;
                }

                if (!response.ok) {
                    throw new Error('세그먼테이션에 실패했습니다.');
                }

                const data = await response.json();

                // 업로드된 파일 목록 업데이트
                setUploadedFiles(prev => prev.map(f =>
                    f.id === file.id
                        ? {
                            ...f,
                            segmentedImage: data.file?.segmentedImage || null,
                            confidence: data.file?.confidence || 0,
                            lastProcessedType: 'segment',
                            lastProcessedTime: new Date(),
                        }
                        : f
                ));
            } catch (error: any) {
                console.error('세그먼테이션 오류:', error);

                // 네트워크 오류나 서버 연결 실패 시 상태 초기화
                if (error.message?.includes('fetch failed') ||
                    error.message?.includes('Failed to fetch') ||
                    error.message?.includes('NetworkError')) {
                    console.warn('서버 연결 실패. 상태를 초기화합니다.');
                    setUploadedFiles([]);
                    setPortfolioFiles([]);
                    setSegmentingIds(new Set());
                    alert('서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.');
                    return;
                }

                alert(`파일 "${file.file.name}"의 세그먼테이션에 실패했습니다.`);
            } finally {
                setSegmentingIds(prev => {
                    const newSet = new Set(prev);
                    newSet.delete(file.id);
                    return newSet;
                });
            }
        }
    }, [uploadedFiles, segmentingIds]);

    const handlePose = useCallback(async () => {
        // 포즈 추정할 이미지 파일들을 찾기 (디텍트 결과와 무관하게 원본 파일 사용)
        const filesToPose = uploadedFiles.filter(
            file => isImageFile(file.file) && !file.poseImage && !posingIds.has(file.id)
        );

        if (filesToPose.length === 0) {
            alert('포즈 추정할 이미지가 없습니다.');
            return;
        }

        // 포즈 추정 수행
        for (const file of filesToPose) {
            setPosingIds(prev => new Set(prev).add(file.id));

            try {
                const response = await fetch('/api/pose', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ filename: file.file.name }),
                });

                // 서버가 종료되었거나 연결할 수 없는 경우 (503 Service Unavailable)
                if (response.status === 503) {
                    console.warn('FastAPI 서버가 실행되지 않았습니다. 상태를 초기화합니다.');
                    setUploadedFiles([]);
                    setPortfolioFiles([]);
                    setPosingIds(new Set());
                    alert('서버가 실행되지 않았습니다. 서버를 시작한 후 다시 시도해주세요.');
                    return;
                }

                if (!response.ok) {
                    throw new Error('포즈 추정에 실패했습니다.');
                }

                const data = await response.json();

                // 업로드된 파일 목록 업데이트
                setUploadedFiles(prev => prev.map(f =>
                    f.id === file.id
                        ? {
                            ...f,
                            poseImage: data.file?.poseImage || null,
                            confidence: data.file?.confidence || 0,
                            lastProcessedType: 'pose',
                            lastProcessedTime: new Date(),
                        }
                        : f
                ));
            } catch (error: any) {
                console.error('포즈 추정 오류:', error);

                // 네트워크 오류나 서버 연결 실패 시 상태 초기화
                if (error.message?.includes('fetch failed') ||
                    error.message?.includes('Failed to fetch') ||
                    error.message?.includes('NetworkError')) {
                    console.warn('서버 연결 실패. 상태를 초기화합니다.');
                    setUploadedFiles([]);
                    setPortfolioFiles([]);
                    setPosingIds(new Set());
                    alert('서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.');
                    return;
                }

                alert(`파일 "${file.file.name}"의 포즈 추정에 실패했습니다.`);
            } finally {
                setPosingIds(prev => {
                    const newSet = new Set(prev);
                    newSet.delete(file.id);
                    return newSet;
                });
            }
        }
    }, [uploadedFiles, posingIds]);

    const handleClassify = useCallback(async () => {
        // 분류할 이미지 파일들을 찾기
        const filesToClassify = uploadedFiles.filter(
            file => isImageFile(file.file) && !file.classifiedImage && !classifyingIds.has(file.id)
        );

        if (filesToClassify.length === 0) {
            alert('분류할 이미지가 없습니다.');
            return;
        }

        // 분류 수행
        for (const file of filesToClassify) {
            setClassifyingIds(prev => new Set(prev).add(file.id));

            try {
                const response = await fetch('/api/classify', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ filename: file.file.name }),
                });

                // 서버가 종료되었거나 연결할 수 없는 경우 (503 Service Unavailable)
                if (response.status === 503) {
                    console.warn('FastAPI 서버가 실행되지 않았습니다. 상태를 초기화합니다.');
                    setUploadedFiles([]);
                    setPortfolioFiles([]);
                    setClassifyingIds(new Set());
                    alert('서버가 실행되지 않았습니다. 서버를 시작한 후 다시 시도해주세요.');
                    return;
                }

                if (!response.ok) {
                    // 서버 오류 메시지 추출
                    let errorMessage = '분류에 실패했습니다.';
                    try {
                        const errorData = await response.json();
                        errorMessage = errorData.error || errorData.detail || errorMessage;
                    } catch {
                        const errorText = await response.text();
                        errorMessage = errorText || errorMessage;
                    }
                    console.error('분류 API 오류:', {
                        status: response.status,
                        statusText: response.statusText,
                        error: errorMessage
                    });
                    throw new Error(errorMessage);
                }

                const data = await response.json();

                // 업로드된 파일 목록 업데이트
                setUploadedFiles(prev => prev.map(f =>
                    f.id === file.id
                        ? {
                            ...f,
                            classifiedImage: data.file?.classifiedImage || null,
                            dogCount: data.file?.dogCount || 0,
                            catCount: data.file?.catCount || 0,
                            totalCount: data.file?.totalCount || 0,
                            confidence: data.file?.confidence || 0,
                            lastProcessedType: 'classify',
                            lastProcessedTime: new Date(),
                        }
                        : f
                ));
            } catch (error: any) {
                console.error('분류 오류:', error);

                // 네트워크 오류나 서버 연결 실패 시 상태 초기화
                if (error.message?.includes('fetch failed') ||
                    error.message?.includes('Failed to fetch') ||
                    error.message?.includes('NetworkError')) {
                    console.warn('서버 연결 실패. 상태를 초기화합니다.');
                    setUploadedFiles([]);
                    setPortfolioFiles([]);
                    setClassifyingIds(new Set());
                    alert('서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.');
                    return;
                }

                alert(`파일 "${file.file.name}"의 분류에 실패했습니다.`);
            } finally {
                setClassifyingIds(prev => {
                    const newSet = new Set(prev);
                    newSet.delete(file.id);
                    return newSet;
                });
            }
        }
    }, [uploadedFiles, classifyingIds]);

    // 가장 최근 처리 결과를 반환하는 헬퍼 함수
    const getLatestResult = useCallback((file: UploadedFile) => {
        const results = [
            { type: 'classify' as const, image: file.classifiedImage, time: file.lastProcessedType === 'classify' ? file.lastProcessedTime : null },
            { type: 'pose' as const, image: file.poseImage, time: file.lastProcessedType === 'pose' ? file.lastProcessedTime : null },
            { type: 'segment' as const, image: file.segmentedImage, time: file.lastProcessedType === 'segment' ? file.lastProcessedTime : null },
            { type: 'detect' as const, image: file.detectedImage, time: file.lastProcessedType === 'detect' ? file.lastProcessedTime : null },
        ].filter(r => r.image !== null && r.image !== undefined);

        if (results.length === 0) return null;

        // 타임스탬프가 있는 것 중 가장 최근 것, 없으면 첫 번째
        return results.reduce((latest, current) => {
            if (current.time && latest.time) {
                return current.time > latest.time ? current : latest;
            }
            return current.time ? current : latest;
        });
    }, []);

    const handleReset = useCallback(() => {
        // 프론트엔드 상태만 초기화 (서버 파일은 유지)
        setUploadedFiles([]);
        setPortfolioFiles([]);
        setDetectingIds(new Set());
        setSegmentingIds(new Set());
        setPosingIds(new Set());
        setUploadingIds(new Set());
    }, []);

    const handleRemoveAll = useCallback(async () => {
        if (uploadedFiles.length === 0) return;
        if (!confirm('업로드된 모든 파일을 삭제하시겠습니까?')) return;

        try {
            const fastApiUrl = process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000';
            console.log('전체 파일 삭제 시도:', `${fastApiUrl}/api/delete-all`);

            // 백엔드에서 모든 파일 삭제
            const response = await fetch(`${fastApiUrl}/api/delete-all`, {
                method: 'DELETE',
                headers: {
                    'Accept': 'application/json',
                },
            });

            console.log('전체 삭제 응답 상태:', response.status, response.statusText);

            if (!response.ok) {
                let errorMessage = `파일 삭제 실패 (${response.status})`;

                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorMessage;
                    console.error('전체 파일 삭제 실패 응답:', errorData);
                } catch (parseError) {
                    const text = await response.text();
                    console.error('전체 파일 삭제 실패 (JSON 파싱 불가):', text);
                    errorMessage = text || errorMessage;
                }

                alert(`전체 파일 삭제에 실패했습니다.\n\n상태: ${response.status}\n오류: ${errorMessage}\n\n브라우저 콘솔을 확인해주세요.`);
                return; // 실패 시 프론트엔드에서도 삭제하지 않음
            }

            const data = await response.json();
            console.log('전체 파일 삭제 완료:', data);

            // 프론트엔드 상태 초기화
            setUploadedFiles([]);
            setPortfolioFiles([]);
            setDetectingIds(new Set());
        } catch (error: any) {
            console.error('전체 파일 삭제 오류:', error);
            console.error('오류 상세:', {
                name: error.name,
                message: error.message,
                stack: error.stack,
            });

            // 네트워크 오류 확인 (더 포괄적으로)
            const isNetworkError =
                error.message?.includes('fetch failed') ||
                error.message?.includes('Failed to fetch') ||
                error.message?.includes('NetworkError') ||
                error.message?.includes('ERR_FAILED') ||
                error.message?.includes('ERR_CONNECTION_REFUSED') ||
                error.message?.includes('ERR_INTERNET_DISCONNECTED') ||
                error.code === 'ECONNREFUSED' ||
                error.name === 'TypeError';

            if (isNetworkError) {
                alert(
                    '서버에 연결할 수 없습니다.\n\n' +
                    'FastAPI 서버가 실행 중인지 확인해주세요.\n\n' +
                    '서버 실행 방법:\n' +
                    'cd cv.kanggyeonggu.store\n' +
                    'python app/yolo/yolo_main.py\n\n' +
                    '또는\n' +
                    'uvicorn app.yolo.yolo_main:app --host 0.0.0.0 --port 8000'
                );
                return; // 네트워크 오류 시 프론트엔드에서도 삭제하지 않음
            }

            // 기타 오류
            const errorMessage = error.message || '알 수 없는 오류';
            alert(`전체 파일 삭제 중 오류가 발생했습니다.\n\n${errorMessage}\n\n브라우저 콘솔을 확인해주세요.`);
            return; // 오류 시 프론트엔드에서도 삭제하지 않음
        }
    }, [uploadedFiles]);

    const handleRemoveAllPortfolio = useCallback(() => {
        if (portfolioFiles.length === 0) return;
        if (confirm('포트폴리오의 모든 파일을 삭제하시겠습니까?')) {
            setPortfolioFiles([]);
        }
    }, [portfolioFiles]);

    const handleDownload = useCallback(async (file: UploadedFile, isDetected: boolean = false) => {
        try {
            const filename = isDetected && file.detectedImage
                ? file.detectedImage
                : file.file.name;

            // FastAPI 서버에서 이미지 다운로드
            const fastApiUrl = process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000';
            const imageUrl = `${fastApiUrl}/api/images/${encodeURIComponent(filename)}`;

            // 새 창에서 이미지 열기
            window.open(imageUrl, '_blank');
        } catch (error) {
            console.error('다운로드 오류:', error);
            alert('이미지 다운로드에 실패했습니다.');
        }
    }, []);

    const handleImageClick = useCallback((uploadedFile: UploadedFile) => {
        // 이미지 파일이 아니면 안내 메시지만 표시
        if (!isImageFile(uploadedFile.file)) {
            return;
        }

        // yolo_main.py가 자동으로 처리한다는 안내 메시지
        alert(
            '파일이 업로드되었습니다.\n\n' +
            '얼굴 디텍션은 자동으로 수행됩니다.\n\n' +
            '디텍션 결과를 확인하려면:\n' +
            '1. cv.kanggyeonggu.store/app/data/yolo 폴더를 확인하세요\n' +
            '2. {원본파일명}_detected.{확장자} 형식의 파일이 생성됩니다\n\n' +
            'yolo_main.py가 실행 중이어야 자동 디텍션이 수행됩니다.'
        );
    }, []);

    const handleButtonClick = () => {
        setIsOpen(true);
    };

    const handleClose = () => {
        if (uploadingIds.size === 0) {
            setIsOpen(false);
        }
    };

    return (
        <>
            {/* 업로드 버튼 */}
            <button
                onClick={handleButtonClick}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                title="파일 업로드"
            >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <span className="hidden sm:inline">파일 업로드</span>
            </button>

            {/* 모달 오버레이 */}
            {isOpen && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4"
                    onClick={handleClose}
                >
                    {/* 모달 컨텐츠 */}
                    <div
                        className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* 모달 헤더 */}
                        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                            <h2 className="text-xl font-bold text-gray-900 dark:text-white">포트폴리오 업로드</h2>
                            <button
                                onClick={handleClose}
                                disabled={uploadingIds.size > 0}
                                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <svg className="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        <div className="p-6">
                            {/* 드래그앤드롭 영역 */}
                            <div
                                onDragOver={handleDragOver}
                                onDragLeave={handleDragLeave}
                                onDrop={handleDrop}
                                className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${isDragging
                                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                                    : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900/50'
                                    }`}
                            >
                                <svg className="w-20 h-20 text-yellow-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                                </svg>
                                <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                                    파일을 여기에 드래그하세요
                                </p>
                                <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                                    또는 클릭하여 파일을 선택하세요
                                </p>
                                <button
                                    onClick={() => fileInputRef.current?.click()}
                                    className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
                                >
                                    파일 선택
                                </button>
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    multiple
                                    className="hidden"
                                    onChange={handleFileInputChange}
                                />
                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-4">
                                    지원 형식: JPG, PNG, GIF, WebP, PDF, TXT (최대 10MB)
                                </p>
                            </div>

                            {/* 업로드된 파일 목록 */}
                            {uploadedFiles.length > 0 && (
                                <div className="mt-8">
                                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                                        업로드된 파일 ({uploadedFiles.length}개)
                                    </h3>
                                    <div className="flex gap-4">
                                        {/* 왼쪽 반: 원본 이미지 + 파일 정보 */}
                                        {uploadedFiles[0].preview && (
                                            <div className="flex-1 flex flex-col rounded-lg border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800">
                                                {/* 파일 정보 및 다운로드 버튼 */}
                                                <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                                                    <div className="flex items-center justify-between mb-3">
                                                        <div className="flex items-center gap-2">
                                                            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                                            </svg>
                                                            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                                                {uploadedFiles[0].file.name}
                                                            </p>
                                                            <button
                                                                onClick={() => handleRemoveFile(uploadedFiles[0].id)}
                                                                className="w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors ml-auto"
                                                                disabled={uploadingIds.has(uploadedFiles[0].id) || detectingIds.has(uploadedFiles[0].id)}
                                                            >
                                                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                                                </svg>
                                                            </button>
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center justify-between">
                                                        <div className="text-xs text-gray-500 dark:text-gray-400">
                                                            <p>{formatFileSize(uploadedFiles[0].file.size)}</p>
                                                            <p className="mt-1">{uploadedFiles[0].uploadTime.toLocaleString('ko-KR')}</p>
                                                            {uploadedFiles[0].faceCount !== undefined && uploadedFiles[0].faceCount > 0 && (
                                                                <p className="text-green-600 dark:text-green-400 mt-1 font-medium">
                                                                    탐지된 얼굴: {uploadedFiles[0].faceCount}개
                                                                </p>
                                                            )}
                                                            {detectingIds.has(uploadedFiles[0].id) && (
                                                                <p className="text-blue-600 dark:text-blue-400 mt-1 font-medium">
                                                                    디텍션 중...
                                                                </p>
                                                            )}
                                                        </div>
                                                        {!uploadingIds.has(uploadedFiles[0].id) && (
                                                            <button
                                                                onClick={() => handleDownload(uploadedFiles[0])}
                                                                className="px-4 py-2 bg-green-500 text-white rounded-lg text-sm font-medium hover:bg-green-600 transition-colors"
                                                            >
                                                                다운로드
                                                            </button>
                                                        )}
                                                    </div>
                                                </div>
                                                {/* 원본 이미지 */}
                                                <div className="flex-1 flex flex-col p-4 min-h-[500px]">
                                                    <div className="mb-2">
                                                        <span className="bg-blue-500 text-white text-sm px-3 py-1 rounded">원본</span>
                                                    </div>
                                                    <div className="flex-1 flex items-center justify-center">
                                                        <img
                                                            src={uploadedFiles[0].preview}
                                                            alt={uploadedFiles[0].file.name}
                                                            className="max-w-full max-h-full object-contain rounded-lg"
                                                            title="원본 이미지"
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {/* 오른쪽 반: 디텍션, 세그먼트 또는 포즈 이미지 (최근 실행 순서대로) */}
                                        {(() => {
                                            const file = uploadedFiles[0];
                                            const latestResult = getLatestResult(file);

                                            if (latestResult?.type === 'classify') {
                                                return (
                                                    <div className="flex-1 rounded-lg border-2 border-gray-300 dark:border-gray-600 p-4 bg-white dark:bg-gray-800">
                                                        <div className="flex flex-col h-full min-h-[500px]">
                                                            <div className="mb-2 flex items-center justify-between">
                                                                <span className="bg-pink-500 text-white text-sm px-3 py-1 rounded">분류</span>
                                                                {file.totalCount !== undefined && file.totalCount > 0 && (
                                                                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                                                                        {file.dogCount !== undefined && file.dogCount > 0 && (
                                                                            <span className="font-semibold text-blue-600 dark:text-blue-400">개: {file.dogCount}마리</span>
                                                                        )}
                                                                        {file.catCount !== undefined && file.catCount > 0 && (
                                                                            <span className="font-semibold text-orange-600 dark:text-orange-400">고양이: {file.catCount}마리</span>
                                                                        )}
                                                                        {file.confidence !== undefined && file.confidence > 0 && (
                                                                            <span className="text-gray-600 dark:text-gray-400">
                                                                                (평균: {(file.confidence * 100).toFixed(1)}%)
                                                                            </span>
                                                                        )}
                                                                    </div>
                                                                )}
                                                            </div>
                                                            <div className="flex-1 flex items-center justify-center">
                                                                <img
                                                                    src={`${process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000'}/api/images/${encodeURIComponent(file.classifiedImage!)}`}
                                                                    alt={`${file.file.name} (분류 결과)`}
                                                                    className="max-w-full max-h-full object-contain rounded-lg"
                                                                    title="분류 결과 이미지"
                                                                />
                                                            </div>
                                                        </div>
                                                    </div>
                                                );
                                            } else if (latestResult?.type === 'pose') {
                                                return (
                                                    <div className="flex-1 rounded-lg border-2 border-gray-300 dark:border-gray-600 p-4 bg-white dark:bg-gray-800">
                                                        <div className="flex flex-col h-full min-h-[500px]">
                                                            <div className="mb-2 flex items-center justify-between">
                                                                <span className="bg-orange-500 text-white text-sm px-3 py-1 rounded">포즈</span>
                                                                {file.confidence !== undefined && file.confidence > 0 && (
                                                                    <span className="text-sm text-gray-600 dark:text-gray-400">
                                                                        Confidence: {(file.confidence * 100).toFixed(1)}%
                                                                    </span>
                                                                )}
                                                            </div>
                                                            <div className="flex-1 flex items-center justify-center">
                                                                <img
                                                                    src={`${process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000'}/api/images/${encodeURIComponent(file.poseImage!)}`}
                                                                    alt={`${file.file.name} (포즈 결과)`}
                                                                    className="max-w-full max-h-full object-contain rounded-lg"
                                                                    title="포즈 결과 이미지"
                                                                />
                                                            </div>
                                                        </div>
                                                    </div>
                                                );
                                            } else if (latestResult?.type === 'segment') {
                                                return (
                                                    <div className="flex-1 rounded-lg border-2 border-gray-300 dark:border-gray-600 p-4 bg-white dark:bg-gray-800">
                                                        <div className="flex flex-col h-full min-h-[500px]">
                                                            <div className="mb-2 flex items-center justify-between">
                                                                <span className="bg-purple-500 text-white text-sm px-3 py-1 rounded">세그먼트</span>
                                                                {file.confidence !== undefined && file.confidence > 0 && (
                                                                    <span className="text-sm text-gray-600 dark:text-gray-400">
                                                                        Confidence: {(file.confidence * 100).toFixed(1)}%
                                                                    </span>
                                                                )}
                                                            </div>
                                                            <div className="flex-1 flex items-center justify-center">
                                                                <img
                                                                    src={`${process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000'}/api/images/${encodeURIComponent(file.segmentedImage!)}`}
                                                                    alt={`${file.file.name} (세그먼트 결과)`}
                                                                    className="max-w-full max-h-full object-contain rounded-lg"
                                                                    title="세그먼트 결과 이미지"
                                                                />
                                                            </div>
                                                        </div>
                                                    </div>
                                                );
                                            } else if (latestResult?.type === 'detect') {
                                                return (
                                                    <div className="flex-1 rounded-lg border-2 border-gray-300 dark:border-gray-600 p-4 bg-white dark:bg-gray-800">
                                                        <div className="flex flex-col h-full min-h-[500px]">
                                                            <div className="mb-2">
                                                                <span className="bg-green-500 text-white text-sm px-3 py-1 rounded">디텍션</span>
                                                            </div>
                                                            <div className="flex-1 flex items-center justify-center">
                                                                <img
                                                                    src={`${process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000'}/api/images/${encodeURIComponent(file.detectedImage!)}`}
                                                                    alt={`${file.file.name} (디텍션 결과)`}
                                                                    className="max-w-full max-h-full object-contain rounded-lg"
                                                                    title="디텍션 결과 이미지"
                                                                />
                                                            </div>
                                                        </div>
                                                    </div>
                                                );
                                            } else {
                                                return (
                                                    <div className="flex-1 rounded-lg border-2 border-gray-300 dark:border-gray-600 p-4 bg-white dark:bg-gray-800 flex items-center justify-center">
                                                        <div className="text-center">
                                                            {detectingIds.has(uploadedFiles[0].id) ? (
                                                                <>
                                                                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                                                                    <p className="text-gray-400">디텍션 중...</p>
                                                                </>
                                                            ) : segmentingIds.has(uploadedFiles[0].id) ? (
                                                                <>
                                                                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
                                                                    <p className="text-gray-400">세그먼트 중...</p>
                                                                </>
                                                            ) : posingIds.has(uploadedFiles[0].id) ? (
                                                                <>
                                                                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto mb-4"></div>
                                                                    <p className="text-gray-400">포즈 추정 중...</p>
                                                                </>
                                                            ) : classifyingIds.has(uploadedFiles[0].id) ? (
                                                                <>
                                                                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-500 mx-auto mb-4"></div>
                                                                    <p className="text-gray-400">분류 중...</p>
                                                                </>
                                                            ) : (
                                                                <>
                                                                    <p className="text-gray-400 mb-2">디텍트, 세그먼트, 포즈 또는 분류 버튼을 눌러</p>
                                                                    <p className="text-gray-400">처리를 시작하세요</p>
                                                                </>
                                                            )}
                                                        </div>
                                                    </div>
                                                );
                                            }
                                        })()}
                                    </div>

                                    {/* 액션 버튼 */}
                                    <div className="flex items-center justify-between gap-4 mt-6">
                                        <div className="flex gap-2">
                                            <button
                                                onClick={handleReset}
                                                disabled={uploadedFiles.length === 0}
                                                className="px-4 py-2 bg-yellow-500 text-white rounded-lg font-medium hover:bg-yellow-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                                title="상태를 초기화하고 다시 테스트할 수 있습니다"
                                            >
                                                초기화
                                            </button>
                                            <button
                                                onClick={handleRemoveAll}
                                                disabled={uploadedFiles.length === 0}
                                                className="px-4 py-2 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                            >
                                                모든 파일 삭제 {uploadedFiles.length > 0 && `(${uploadedFiles.length})`}
                                            </button>
                                        </div>
                                        <div className="flex gap-2">
                                            <button
                                                onClick={handleDetect}
                                                disabled={uploadedFiles.filter(f => isImageFile(f.file) && !f.detectedImage).length === 0 || detectingIds.size > 0}
                                                className="px-4 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                            >
                                                {detectingIds.size > 0
                                                    ? `디텍션 중... (${detectingIds.size})`
                                                    : `디텍트 (${uploadedFiles.filter(f => isImageFile(f.file) && !f.detectedImage).length})`
                                                }
                                            </button>
                                            <button
                                                onClick={handleSegment}
                                                disabled={uploadedFiles.filter(f => isImageFile(f.file) && !f.segmentedImage).length === 0 || segmentingIds.size > 0}
                                                className="px-4 py-2 bg-purple-500 text-white rounded-lg font-medium hover:bg-purple-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                            >
                                                {segmentingIds.size > 0
                                                    ? `세그먼트 중... (${segmentingIds.size})`
                                                    : `세그먼트 (${uploadedFiles.filter(f => isImageFile(f.file) && !f.segmentedImage).length})`
                                                }
                                            </button>
                                            <button
                                                onClick={handlePose}
                                                disabled={uploadedFiles.filter(f => isImageFile(f.file) && !f.poseImage).length === 0 || posingIds.size > 0}
                                                className="px-4 py-2 bg-orange-500 text-white rounded-lg font-medium hover:bg-orange-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                            >
                                                {posingIds.size > 0
                                                    ? `포즈 중... (${posingIds.size})`
                                                    : `포즈 (${uploadedFiles.filter(f => isImageFile(f.file) && !f.poseImage).length})`
                                                }
                                            </button>
                                            <button
                                                onClick={handleClassify}
                                                disabled={uploadedFiles.filter(f => isImageFile(f.file) && !f.classifiedImage).length === 0 || classifyingIds.size > 0}
                                                className="px-4 py-2 bg-pink-500 text-white rounded-lg font-medium hover:bg-pink-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                            >
                                                {classifyingIds.size > 0
                                                    ? `분류 중... (${classifyingIds.size})`
                                                    : `분류 (${uploadedFiles.filter(f => isImageFile(f.file) && !f.classifiedImage).length})`}
                                            </button>
                                            <button
                                                onClick={handleClose}
                                                className="px-4 py-2 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
                                            >
                                                ← 이전 페이지로
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* 포트폴리오에 추가된 이미지들 */}
                            {portfolioFiles.length > 0 && (
                                <div className="mt-8">
                                    <div className="flex items-center justify-between mb-4">
                                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                                            포트폴리오 ({portfolioFiles.length}개)
                                        </h3>
                                        <button
                                            onClick={handleRemoveAllPortfolio}
                                            className="px-4 py-2 bg-red-500 text-white rounded-lg text-sm font-medium hover:bg-red-600 transition-colors"
                                        >
                                            포트폴리오 전체 삭제
                                        </button>
                                    </div>
                                    <div className="space-y-6">
                                        {portfolioFiles.map((portfolioFile, index) => (
                                            <div key={`portfolio-${portfolioFile.id}-${index}`} className="flex gap-4">
                                                {/* 왼쪽 반: 원본 이미지 + 파일 정보 */}
                                                {portfolioFile.preview && (
                                                    <div className="flex-1 flex flex-col rounded-lg border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800">
                                                        {/* 파일 정보 */}
                                                        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                                                            <div className="flex items-center justify-between mb-3">
                                                                <div className="flex items-center gap-2">
                                                                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                                                    </svg>
                                                                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                                                        {portfolioFile.file.name}
                                                                    </p>
                                                                </div>
                                                            </div>
                                                            <div className="text-xs text-gray-500 dark:text-gray-400">
                                                                <p>{formatFileSize(portfolioFile.file.size)}</p>
                                                                <p className="mt-1">{portfolioFile.uploadTime.toLocaleString('ko-KR')}</p>
                                                                {portfolioFile.faceCount !== undefined && portfolioFile.faceCount > 0 && (
                                                                    <p className="text-green-600 dark:text-green-400 mt-1 font-medium">
                                                                        탐지된 얼굴: {portfolioFile.faceCount}개
                                                                    </p>
                                                                )}
                                                            </div>
                                                        </div>
                                                        {/* 원본 이미지 */}
                                                        <div className="flex-1 flex flex-col p-4 min-h-[500px]">
                                                            <div className="mb-2">
                                                                <span className="bg-blue-500 text-white text-sm px-3 py-1 rounded">원본</span>
                                                            </div>
                                                            <div className="flex-1 flex items-center justify-center">
                                                                <img
                                                                    src={portfolioFile.preview}
                                                                    alt={portfolioFile.file.name}
                                                                    className="max-w-full max-h-full object-contain rounded-lg"
                                                                    title="원본 이미지"
                                                                />
                                                            </div>
                                                        </div>
                                                    </div>
                                                )}

                                                {/* 오른쪽 반: 디텍션된 이미지 */}
                                                {portfolioFile.detectedImage && (
                                                    <div className="flex-1 rounded-lg border-2 border-gray-300 dark:border-gray-600 p-4 bg-white dark:bg-gray-800">
                                                        <div className="flex flex-col h-full min-h-[500px]">
                                                            <div className="mb-2">
                                                                <span className="bg-green-500 text-white text-sm px-3 py-1 rounded">디텍션</span>
                                                            </div>
                                                            <div className="flex-1 flex items-center justify-center">
                                                                <img
                                                                    src={`${process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000'}/api/images/${encodeURIComponent(portfolioFile.detectedImage)}`}
                                                                    alt={`${portfolioFile.file.name} (디텍션 결과)`}
                                                                    className="max-w-full max-h-full object-contain rounded-lg"
                                                                    title="디텍션 결과 이미지"
                                                                />
                                                            </div>
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
