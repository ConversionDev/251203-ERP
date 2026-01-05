import { NextRequest, NextResponse } from 'next/server';

/**
 * API 루트 엔드포인트
 * /api 경로에 대한 기본 핸들러
 */
export async function GET(request: NextRequest) {
  return NextResponse.json(
    {
      message: 'API Gateway',
      version: '1.0.0',
      endpoints: {
        classify: '/api/classify',
        detect: '/api/detect',
        generate: '/api/generate',
        upload: '/api/upload',
        pose: '/api/pose',
        segment: '/api/segment',
      },
    },
    { status: 200 }
  );
}

