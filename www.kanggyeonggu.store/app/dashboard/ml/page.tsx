'use client';

import { useState, useEffect } from 'react';
import {
  getTopPassengersSimple,
  getSurvivalRate,
  getAgeStatistics,
  preprocessData,
  getDatasetSummary,
  runModeling,
  runLearning,
  runEvaluate,
  runSubmit,
  type TitanicPassengerSimple,
  type SurvivalRate,
  type AgeStatistics,
  type PreprocessResult,
  type DatasetSummary,
} from '@/service/mlservice';

export default function MLPage() {
  const [activeTab, setActiveTab] = useState<'data' | 'stats' | 'preprocess' | 'modeling' | 'learning' | 'evaluate' | 'submit' | 'summary'>('data');
  const [dataset, setDataset] = useState<'train' | 'test'>('train');

  // 데이터 상태
  const [passengers, setPassengers] = useState<TitanicPassengerSimple[]>([]);
  const [survivalRate, setSurvivalRate] = useState<SurvivalRate | null>(null);
  const [ageStats, setAgeStats] = useState<AgeStatistics | null>(null);
  const [preprocessResult, setPreprocessResult] = useState<PreprocessResult | null>(null);
  const [modelingResult, setModelingResult] = useState<any>(null);
  const [learningResult, setLearningResult] = useState<any>(null);
  const [evaluateResult, setEvaluateResult] = useState<any>(null);
  const [submitResult, setSubmitResult] = useState<any>(null);
  const [datasetSummary, setDatasetSummary] = useState<DatasetSummary | null>(null);

  // 로딩 상태
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 데이터 조회
  useEffect(() => {
    loadData();
  }, [activeTab, dataset]);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      switch (activeTab) {
        case 'data':
          const data = await getTopPassengersSimple(10, dataset);
          setPassengers(data);
          break;
        case 'stats':
          const [survival, age] = await Promise.all([
            getSurvivalRate(dataset),
            getAgeStatistics(dataset),
          ]);
          setSurvivalRate(survival);
          setAgeStats(age);
          break;
        case 'preprocess':
          const preprocess = await preprocessData();
          setPreprocessResult(preprocess);
          break;
        case 'modeling':
          const modeling = await runModeling();
          setModelingResult(modeling);
          break;
        case 'learning':
          const learning = await runLearning();
          setLearningResult(learning);
          break;
        case 'evaluate':
          const evaluate = await runEvaluate();
          setEvaluateResult(evaluate);
          break;
        case 'submit':
          const submit = await runSubmit();
          setSubmitResult(submit);
          break;
        case 'summary':
          const summary = await getDatasetSummary(dataset);
          setDatasetSummary(summary);
          break;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '데이터 로드 실패');
      console.error('데이터 로드 오류:', err);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'data', name: '승객 데이터', icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z' },
    { id: 'stats', name: '통계 분석', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
    { id: 'preprocess', name: '전처리', icon: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' },
    { id: 'modeling', name: '모델링', icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z' },
    { id: 'learning', name: '학습', icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253' },
    { id: 'evaluate', name: '평가', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
    { id: 'submit', name: '제출', icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' },
    { id: 'summary', name: '데이터셋 요약', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
  ];

  return (
    <div className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900">
      {/* 헤더 */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">ML 분석 - Titanic</h1>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                타이타닉 데이터셋 분석 및 머신러닝
              </p>
            </div>
            <div className="flex items-center gap-3">
              <select
                value={dataset}
                onChange={(e) => setDataset(e.target.value as 'train' | 'test')}
                className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="train">학습 데이터 (891명)</option>
                <option value="test">테스트 데이터 (418명)</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* 탭 메뉴 */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="px-6">
          <div className="flex space-x-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:border-gray-300'
                  }`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={tab.icon} />
                </svg>
                <span>{tab.name}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 컨텐츠 */}
      <div className="px-6 py-6">
        {loading && (
          <div className="flex items-center justify-center py-12">
            <svg className="animate-spin h-8 w-8 text-blue-500" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span className="ml-3 text-gray-600 dark:text-gray-400">데이터 로딩 중...</span>
          </div>
        )}

        {error && (
          <div className="mb-6 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3">
            <div className="flex items-center gap-2">
              <svg className="h-5 w-5 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-sm text-red-600 dark:text-red-400">{error}</span>
            </div>
          </div>
        )}

        {!loading && !error && (
          <>
            {/* 승객 데이터 탭 */}
            {activeTab === 'data' && (
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">상위 10명 승객 정보</h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 dark:bg-gray-700">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">ID</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">이름</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">나이</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">성별</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">등급</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">생존</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">요금</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                      {passengers.map((passenger) => (
                        <tr key={passenger.PassengerId} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{passenger.PassengerId}</td>
                          <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">{passenger.Name}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">{passenger.Age ?? 'N/A'}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">{passenger.Sex}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">{passenger.Pclass}등급</td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${passenger.Survived === '생존'
                              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                              : passenger.Survived === '사망'
                                ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                                : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                              }`}>
                              {passenger.Survived}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">${passenger.Fare?.toFixed(2) ?? 'N/A'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* 통계 분석 탭 */}
            {activeTab === 'stats' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* 생존율 통계 */}
                {survivalRate && (
                  <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">생존율 통계</h3>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600 dark:text-gray-400">전체 승객</span>
                        <span className="text-lg font-bold text-gray-900 dark:text-white">{survivalRate.total}명</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600 dark:text-gray-400">생존자</span>
                        <span className="text-lg font-bold text-green-600 dark:text-green-400">{survivalRate.survived}명</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600 dark:text-gray-400">사망자</span>
                        <span className="text-lg font-bold text-red-600 dark:text-red-400">{survivalRate.died}명</span>
                      </div>
                      <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">생존율</span>
                          <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">{survivalRate.survival_rate}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* 나이 통계 */}
                {ageStats && (
                  <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">나이 통계</h3>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600 dark:text-gray-400">평균 나이</span>
                        <span className="text-lg font-bold text-gray-900 dark:text-white">{ageStats.mean}세</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600 dark:text-gray-400">중앙값</span>
                        <span className="text-lg font-bold text-gray-900 dark:text-white">{ageStats.median}세</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600 dark:text-gray-400">최소 나이</span>
                        <span className="text-lg font-bold text-gray-900 dark:text-white">{ageStats.min}세</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600 dark:text-gray-400">최대 나이</span>
                        <span className="text-lg font-bold text-gray-900 dark:text-white">{ageStats.max}세</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600 dark:text-gray-400">표준편차</span>
                        <span className="text-lg font-bold text-gray-900 dark:text-white">{ageStats.std}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* 전처리 탭 */}
            {activeTab === 'preprocess' && preprocessResult && (
              <div className="space-y-6">
                {/* 전처리 시작 - 원본 데이터 테이블 */}
                {preprocessResult.before && preprocessResult.before.sample_data && preprocessResult.before.sample_data.length > 0 && (
                  <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
                    <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                      <h2 className="text-lg font-semibold text-gray-900 dark:text-white">😎😎 전처리 시작 - 원본 데이터 샘플 (상위 5개)</h2>
                      <div className="mt-2 flex gap-4 text-sm text-gray-600 dark:text-gray-400">
                        <span>컬럼 수: {preprocessResult.before.column_count}</span>
                        <span>결측치: {preprocessResult.before.null_count}개</span>
                      </div>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-50 dark:bg-gray-700">
                          <tr>
                            {preprocessResult.before.columns?.map((col) => (
                              <th key={col} className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                          {preprocessResult.before.sample_data.map((row, index) => (
                            <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                              {preprocessResult.before?.columns?.map((col) => (
                                <td key={col} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                                  {row[col] !== null && row[col] !== undefined ? String(row[col]) : 'N/A'}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* 전처리 완료 - Train과 Test를 하나의 표에 표시 */}
                {((preprocessResult.train && preprocessResult.train.sample_data && preprocessResult.train.sample_data.length > 0) ||
                  (preprocessResult.test && preprocessResult.test.sample_data && preprocessResult.test.sample_data.length > 0)) && (
                    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
                      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">😎😎 전처리 완료 - 데이터 샘플 (상위 5개)</h2>
                        <div className="mt-2 flex gap-4 text-sm text-gray-600 dark:text-gray-400">
                          {preprocessResult.train && (
                            <>
                              <span>Train 컬럼 수: {preprocessResult.train.column_count}</span>
                              <span>Train 결측치: {preprocessResult.train.null_count}개</span>
                            </>
                          )}
                          {preprocessResult.test && (
                            <>
                              <span>Test 컬럼 수: {preprocessResult.test.column_count}</span>
                              <span>Test 결측치: {preprocessResult.test.null_count}개</span>
                            </>
                          )}
                        </div>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead className="bg-gray-50 dark:bg-gray-700">
                            <tr>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                Dataset
                              </th>
                              {(preprocessResult.train?.columns || preprocessResult.test?.columns)?.map((col) => (
                                <th key={col} className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                  {col}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                            {preprocessResult.train?.sample_data?.map((row, index) => (
                              <tr key={`train-${index}`} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-blue-600 dark:text-blue-400">
                                  Train
                                </td>
                                {(preprocessResult.train?.columns || preprocessResult.test?.columns)?.map((col) => (
                                  <td key={col} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                                    {row[col] !== null && row[col] !== undefined ? String(row[col]) : 'N/A'}
                                  </td>
                                ))}
                              </tr>
                            ))}
                            {preprocessResult.test?.sample_data?.map((row, index) => {
                              const testColumns = preprocessResult.test?.columns || preprocessResult.train?.columns || [];
                              return (
                                <tr key={`test-${index}`} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-600 dark:text-green-400">
                                    Test
                                  </td>
                                  {testColumns.map((col) => (
                                    <td key={col} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                                      {row[col] !== null && row[col] !== undefined ? String(row[col]) : 'N/A'}
                                    </td>
                                  ))}
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                {/* 전처리 통계 정보 */}
                {preprocessResult.train && (
                  <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">전처리 정보</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {preprocessResult.train.rows !== undefined && (
                        <div>
                          <span className="text-sm text-gray-600 dark:text-gray-400">Train 행 수</span>
                          <p className="text-xl font-bold text-gray-900 dark:text-white mt-1">{preprocessResult.train.rows.toLocaleString()}</p>
                        </div>
                      )}
                      {preprocessResult.train.column_count !== undefined && (
                        <div>
                          <span className="text-sm text-gray-600 dark:text-gray-400">컬럼 수</span>
                          <p className="text-xl font-bold text-gray-900 dark:text-white mt-1">{preprocessResult.train.column_count}</p>
                        </div>
                      )}
                      {preprocessResult.train.null_count !== undefined && (
                        <div>
                          <span className="text-sm text-gray-600 dark:text-gray-400">Train 결측치</span>
                          <p className="text-xl font-bold text-gray-900 dark:text-white mt-1">{preprocessResult.train.null_count}</p>
                        </div>
                      )}
                      {preprocessResult.status && (
                        <div>
                          <span className="text-sm text-gray-600 dark:text-gray-400">상태</span>
                          <p className="text-xl font-bold text-green-600 dark:text-green-400 mt-1">{preprocessResult.status}</p>
                        </div>
                      )}
                    </div>
                    {preprocessResult.test && (
                      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                          {preprocessResult.test.rows !== undefined && (
                            <div>
                              <span className="text-sm text-gray-600 dark:text-gray-400">Test 행 수</span>
                              <p className="text-xl font-bold text-gray-900 dark:text-white mt-1">{preprocessResult.test.rows.toLocaleString()}</p>
                            </div>
                          )}
                          {preprocessResult.test.null_count !== undefined && (
                            <div>
                              <span className="text-sm text-gray-600 dark:text-gray-400">Test 결측치</span>
                              <p className="text-xl font-bold text-gray-900 dark:text-white mt-1">{preprocessResult.test.null_count}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* 모델링 탭 */}
            {activeTab === 'modeling' && modelingResult && (
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">모델링 결과</h2>
                </div>
                <div className="p-6">
                  <div className="bg-gray-900 dark:bg-black rounded-lg p-4 font-mono text-sm text-green-400 overflow-x-auto">
                    {modelingResult.result?.logs?.map((log: string, index: number) => (
                      <div key={index} className="mb-1">{log}</div>
                    ))}
                    {!modelingResult.result?.logs && (
                      <>
                        <div className="mb-2">✅ {modelingResult.message}</div>
                        <div className="mb-2">Status: {modelingResult.status}</div>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* 학습 탭 */}
            {activeTab === 'learning' && learningResult && (
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">학습 결과</h2>
                </div>
                <div className="p-6">
                  <div className="bg-gray-900 dark:bg-black rounded-lg p-4 font-mono text-sm text-green-400 overflow-x-auto">
                    {learningResult.result?.logs?.map((log: string, index: number) => (
                      <div key={index} className="mb-1">{log}</div>
                    ))}
                    {!learningResult.result?.logs && (
                      <>
                        <div className="mb-2">✅ {learningResult.message}</div>
                        <div className="mb-2">Status: {learningResult.status}</div>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* 평가 탭 */}
            {activeTab === 'evaluate' && evaluateResult && (
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">평가 결과</h2>
                </div>
                <div className="p-6">
                  <div className="bg-gray-900 dark:bg-black rounded-lg p-4 font-mono text-sm text-green-400 overflow-x-auto">
                    {evaluateResult.result?.logs?.map((log: string, index: number) => (
                      <div key={index} className="mb-1">{log}</div>
                    ))}
                    {!evaluateResult.result?.logs && (
                      <>
                        <div className="mb-2">✅ {evaluateResult.message}</div>
                        <div className="mb-2">Status: {evaluateResult.status}</div>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* 제출 탭 */}
            {activeTab === 'submit' && submitResult && (
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">제출 결과</h2>
                </div>
                <div className="p-6">
                  <div className="bg-gray-900 dark:bg-black rounded-lg p-4 font-mono text-sm text-green-400 overflow-x-auto">
                    {submitResult.result?.logs?.map((log: string, index: number) => (
                      <div key={index} className="mb-1">{log}</div>
                    ))}
                    {!submitResult.result?.logs && (
                      <>
                        <div className="mb-2">✅ {submitResult.message}</div>
                        <div className="mb-2">Status: {submitResult.status}</div>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* 데이터셋 요약 탭 */}
            {activeTab === 'summary' && datasetSummary && (
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">데이터셋 요약</h2>
                </div>
                <div className="p-6 space-y-6">
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">기본 정보</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <span className="text-sm text-gray-600 dark:text-gray-400">행 수:</span>
                        <span className="ml-2 text-sm font-medium text-gray-900 dark:text-white">{datasetSummary.shape[0]}</span>
                      </div>
                      <div>
                        <span className="text-sm text-gray-600 dark:text-gray-400">열 수:</span>
                        <span className="ml-2 text-sm font-medium text-gray-900 dark:text-white">{datasetSummary.shape[1]}</span>
                      </div>
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">컬럼 목록</h3>
                    <div className="flex flex-wrap gap-2">
                      {datasetSummary.columns.map((col) => (
                        <span key={col} className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-xs">
                          {col}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">결측치 (Null) 개수</h3>
                    <div className="space-y-2">
                      {Object.entries(datasetSummary.null_counts).map(([col, count]) => (
                        <div key={col} className="flex justify-between items-center">
                          <span className="text-sm text-gray-600 dark:text-gray-400">{col}</span>
                          <span className={`text-sm font-medium ${count > 0 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}`}>
                            {count}개
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}


