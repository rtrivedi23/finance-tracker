import client from './client'
import type { Budget, BudgetVsActual } from './types'

export async function getBudgets(): Promise<Budget[]> {
  const { data } = await client.get<Budget[]>('/budgets')
  return data
}

export async function createBudget(
  payload: Omit<Budget, 'id' | 'category_name' | 'category_icon'>
): Promise<Budget> {
  const { data } = await client.post<Budget>('/budgets', payload)
  return data
}

export async function deleteBudget(id: number): Promise<void> {
  await client.delete(`/budgets/${id}`)
}

export async function getBudgetsVsActual(): Promise<BudgetVsActual[]> {
  const { data } = await client.get<BudgetVsActual[]>('/budgets/vs-actual')
  return data
}
