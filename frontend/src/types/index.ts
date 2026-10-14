export interface Dataset {
  id: number
  name: string
  source_path: string
  item_count: number
  hash: string
  createdAt: string
}

export interface Run {
  id: number
  dataset_id: number
  model: string
  system_prompt: string
  judge_model: string
  avg_score: number | null
  total: number
  created_at: string
}

export interface Result {
  id: number
  run_id: number
  idx: number
  question: string
  expected: string | null
  response: string | null
  score: number | null
  flaw: string | null
  reason: string | null
  latency_ms: number | null
}

export interface CompareData {
  run_a: Run
  run_b: Run
  comparison: Array<{
    idx: number
    question: string
    expected: string | null
    run_a_response: string | null
    run_b_response: string | null
    run_a_score: number | null
    run_b_score: number | null
    diff: number | null
  }>
}

export interface User {
  id: string
  email: string
  name: string
  avatar_url?: string
}

export interface AuthState {
  user: User | null
  isLoading: boolean
}