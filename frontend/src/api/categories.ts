import client from './client'
import type { Category, CategoryRule } from './types'

export async function getCategories(): Promise<Category[]> {
  const { data } = await client.get<Category[]>('/categories')
  return data
}

export async function createCategory(payload: Omit<Category, 'id'>): Promise<Category> {
  const { data } = await client.post<Category>('/categories', payload)
  return data
}

export async function getCategoryRules(id: number): Promise<CategoryRule[]> {
  const { data } = await client.get<CategoryRule[]>(`/categories/${id}/rules`)
  return data
}

export async function createRule(
  categoryId: number,
  payload: Omit<CategoryRule, 'id' | 'category_id'>
): Promise<CategoryRule> {
  const { data } = await client.post<CategoryRule>(`/categories/${categoryId}/rules`, payload)
  return data
}

export async function deleteRule(ruleId: number): Promise<void> {
  await client.delete(`/categories/rules/${ruleId}`)
}
