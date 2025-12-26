import { NextRequest, NextResponse } from 'next/server';

/**
 * FastAPI 서버로 파일 업로드 요청을 전달하는 프록시 API
 * FastAPI 서버가 http://localhost:8000에서 실행 중이어야 합니다.
 */
export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File;

    if (!file) {
      return NextResponse.json(
        { error: '파일이 제공되지 않았습니다.' },
        { status: 400 }
      );
    }

    // FastAPI 서버 URL (환경 변수로 설정 가능)
    const fastApiUrl = process.env.FASTAPI_URL || 'http://localhost:8000';

    try {
      // FastAPI 서버에 파일 업로드 요청 전달
      const uploadFormData = new FormData();
      uploadFormData.append('file', file);

      const response = await fetch(`${fastApiUrl}/api/upload`, {
        method: 'POST',
        body: uploadFormData,
      });

      // FastAPI 서버의 응답을 그대로 전달
      const data = await response.json();

      if (!response.ok) {
        return NextResponse.json(
          {
            error: data.detail || '파일 업로드 중 오류가 발생했습니다.',
            details: data.detail,
          },
          { status: response.status }
        );
      }

      return NextResponse.json(data);
    } catch (error: any) {
      console.error('FastAPI 서버 연결 오류:', error.message || error);

      // FastAPI 서버가 실행되지 않은 경우
      if (error.code === 'ECONNREFUSED' || error.message?.includes('fetch failed')) {
        return NextResponse.json(
          {
            error: 'FastAPI 서버에 연결할 수 없습니다.',
            details:
              'FastAPI 서버가 실행 중인지 확인하세요. (python app/yolo/yolo_main.py)',
          },
          { status: 503 }
        );
      }

      return NextResponse.json(
        { error: '파일 업로드 중 오류가 발생했습니다.', details: error.message },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error('업로드 API 오류:', error);
    return NextResponse.json(
      { error: '파일 업로드 요청 처리 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}
