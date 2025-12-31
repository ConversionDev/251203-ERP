'use client';

import FileUpload from '@/app/components/FileUpload';

export default function UploadPage() {
  return (
    <div className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900">
      {/* 헤더 */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">파일 업로드</h1>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                이미지 파일을 업로드하고 AI 분석 기능을 사용하세요
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 메인 컨텐츠 */}
      <div className="px-6 py-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <FileUpload
            onUploadComplete={(file) => {
              console.log('파일 업로드 완료:', file.name);
            }}
            onUploadError={(error) => {
              console.error('파일 업로드 오류:', error);
            }}
          />
        </div>
      </div>
    </div>
  );
}

