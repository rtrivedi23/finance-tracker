import client from './client'
import type { MonthlySummary, YearlyTrend, CategoryAmount } from './types'

export async function getMonthlySummary(
  year: number,
  month: number,
  accountId?: number
): Promise<MonthlySummary> {
  const params: Record<string, string | number> = { year, month }
  if (accountId !== undefined) params.account_id = accountId
  const { data } = await client.get<MonthlySummary>('/reports/monthly-summary', { params })
  return data
}

export async function getYearlyTrend(
  year: number,
  accountId?: number
): Promise<YearlyTrend> {
  const params: Record<string, string | number> = { year }
  if (accountId !== undefined) params.account_id = accountId
  const { data } = await client.get<YearlyTrend>('/reports/yearly-trend', { params })
  return data
}

export async function getCategoryBreakdown(
  dateFrom: string,
  dateTo: string,
  accountId?: number
): Promise<CategoryAmount[]> {
  const params: Record<string, string | number> = { date_from: dateFrom, date_to: dateTo }
  if (accountId !== undefined) params.account_id = accountId
  const { data } = await client.get<CategoryAmount[]>('/reports/category-breakdown', { params })
  return data
}

export async function getPillars(dateFrom: string, dateTo: string, accountId?: number) {
  const params: any = { date_from: dateFrom, date_to: dateTo }
  if (accountId !== undefined) params.account_id = accountId
  const { data } = await client.get('/reports/pillars', { params })
  return data
}

export async function getPillarsTrend(year: number, accountId?: number) {
  const params: any = { year }
  if (accountId !== undefined) params.account_id = accountId
  const { data } = await client.get('/reports/pillars-trend', { params })
  return data
}
