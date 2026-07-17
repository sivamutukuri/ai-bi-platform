export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface Dataset {
  id: string;
  name: string;
  description: string | null;
  source_type: string;
  status: string;
  row_count: number | null;
  column_count: number | null;
  schema_json: Record<string, string> | null;
  created_at: string;
}

export interface ColumnProfile {
  name: string;
  dtype: string;
  missing: number;
  missing_pct: number;
  unique: number;
  outliers: number;
  mean: number | null;
  std: number | null;
  min: number | null;
  max: number | null;
  top: string | number | null;
}

export interface QualityReport {
  quality_score: number;
  total_rows: number;
  total_columns: number;
  duplicate_rows: number;
  total_missing: number;
  columns: ColumnProfile[];
  issues: string[];
}

export interface Insight {
  title: string;
  detail: string;
  severity: "info" | "warning" | "critical";
}

export interface Kpi {
  label: string;
  value: number;
  suffix?: string;
  icon: string;
}

export interface CorrelationPair {
  x: string;
  y: string;
  corr: number;
}

export interface Correlation {
  columns: string[];
  matrix: (number | null)[][];
  top_pairs: CorrelationPair[];
}

export interface Trend {
  available: boolean;
  date_column?: string;
  metric?: string;
  dates?: string[];
  values?: number[];
  slope?: number;
  direction?: string;
}

export interface Histogram {
  bins: number[];
  counts: number[];
}

export interface CategoryDistribution {
  labels: string[];
  counts: number[];
}

export interface Eda {
  numeric_columns: string[];
  categorical_columns: string[];
  datetime_columns: string[];
  descriptive_stats: Record<string, Record<string, number | null>>;
  correlation: Correlation;
  trend: Trend;
  histograms: Record<string, Histogram>;
  category_distributions: Record<string, CategoryDistribution>;
}

export interface FeatureImportanceItem {
  feature: string;
  importance: number;
}

export interface FeatureImportance {
  available: boolean;
  reason?: string;
  target?: string;
  task?: string;
  backend?: string;
  importances?: FeatureImportanceItem[];
}

export interface AnalysisResult {
  cleaning_actions: string[];
  quality: QualityReport;
  eda: Eda;
  feature_importance: FeatureImportance;
  insights: Insight[];
  kpis: Kpi[];
  executive_summary: { summary: string; used_llm: boolean };
  schema: Record<string, string>;
  row_count: number;
  column_count: number;
}

export interface NLQueryResponse {
  answer: string;
  used_llm: boolean;
  generated_code: string | null;
  result_preview: Record<string, unknown>[] | null;
}
