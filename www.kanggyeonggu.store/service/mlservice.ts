/**
 * ML Service API 연동
 * Titanic 분석 관련 API 호출 함수들
 */

// API URL 헬퍼 함수
const getApiBaseUrl = () => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'localhost:8080';
    if (baseUrl.startsWith('http://') || baseUrl.startsWith('https://')) {
        return baseUrl;
    }
    return baseUrl.includes('localhost') ? `http://${baseUrl}` : `https://${baseUrl}`;
};

const gatewayUrl = getApiBaseUrl();
const mlApiBase = `${gatewayUrl}/api/ml/titanic`;

// 타입 정의
export interface TitanicPassengerSimple {
  PassengerId: number;
  Name: string;
  Age: number | null;
  Sex: string;
  Pclass: number;
  Survived: string;
  Fare: number | null;
}

export interface TitanicPassenger {
  PassengerId: number;
  Survived: number | null;
  Pclass: number;
  Name: string;
  Sex: string;
  Age: number | null;
  SibSp: number;
  Parch: number;
  Ticket: string;
  Fare: number | null;
  Cabin: string | null;
  Embarked: string | null;
}

export interface SurvivalRate {
  total: number;
  survived: number;
  died: number;
  survival_rate: number;
}

export interface AgeStatistics {
  mean: number;
  min: number;
  max: number;
  median: number;
  std: number;
}

export interface PreprocessResult {
  logs: string[];
  status?: string;
  rows?: number;
  columns?: string[];
  column_count?: number;
  null_count?: number;
  sample_data?: any[];
  train?: {
    rows: number;
    columns: string[];
    column_count: number;
    null_count: number;
    sample_data: any[];
  };
  test?: {
    rows: number;
    columns: string[];
    column_count: number;
    null_count: number;
    sample_data: any[];
  };
  before?: {
    columns: string[];
    column_count: number;
    null_count: number;
    sample_data: any[];
  };
}

export interface DatasetSummary {
  shape: number[];
  columns: string[];
  dtypes: Record<string, string>;
  null_counts: Record<string, number>;
  describe: Record<string, Record<string, number>>;
}

/**
 * 상위 N명 승객 조회 (간단 버전)
 */
export async function getTopPassengersSimple(
  n: number = 10,
  dataset: 'train' | 'test' = 'train'
): Promise<TitanicPassengerSimple[]> {
  const response = await fetch(
    `${mlApiBase}/passengers/top10/simple?dataset=${dataset}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`승객 데이터 조회 실패: ${response.statusText}`);
  }

  return response.json();
}

/**
 * 상위 N명 승객 조회 (전체 정보)
 */
export async function getTopPassengers(
  n: number = 10,
  dataset: 'train' | 'test' = 'train'
): Promise<TitanicPassenger[]> {
  const response = await fetch(
    `${mlApiBase}/passengers/top10?dataset=${dataset}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`승객 데이터 조회 실패: ${response.statusText}`);
  }

  return response.json();
}

/**
 * 생존율 통계 조회
 */
export async function getSurvivalRate(
  dataset: 'train' | 'test' = 'train'
): Promise<SurvivalRate> {
  const response = await fetch(
    `${mlApiBase}/statistics/survival-rate?dataset=${dataset}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`생존율 통계 조회 실패: ${response.statusText}`);
  }

  return response.json();
}

/**
 * 나이 통계 조회
 */
export async function getAgeStatistics(
  dataset: 'train' | 'test' = 'train'
): Promise<AgeStatistics> {
  const response = await fetch(
    `${mlApiBase}/statistics/age?dataset=${dataset}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`나이 통계 조회 실패: ${response.statusText}`);
  }

  return response.json();
}

/**
 * 데이터 전처리 실행
 */
export async function preprocessData(): Promise<PreprocessResult> {
  const response = await fetch(
    `${mlApiBase}/dataset/preprocess?dataset=train`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`전처리 실행 실패: ${response.statusText}`);
  }

  return response.json();
}

/**
 * 데이터셋 요약 정보 조회
 */
export async function getDatasetSummary(
  dataset: 'train' | 'test' = 'train'
): Promise<DatasetSummary> {
  const response = await fetch(
    `${mlApiBase}/dataset/summary?dataset=${dataset}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`데이터셋 요약 조회 실패: ${response.statusText}`);
  }

  return response.json();
}

/**
 * 모델링 실행
 */
export async function runModeling(): Promise<{ status: string; message: string; result: any }> {
  const response = await fetch(
    `${mlApiBase}/ml/modeling`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`모델링 실행 실패: ${response.statusText}`);
  }

  return response.json();
}

/**
 * 학습 실행
 */
export async function runLearning(): Promise<{ status: string; message: string; result: any }> {
  const response = await fetch(
    `${mlApiBase}/ml/learning`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`학습 실행 실패: ${response.statusText}`);
  }

  return response.json();
}

/**
 * 평가 실행
 */
export async function runEvaluate(): Promise<{ status: string; message: string; result: any }> {
  const response = await fetch(
    `${mlApiBase}/ml/evaluate`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`평가 실행 실패: ${response.statusText}`);
  }

  return response.json();
}

/**
 * 제출 실행
 */
export async function runSubmit(): Promise<{ status: string; message: string; result: any }> {
  const response = await fetch(
    `${mlApiBase}/ml/submit`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`제출 실행 실패: ${response.statusText}`);
  }

  return response.json();
}


