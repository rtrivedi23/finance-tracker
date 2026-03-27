import client from './client'
import type { Transaction, TransactionFilters, TransactionStats, PaginatedTransactions } from './types'

export async function getTransactions(filters: TransactionFilters = {}): Promise<PaginatedTransactions> {
  const params: Record<string, string | number> = {}
  if (filters.account_id !== undefined) params.account_id = filters.account_id
  if (filters.category_id !== undefined) params.category_id = filters.category_id
  if (filters.type) params.type = filters.type
  if (filters.search) params.search = filters.search
  if (filters.date_from) params.date_from = filters.date_from
  if (filters.date_to) params.date_to = filters.date_to
  params.page = filters.page ?? 1
  params.page_size = filters.page_size ?? 50

  const { data } = await client.get<PaginatedTransactions>('/transactions', { params })
  return data
}

export async function updateTransactionCategory(
  id: number,
  categoryId: number
): Promise<Transaction> {
  const { data } = await client.patch<Transaction>(`/transactions/${id}/category`, {
    category_id: categoryId,
  })
  return data
}

export async function getTransactionStats(filters: Omit<TransactionFilters, 'page' | 'page_size'> = {}): Promise<TransactionStats> {
  const params: Record<string, string | number> = {}
  if (filters.account_id !== undefined) params.account_id = filters.account_id
  if (filters.date_from) params.date_from = filters.date_from
  if (filters.date_to) params.date_to = filters.date_to
  if (filters.type) params.type = filters.type
  if (filters.search) params.search = filters.search

  const { data } = await client.get<TransactionStats>('/transactions/stats', { params })
  return data
}
