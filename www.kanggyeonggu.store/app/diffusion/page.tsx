'use client';

import { useState } from 'react';

interface GenerateRequest {
  prompt: string;
  negative_prompt?: string;
  width?: number;
  height?: number;
  steps?: number;
  guidance_scale?: number;
  seed?: number;
}

interface GenerateResponse {
  id: string;
  image_url: string;
  meta_url: string;
  meta: {
    prompt: string;
    width: number;
    height: number;
    steps: number;
    seed?: number;
    device: string;
  };
}

export default function DiffusionPage() {
  const [prompt, setPrompt] = useState('a cute cat, kawaii style');
  const [negativePrompt, setNegativePrompt] = useState('');
  const [width, setWidth] = useState(512);
  const [height, setHeight] = useState(512);
  const [steps, setSteps] = useState(4);
  const [seed, setSeed] = useState<number | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GenerateResponse | null>(null);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const requestBody: GenerateRequest = {
        prompt,
        width,
        height,
        steps,
      };

      if (negativePrompt) {
        requestBody.negative_prompt = negativePrompt;
      }

      if (seed !== undefined && seed !== null) {
        requestBody.seed = seed;
      }

      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || '이미지 생성에 실패했습니다.');
      }

      const data: GenerateResponse = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || '이미지 생성 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleRandomSeed = () => {
    setSeed(Math.floor(Math.random() * 1000000));
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto p-6 max-w-6xl">
        <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">AI 이미지 생성</h1>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 입력 폼 */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                프롬프트 (Prompt) *
              </label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                className="w-full p-3 border rounded-lg resize-none bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                rows={3}
                placeholder="생성하고 싶은 이미지를 설명하세요"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                네거티브 프롬프트 (Negative Prompt)
              </label>
              <textarea
                value={negativePrompt}
                onChange={(e) => setNegativePrompt(e.target.value)}
                className="w-full p-3 border rounded-lg resize-none bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                rows={2}
                placeholder="피하고 싶은 요소를 입력하세요 (선택사항)"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">너비 (Width)</label>
                <select
                  value={width}
                  onChange={(e) => setWidth(Number(e.target.value))}
                  className="w-full p-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                >
                  <option value={256}>256px (최소 용량)</option>
                  <option value={512}>512px</option>
                  <option value={768}>768px</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">높이 (Height)</label>
                <select
                  value={height}
                  onChange={(e) => setHeight(Number(e.target.value))}
                  className="w-full p-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                >
                  <option value={256}>256px (최소 용량)</option>
                  <option value={512}>512px</option>
                  <option value={768}>768px</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">스텝 (Steps)</label>
                <input
                  type="number"
                  value={steps}
                  onChange={(e) => setSteps(Number(e.target.value))}
                  min={1}
                  max={8}
                  className="w-full p-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                  시드 (Seed)
                  <button
                    onClick={handleRandomSeed}
                    className="ml-2 text-xs text-blue-500 hover:underline"
                  >
                    랜덤
                  </button>
                </label>
                <input
                  type="number"
                  value={seed ?? ''}
                  onChange={(e) => setSeed(e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full p-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  placeholder="비워두면 랜덤"
                />
              </div>
            </div>

            <button
              onClick={handleGenerate}
              disabled={loading || !prompt.trim()}
              style={{
                width: '100%',
                padding: '12px',
                backgroundColor: loading || !prompt.trim() ? '#9ca3af' : '#3b82f6',
                color: 'white',
                borderRadius: '8px',
                fontWeight: '500',
                fontSize: '16px',
                border: 'none',
                cursor: loading || !prompt.trim() ? 'not-allowed' : 'pointer',
                marginTop: '16px'
              }}
            >
              {loading ? '이미지 생성 중...' : '이미지 생성'}
            </button>

            {error && (
              <div className="p-3 bg-red-100 text-red-700 rounded-lg">
                {error}
              </div>
            )}
          </div>

          {/* 결과 표시 */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">생성된 이미지</h2>

            {loading && (
              <div className="flex items-center justify-center h-64 bg-gray-100 dark:bg-gray-800 rounded-lg">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                  <p className="text-gray-600 dark:text-gray-400">이미지를 생성하고 있습니다...</p>
                  <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">잠시만 기다려주세요 (30초~2분 소요)</p>
                </div>
              </div>
            )}

            {result && !loading && (
              <div className="space-y-4">
                <div className="border rounded-lg overflow-hidden bg-white dark:bg-gray-800">
                  <img
                    src={`http://localhost:8000${result.image_url}`}
                    alt={result.meta.prompt}
                    className="w-full h-auto"
                  />
                </div>

                <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <h3 className="font-semibold mb-2 text-gray-900 dark:text-white">생성 정보</h3>
                  <div className="text-sm space-y-1 text-gray-700 dark:text-gray-300">
                    <p><strong>ID:</strong> {result.id}</p>
                    <p><strong>프롬프트:</strong> {result.meta.prompt}</p>
                    <p><strong>크기:</strong> {result.meta.width} × {result.meta.height}px</p>
                    <p><strong>스텝:</strong> {result.meta.steps}</p>
                    {result.meta.seed !== undefined && (
                      <p><strong>시드:</strong> {result.meta.seed}</p>
                    )}
                    <p><strong>디바이스:</strong> {result.meta.device}</p>
                  </div>
                </div>
              </div>
            )}

            {!result && !loading && (
              <div className="flex items-center justify-center h-64 bg-gray-100 dark:bg-gray-800 rounded-lg">
                <p className="text-gray-500 dark:text-gray-400">생성된 이미지가 여기에 표시됩니다</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

