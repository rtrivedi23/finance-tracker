export interface Account {
  id: number
  bank_name: string
  account_type: string
  account_number?: string
  account_holder?: string
  currency: string
}

export interface Category {
  id: number
  name: string
  icon?: string
  color?: string
}

export interface Transaction {
  id: number
  transaction_date: string
  description: string
  clean_description?: string
  amount: number
  type: 'debit' | 'credit'
  category_id?: number
  category_name?: string
  category_icon?: string
  category_color?: string
  merchant_name?: string
  is_manually_categorized: boolean
  reference_number?: string
  balance_after?: number
}

export interface TransactionStats {
  total_debit: number
  total_credit: number
  net: number
  count: number
}

export interface TransactionFilters {
  account_id?: number
  category_id?: number
  type?: 'debit' | 'credit'
  search?: string
  date_from?: string
  date_to?: string
  page?: number
  page_size?: number
}

export interface PaginatedTransactions {
  items: Transaction[]
  total: number
  page: number
  page_size: number
}

export interface CategoryAmount {
  category_id?: number
  category_name: string
  amount: number
  percentage: number
  color?: string
  icon?: string
}

export interface MonthlySummary {
  year: number
  month: number
  total_debit: number
  total_credit: number
  net: number
  transaction_count: number
  categories: CategoryAmount[]
  investments_total?: number
  expenses_total?: number
}

export interface YearlyTrendMonth {
  month: number
  month_name: string
  total_debit: number
  total_credit: number
  net: number
  transaction_count: number
}

export interface YearlyTrend {
  year: number
  months: YearlyTrendMonth[]
  total_debit: number
  total_credit: number
  net: number
}

export interface UploadResponse {
  statement_id: number
  account_id: number
  bank_name: string
  filename: string
  transaction_count: number
  parse_status: string
  parse_warnings: string[]
  period_from?: string
  period_to?: string
}

export interface Budget {
  id: number
  category_id: number
  category_name?: string
  category_icon?: string
  amount: number
  period_type: string
}

export interface BudgetVsActual extends Budget {
  actual: number
  percentage: number
}

export interface CategoryRule {
  id: number
  category_id: number
  rule_type: string
  pattern: string
  priority: number
}
