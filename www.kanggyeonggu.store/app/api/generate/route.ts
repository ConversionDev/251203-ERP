import { NextRequest, NextResponse } from 'next/server';

const DIFFUSION_API_URL = process.env.DIFFUSION_API_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();

        const response = await fetch(`${DIFFUSION_API_URL}/api/v1/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            const errorText = await response.text();
            return NextResponse.json(
                { error: `이미지 생성 실패: ${errorText}` },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error: any) {
        console.error('이미지 생성 오류:', error);
        return NextResponse.json(
            { error: `이미지 생성 중 오류가 발생했습니다: ${error.message}` },
            { status: 500 }
        );
    }
}

