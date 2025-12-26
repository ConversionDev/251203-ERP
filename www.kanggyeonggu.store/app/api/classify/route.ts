import { NextRequest, NextResponse } from 'next/server';

const FASTAPI_URL = process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { filename } = body;

    if (!filename) {
      return NextResponse.json(
        { error: '파일명이 제공되지 않았습니다.' },
        { status: 400 }
      );
    }

    // FastAPI 서버에 분류 요청 전달
    const response = await fetch(`${FASTAPI_URL}/api/classify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ filename }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = '분류에 실패했습니다.';

      try {
        const errorData = JSON.parse(errorText);
        errorMessage = errorData.detail || errorMessage;
      } catch {
        errorMessage = errorText || errorMessage;
      }

      return NextResponse.json(
        { error: errorMessage },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error: any) {
    console.error('분류 오류:', error);
    return NextResponse.json(
      { error: error.message || '분류 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}

