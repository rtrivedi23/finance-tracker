import { useQuery } from '@tanstack/react-query'
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { TrendingUp, TrendingDown, BarChart2, ArrowUpRight, Upload } from 'lucide-react'
import { format, startOfMonth } from 'date-fns'
import { Link } from 'react-router-dom'
import { getPillars, getCategoryBreakdown } from '../api/reports'
import { getTransactions } from '../api/transactions'
import { formatINR } from '../utils/currency'

const CHART_COLORS = [
  '#8B5CF6', '#6366F1', '#EC4899', '#F59E0B', '#10B981',
  '#06B6D4', '#F97316', '#14B8A6', '#84CC16', '#EF4444',
]

function SkeletonPillar() {
  return (
    <div className="glass-card p-6 animate-pulse">
      <div className="flex items-center justify-between mb-4">
        <div className="h-3 bg-white/[0.06] rounded w-16" />
        <div className="w-10 h-10 rounded-xl bg-white/[0.06]" />
      </div>
      <div className="h-8 bg-white/[0.06] rounded w-2/3 mb-2" />
      <div className="h-3 bg-white/[0.06] rounded w-1/3" />
    </div>
  )
}

interface CustomTooltipProps {
  active?: boolean
  payload?: { name: string; value: number; payload: { color?: string } }[]
}

function CustomDonutTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.length) return null
  const item = payload[0]
  return (
    <div
      className="rounded-xl border border-white/[0.08] px-4 py-3 text-sm"
      style={{ background: '#0F0F1A' }}
    >
      <p className="text-[#F1F5F9] font-medium mb-1">{item.name}</p>
      <p className="text-[#7C3AED] font-bold">{formatINR(item.value)}</p>
    </div>
  )
}

export default function Dashboard() {
  const now = new Date()
  const dateFrom = format(startOfMonth(now), 'yyyy-MM-dd')
  const dateTo = format(now, 'yyyy-MM-dd')

  const pillarsQuery = useQuery({
    queryKey: ['pillars', dateFrom, dateTo],
    queryFn: () => getPillars(dateFrom, dateTo),
  })

  const categoryQuery = useQuery({
    queryKey: ['category-breakdown', dateFrom, dateTo],
    queryFn: () => getCategoryBreakdown(dateFrom, dateTo),
  })

  const recentQuery = useQuery({
    queryKey: ['recent-transactions'],
    queryFn: () => getTransactions({ page: 1, page_size: 8 }),
  })

  const pillars = pillarsQuery.data
  const categories = categoryQuery.data ?? []
  const transactions = recentQuery.data?.items ?? []
  const total = recentQuery.data?.total ?? 0

  const isEmpty =
    !pillarsQuery.isLoading &&
    !recentQuery.isLoading &&
    total === 0 &&
    !pillars?.income?.count &&
    !pillars?.expenses?.count

  if (isEmpty) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-12 text-center">
        <div className="glass-card p-12 max-w-sm w-full flex flex-col items-center">
          <div className="w-20 h-20 rounded-2xl bg-[#7C3AED]/10 border border-[#7C3AED]/20 flex items-center justify-center mb-6">
            <Upload className="w-10 h-10 text-[#7C3AED]" />
          </div>
          <h2 className="text-2xl font-bold text-[#F1F5F9] mb-2">No transactions yet</h2>
          <p className="text-[#64748B] mb-8 text-sm leading-relaxed">
            Import your first statement to start tracking your finances.
          </p>
          <Link to="/upload" className="btn-primary w-full text-center">
            Import Statement
          </Link>
        </div>
      </div>
    )
  }

  const incomeTotal = pillars?.income?.total ?? 0
  const incomeCount = pillars?.income?.count ?? 0
  const expensesTotal = pillars?.expenses?.total ?? 0
  const expensesCount = pillars?.expenses?.count ?? 0
  const investmentsTotal = pillars?.investments?.total ?? 0
  const investmentsCount = pillars?.investments?.count ?? 0

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-[#F1F5F9]">
          Good morning, Riveshu
        </h1>
        <p className="text-sm text-[#64748B] mt-1">
          {format(now, 'EEEE, d MMMM yyyy')} &middot; {format(startOfMonth(now), 'MMMM yyyy')}
        </p>
      </div>

      {/* Pillar Cards */}
      <div className="grid grid-cols-3 gap-4">
        {pillarsQuery.isLoading ? (
          <>
            <SkeletonPillar />
            <SkeletonPillar />
            <SkeletonPillar />
          </>
        ) : (
          <>
            {/* Income */}
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-4">
                <span className="label-tag">Income</span>
                <div className="w-10 h-10 rounded-xl bg-[#10B981]/10 flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-[#10B981]" />
                </div>
              </div>
              <p className="stat-number text-[#10B981]">{formatINR(incomeTotal)}</p>
              <p className="text-xs text-[#64748B] mt-1">{incomeCount} transactions</p>
            </div>

            {/* Expenses */}
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-4">
                <span className="label-tag">Expenses</span>
                <div className="w-10 h-10 rounded-xl bg-[#F43F5E]/10 flex items-center justify-center">
                  <TrendingDown className="w-5 h-5 text-[#F43F5E]" />
                </div>
              </div>
              <p className="stat-number text-[#F43F5E]">{formatINR(expensesTotal)}</p>
              <p className="text-xs text-[#64748B] mt-1">{expensesCount} transactions</p>
            </div>

            {/* Investments */}
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-4">
                <span className="label-tag">Investments</span>
                <div className="w-10 h-10 rounded-xl bg-[#6366F1]/10 flex items-center justify-center">
                  <BarChart2 className="w-5 h-5 text-[#6366F1]" />
                </div>
              </div>
              <p className="stat-number text-[#6366F1]">{formatINR(investmentsTotal)}</p>
              <p className="text-xs text-[#64748B] mt-1">{investmentsCount} transactions</p>
            </div>
          </>
        )}
      </div>

      {/* Category Breakdown */}
      <div className="glass-card p-6">
        <h2 className="text-base font-semibold text-[#F1F5F9] mb-6">
          Category Breakdown
          <span className="text-xs text-[#64748B] ml-2 font-normal">
            {format(startOfMonth(now), 'MMMM yyyy')}
          </span>
        </h2>

        {categoryQuery.isLoading ? (
          <div className="h-64 bg-white/[0.06] rounded-xl animate-pulse" />
        ) : categories.length === 0 ? (
          <div className="h-48 flex items-center justify-center text-[#64748B] text-sm">
            No category data available
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-8">
            {/* Donut Chart */}
            <div className="flex items-center justify-center">
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={categories}
                    dataKey="amount"
                    nameKey="category_name"
                    cx="50%"
                    cy="50%"
                    outerRadius={120}
                    innerRadius={70}
                    paddingAngle={2}
                    strokeWidth={0}
                  >
                    {categories.map((entry, index) => (
                      <Cell
                        key={entry.category_name}
                        fill={entry.color ?? CHART_COLORS[index % CHART_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomDonutTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Category List */}
            <div className="space-y-3 overflow-y-auto max-h-72 pr-1">
              {categories.map((cat, idx) => {
                const color = cat.color ?? CHART_COLORS[idx % CHART_COLORS.length]
                return (
                  <div key={cat.category_name} className="flex items-center gap-3">
                    <span
                      className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                      style={{ backgroundColor: color }}
                    />
                    <span className="text-sm text-[#F1F5F9] flex-1 truncate">
                      {cat.icon ? `${cat.icon} ` : ''}
                      {cat.category_name}
                    </span>
                    <div className="w-24 h-1 rounded-full bg-white/[0.06] flex-shrink-0">
                      <div
                        className="h-1 rounded-full"
                        style={{ width: `${Math.min(cat.percentage, 100)}%`, backgroundColor: color }}
                      />
                    </div>
                    <span className="text-xs text-[#64748B] w-10 text-right flex-shrink-0">
                      {cat.percentage.toFixed(0)}%
                    </span>
                    <span className="text-sm font-semibold text-[#F1F5F9] w-24 text-right flex-shrink-0 tabular-nums">
                      {formatINR(cat.amount)}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {/* Recent Transactions */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold text-[#F1F5F9]">Recent Transactions</h2>
          <Link
            to="/transactions"
            className="text-xs text-[#7C3AED] hover:text-[#9D5CF6] flex items-center gap-1 transition-colors"
          >
            View all <ArrowUpRight className="w-3 h-3" />
          </Link>
        </div>

        {recentQuery.isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-12 bg-white/[0.06] rounded-xl animate-pulse" />
            ))}
          </div>
        ) : transactions.length === 0 ? (
          <div className="h-32 flex items-center justify-center text-[#64748B] text-sm">
            No transactions yet
          </div>
        ) : (
          <div className="space-y-1">
            {transactions.map((tx) => (
              <div
                key={tx.id}
                className="flex items-center justify-between py-3 border-b border-white/[0.04] last:border-0"
              >
                {/* Left: emoji + description + date */}
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div
                    className="w-9 h-9 rounded-xl flex items-center justify-center text-base flex-shrink-0"
                    style={{
                      backgroundColor: tx.category_color
                        ? `${tx.category_color}18`
                        : 'rgba(255,255,255,0.04)',
                    }}
                  >
                    {tx.category_icon ?? '💳'}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-[#F1F5F9] truncate max-w-xs">
                      {tx.clean_description ?? tx.description}
                    </p>
                    <p className="text-xs text-[#64748B] mt-0.5">
                      {format(new Date(tx.transaction_date), 'dd MMM')}
                      {tx.category_name && (
                        <span
                          className="ml-2 px-1.5 py-0.5 rounded-md text-[10px] font-medium"
                          style={{
                            backgroundColor: tx.category_color
                              ? `${tx.category_color}20`
                              : 'rgba(255,255,255,0.06)',
                            color: tx.category_color ?? '#94a3b8',
                          }}
                        >
                          {tx.category_name}
                        </span>
                      )}
                    </p>
                  </div>
                </div>

                {/* Right: amount */}
                <span
                  className={`text-sm font-bold ml-4 flex-shrink-0 tabular-nums ${
                    tx.type === 'credit' ? 'text-[#10B981]' : 'text-[#F43F5E]'
                  }`}
                >
                  {tx.type === 'credit' ? '+' : '-'}
                  {formatINR(tx.amount)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
