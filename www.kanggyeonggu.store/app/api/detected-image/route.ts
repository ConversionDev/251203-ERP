import { NextRequest, NextResponse } from 'next/server';
import { readFile } from 'fs/promises';
import { join } from 'path';
import { existsSync } from 'fs';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const filename = searchParams.get('filename');

    if (!filename) {
      return NextResponse.json(
        { error: '파일명이 제공되지 않았습니다.' },
        { status: 400 }
      );
    }

    // cv.kanggyeonggu.store/app/data/yolo 디렉토리에서 파일 찾기
    const currentDir = process.cwd();
    const projectRoot = join(currentDir, '..');
    const yoloDataDir = join(projectRoot, 'cv.kanggyeonggu.store', 'app', 'data', 'yolo');
    const filePath = join(yoloDataDir, filename);

    // 파일 존재 확인
    if (!existsSync(filePath)) {
      return NextResponse.json(
        { error: '파일을 찾을 수 없습니다.' },
        { status: 404 }
      );
    }

    // 파일 읽기
    const fileBuffer = await readFile(filePath);
    
    // 이미지 타입 결정
    const ext = filename.split('.').pop()?.toLowerCase();
    let contentType = 'image/jpeg';
    if (ext === 'png') contentType = 'image/png';
    else if (ext === 'gif') contentType = 'image/gif';
    else if (ext === 'webp') contentType = 'image/webp';

    // 이미지 반환
    return new NextResponse(fileBuffer, {
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=3600',
      },
    });
  } catch (error) {
    console.error('이미지 서빙 오류:', error);
    return NextResponse.json(
      { error: '이미지를 불러오는 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}

