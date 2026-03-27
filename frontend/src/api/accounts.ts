import client from './client'
import type { Account } from './types'

export async function getAccounts(): Promise<Account[]> {
  const { data } = await client.get<Account[]>('/accounts')
  return data
}

export async function createAccount(payload: Omit<Account, 'id'>): Promise<Account> {
  const { data } = await client.post<Account>('/accounts', payload)
  return data
}
