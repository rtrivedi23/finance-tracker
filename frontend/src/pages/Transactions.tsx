import { useState, useCallback, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, ChevronLeft, ChevronRight } from 'lucide-react'
import { format } from 'date-fns'
import { getTransactions, updateTransactionCategory, getTransactionStats } from '../api/transactions'
import { getCategories } from '../api/categories'
import { getAccounts } from '../api/accounts'
import { formatINR } from '../utils/currency'
import type { TransactionFilters, Transaction } from '../api/types'

function CategoryBadge({
  tx,
  categories,
  onSelect,
}: {
  tx: Transaction
  categories: { id: number; name: string; icon?: string; color?: string }[]
  onSelect: (catId: number) => void
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="text-[11px] px-2 py-1 rounded-full border transition-all hover:opacity-80"
        style={
          tx.category_color
            ? {
                backgroundColor: `${tx.category_color}20`,
                color: tx.category_color,
                borderColor: `${tx.category_color}30`,
              }
            : {
                backgroundColor: 'rgba(255,255,255,0.04)',
                color: '#64748B',
                borderColor: 'rgba(255,255,255,0.08)',
                borderStyle: 'dashed',
              }
        }
      >
        {tx.category_icon ? `${tx.category_icon} ` : ''}
        {tx.category_name ?? 'Uncategorized'}
      </button>
      {open && (
        <div
          className="absolute z-20 mt-1 left-0 rounded-xl border border-white/[0.08] w-48 max-h-56 overflow-y-auto shadow-2xl"
          style={{ background: '#0F0F1A' }}
        >
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => {
                onSelect(cat.id)
                setOpen(false)
              }}
              className="w-full text-left px-3 py-2 text-sm text-[#F1F5F9] hover:bg-white/[0.06] flex items-center gap-2 transition-colors"
            >
              <span
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ backgroundColor: cat.color ?? '#94a3b8' }}
              />
              {cat.icon ? `${cat.icon} ` : ''}
              {cat.name}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function SkeletonRow() {
  return (
    <div className="flex items-center gap-4 px-4 py-4 border-b border-white/[0.04]">
      <div className="w-10 h-10 rounded-xl bg-white/[0.06] animate-pulse flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="h-3.5 bg-white/[0.06] rounded animate-pulse w-2/5" />
        <div className="h-2.5 bg-white/[0.06] rounded animate-pulse w-1/5" />
      </div>
      <div className="w-20 h-5 bg-white/[0.06] rounded-full animate-pulse" />
      <div className="w-24 h-4 bg-white/[0.06] rounded animate-pulse" />
    </div>
  )
}

export default function Transactions() {
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [categoryId, setCategoryId] = useState<number | undefined>()
  const [type, setType] = useState<'debit' | 'credit' | undefined>()
  const [accountId, setAccountId] = useState<number | undefined>()
  const [page, setPage] = useState(1)
  const queryClient = useQueryClient()

  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const handleSearch = useCallback((value: string) => {
    setSearch(value)
    if (debounceTimer.current) clearTimeout(debounceTimer.current)
    debounceTimer.current = setTimeout(() => {
      setDebouncedSearch(value)
      setPage(1)
    }, 300)
  }, [])

  const filters: TransactionFilters = {
    search: debouncedSearch || undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    category_id: categoryId,
    type,
    account_id: accountId,
    page,
    page_size: 50,
  }

  const txQuery = useQuery({
    queryKey: ['transactions', filters],
    queryFn: () => getTransactions(filters),
  })

  const statsQuery = useQuery({
    queryKey: ['transaction-stats', debouncedSearch, dateFrom, dateTo, categoryId, type, accountId],
    queryFn: () =>
      getTransactionStats({
        search: debouncedSearch || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        account_id: accountId,
        type,
      }),
  })

  const categoriesQuery = useQuery({
    queryKey: ['categories'],
    queryFn: getCategories,
  })

  const accountsQuery = useQuery({
    queryKey: ['accounts'],
    queryFn: getAccounts,
  })

  const updateCategoryMutation = useMutation({
    mutationFn: ({ id, catId }: { id: number; catId: number }) =>
      updateTransactionCategory(id, catId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['category-breakdown'] })
    },
  })

  const categories = categoriesQuery.data ?? []
  const accounts = accountsQuery.data ?? []
  const transactions = txQuery.data?.items ?? []
  const total = txQuery.data?.total ?? 0
  const totalPages = Math.ceil(total / 50)

  return (
    <div className="p-6 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-[#F1F5F9]">Transactions</h1>
          {!txQuery.isLoading && (
            <span className="badge">{total} total</span>
          )}
        </div>
        {!statsQuery.isLoading && statsQuery.data && (
          <div className="flex gap-5 text-sm">
            <span className="text-[#64748B]">
              Income{' '}
              <span className="text-[#10B981] font-semibold tabular-nums">
                {formatINR(statsQuery.data.total_credit)}
              </span>
            </span>
            <span className="text-[#64748B]">
              Expenses{' '}
              <span className="text-[#F43F5E] font-semibold tabular-nums">
                {formatINR(statsQuery.data.total_debit)}
              </span>
            </span>
            <span className="text-[#64748B]">
              Net{' '}
              <span className="text-[#F1F5F9] font-semibold tabular-nums">
                {formatINR(statsQuery.data.net)}
              </span>
            </span>
          </div>
        )}
      </div>

      {/* Filter Bar */}
      <div className="glass-card p-4">
        <div className="flex flex-wrap gap-3">
          {/* Search */}
          <div className="relative flex-1 min-w-48">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#64748B]" />
            <input
              type="text"
              placeholder="Search transactions..."
              value={search}
              onChange={(e) => handleSearch(e.target.value)}
              className="input-dark w-full pl-9"
            />
          </div>

          <input
            type="date"
            value={dateFrom}
            onChange={(e) => { setDateFrom(e.target.value); setPage(1) }}
            className="input-dark"
          />

          <input
            type="date"
            value={dateTo}
            onChange={(e) => { setDateTo(e.target.value); setPage(1) }}
            className="input-dark"
          />

          <select
            value={categoryId ?? ''}
            onChange={(e) => {
              setCategoryId(e.target.value ? Number(e.target.value) : undefined)
              setPage(1)
            }}
            className="select-dark"
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.icon ? `${c.icon} ` : ''}{c.name}
              </option>
            ))}
          </select>

          <select
            value={type ?? ''}
            onChange={(e) => {
              setType((e.target.value as 'debit' | 'credit') || undefined)
              setPage(1)
            }}
            className="select-dark"
          >
            <option value="">All Types</option>
            <option value="credit">Income</option>
            <option value="debit">Expenses</option>
          </select>

          <select
            value={accountId ?? ''}
            onChange={(e) => {
              setAccountId(e.target.value ? Number(e.target.value) : undefined)
              setPage(1)
            }}
            className="select-dark"
          >
            <option value="">All Accounts</option>
            {accounts.map((a) => (
              <option key={a.id} value={a.id}>
                {a.bank_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Transaction Card List */}
      <div className="glass-card overflow-hidden">
        {txQuery.isLoading ? (
          <>
            {Array.from({ length: 8 }).map((_, i) => (
              <SkeletonRow key={i} />
            ))}
          </>
        ) : transactions.length === 0 ? (
          <div className="p-16 text-center">
            <p className="text-[#F1F5F9] font-semibold mb-1">No transactions found</p>
            <p className="text-sm text-[#64748B]">Try adjusting your filters</p>
          </div>
        ) : (
          <>
            {transactions.map((tx) => (
              <div
                key={tx.id}
                className="flex items-center gap-4 px-5 py-4 border-b border-white/[0.04] last:border-0 hover:bg-white/[0.02] transition-colors"
              >
                {/* Category emoji circle */}
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center text-base flex-shrink-0"
                  style={{
                    backgroundColor: tx.category_color
                      ? `${tx.category_color}18`
                      : 'rgba(255,255,255,0.04)',
                  }}
                >
                  {tx.category_icon ?? '💳'}
                </div>

                {/* Description + date */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[#F1F5F9] truncate max-w-sm">
                    {tx.clean_description ?? tx.description}
                  </p>
                  <p className="text-xs text-[#64748B] mt-0.5">
                    {format(new Date(tx.transaction_date), 'dd MMM yyyy')}
                    {tx.merchant_name &&
                      tx.merchant_name !== tx.clean_description &&
                      tx.merchant_name !== tx.description && (
                        <span className="ml-2 text-[#64748B]/70">{tx.merchant_name}</span>
                      )}
                  </p>
                </div>

                {/* Category badge (clickable) */}
                <CategoryBadge
                  tx={tx}
                  categories={categories}
                  onSelect={(catId) => updateCategoryMutation.mutate({ id: tx.id, catId })}
                />

                {/* Amount */}
                <span
                  className={`text-sm font-bold ml-2 flex-shrink-0 tabular-nums ${
                    tx.type === 'credit' ? 'text-[#10B981]' : 'text-[#F43F5E]'
                  }`}
                >
                  {tx.type === 'credit' ? '+' : '-'}
                  {formatINR(tx.amount)}
                </span>
              </div>
            ))}
          </>
        )}

        {/* Pagination */}
        {total > 50 && (
          <div className="flex items-center justify-between px-5 py-4 border-t border-white/[0.06]">
            <span className="text-xs text-[#64748B]">
              {(page - 1) * 50 + 1}–{Math.min(page * 50, total)} of {total}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn-ghost text-xs px-3 py-1.5 disabled:opacity-30"
              >
                <ChevronLeft className="w-4 h-4 inline -mt-0.5" /> Prev
              </button>
              <span className="text-xs text-[#64748B] px-3">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="btn-ghost text-xs px-3 py-1.5 disabled:opacity-30"
              >
                Next <ChevronRight className="w-4 h-4 inline -mt-0.5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
