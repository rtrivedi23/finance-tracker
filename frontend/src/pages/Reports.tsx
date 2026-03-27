import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { ChevronLeft, ChevronRight, TrendingUp, TrendingDown, BarChart2, Wallet } from 'lucide-react'
import { getYearlyTrend, getMonthlySummary, getPillarsTrend } from '../api/reports'
import { getAccounts } from '../api/accounts'
import { formatINR, formatINRCompact } from '../utils/currency'

const MONTH_NAMES = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]

const CHART_COLORS = [
  '#8B5CF6', '#6366F1', '#EC4899', '#F59E0B', '#10B981',
  '#06B6D4', '#F97316', '#14B8A6', '#84CC16', '#EF4444',
]

interface CustomTooltipProps {
  active?: boolean
  payload?: { name: string; value: number; color?: string }[]
  label?: string
}

function DarkTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload?.length) return null
  return (
    <div
      className="rounded-xl border border-white/[0.08] px-4 py-3 text-sm shadow-2xl"
      style={{ background: '#0F0F1A' }}
    >
      <p className="text-[#64748B] text-xs mb-2">{label}</p>
      {payload.map((p) => (
        <p key={p.name} className="font-semibold" style={{ color: p.color }}>
          {p.name}: {formatINR(p.value)}
        </p>
      ))}
    </div>
  )
}

export default function Reports() {
  const currentYear = new Date().getFullYear()
  const currentMonth = new Date().getMonth() + 1

  const [year, setYear] = useState(currentYear)
  const [accountId, setAccountId] = useState<number | undefined>()
  const [selectedMonth, setSelectedMonth] = useState<number>(currentMonth)

  const accountsQuery = useQuery({ queryKey: ['accounts'], queryFn: getAccounts })

  const trendQuery = useQuery({
    queryKey: ['yearly-trend', year, accountId],
    queryFn: () => getYearlyTrend(year, accountId),
  })

  const pillarsTrendQuery = useQuery({
    queryKey: ['pillars-trend', year, accountId],
    queryFn: () => getPillarsTrend(year, accountId),
  })

  const monthlySummaryQuery = useQuery({
    queryKey: ['monthly-summary', year, selectedMonth, accountId],
    queryFn: () => getMonthlySummary(year, selectedMonth, accountId),
    enabled: selectedMonth > 0,
  })

  const accounts = accountsQuery.data ?? []
  const trend = trendQuery.data

  const incomeExpenseData =
    trend?.months?.map((m) => ({
      name: MONTH_NAMES[m.month - 1],
      month: m.month,
      Income: m.total_credit,
      Expenses: m.total_debit,
    })) ?? []

  const pillarChartData =
    pillarsTrendQuery.data?.map((m: { month: number; income: number; investments: number; expenses: number }) => ({
      name: MONTH_NAMES[m.month - 1],
      month: m.month,
      Income: m.income,
      Investments: m.investments,
      Expenses: m.expenses,
    })) ?? []

  const monthSummary = monthlySummaryQuery.data
  const categories = monthSummary?.categories ?? []

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[#F1F5F9]">Reports</h1>
        <div className="flex items-center gap-3">
          {/* Year Selector */}
          <div className="flex items-center glass-card overflow-hidden px-1">
            <button
              onClick={() => setYear((y) => y - 1)}
              className="p-2 hover:bg-white/[0.06] transition-colors rounded-lg"
            >
              <ChevronLeft className="w-4 h-4 text-[#64748B]" />
            </button>
            <span className="px-3 text-sm font-semibold text-[#F1F5F9]">{year}</span>
            <button
              onClick={() => setYear((y) => Math.min(currentYear, y + 1))}
              disabled={year >= currentYear}
              className="p-2 hover:bg-white/[0.06] transition-colors rounded-lg disabled:opacity-30"
            >
              <ChevronRight className="w-4 h-4 text-[#64748B]" />
            </button>
          </div>

          <select
            value={accountId ?? ''}
            onChange={(e) => setAccountId(e.target.value ? Number(e.target.value) : undefined)}
            className="select-dark"
          >
            <option value="">All Accounts</option>
            {accounts.map((a) => (
              <option key={a.id} value={a.id}>{a.bank_name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Year Summary Cards */}
      {trend && (
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: 'Total Income', value: trend.total_credit, color: '#10B981', icon: TrendingUp },
            { label: 'Total Expenses', value: trend.total_debit, color: '#F43F5E', icon: TrendingDown },
            { label: 'Net Savings', value: trend.net, color: '#6366F1', icon: Wallet },
            { label: 'Avg Monthly Spend', value: trend.total_debit / 12, color: '#F59E0B', icon: BarChart2 },
          ].map(({ label, value, color, icon: Icon }) => (
            <div key={label} className="glass-card p-5">
              <div className="flex items-center justify-between mb-3">
                <span className="label-tag">{label}</span>
                <div className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: `${color}15` }}>
                  <Icon className="w-4 h-4" style={{ color }} />
                </div>
              </div>
              <p className="text-xl font-bold tabular-nums" style={{ color }}>{formatINR(value)}</p>
            </div>
          ))}
        </div>
      )}

      {/* 3-Pillar Trend Chart */}
      <div className="glass-card p-6">
        <h2 className="text-base font-semibold text-[#F1F5F9] mb-5">
          Income · Investments · Expenses
          <span className="text-xs text-[#64748B] ml-2 font-normal">{year}</span>
        </h2>
        {pillarsTrendQuery.isLoading ? (
          <div className="h-64 bg-white/[0.04] rounded-xl animate-pulse" />
        ) : pillarChartData.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-[#64748B] text-sm">
            No data available for {year}
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={pillarChartData}
              onClick={(data) => {
                if (data?.activePayload?.[0]) {
                  setSelectedMonth(data.activePayload[0].payload.month as number)
                }
              }}
              style={{ cursor: 'pointer' }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748B' }} axisLine={false} tickLine={false} />
              <YAxis tickFormatter={(v) => formatINRCompact(v)} tick={{ fontSize: 10, fill: '#64748B' }} axisLine={false} tickLine={false} />
              <Tooltip content={<DarkTooltip />} />
              <Legend wrapperStyle={{ fontSize: '12px' }} formatter={(value) => (
                <span style={{ color: '#94A3B8' }}>{value}</span>
              )} />
              <Bar dataKey="Income" fill="#10B981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Investments" fill="#6366F1" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Expenses" fill="#F43F5E" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
        <p className="text-xs text-[#64748B] mt-2 text-center">Click a month to see category breakdown</p>
      </div>

      {/* Category Breakdown for selected month */}
      {selectedMonth > 0 && (
        <div className="glass-card p-6">
          <h2 className="text-base font-semibold text-[#F1F5F9] mb-5">
            Category Breakdown
            <span className="text-xs text-[#64748B] ml-2 font-normal">
              {MONTH_NAMES[selectedMonth - 1]} {year}
            </span>
          </h2>

          {monthlySummaryQuery.isLoading ? (
            <div className="h-48 bg-white/[0.04] rounded-xl animate-pulse" />
          ) : categories.length === 0 ? (
            <div className="h-32 flex items-center justify-center text-[#64748B] text-sm">
              No category data for this month
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-8">
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={categories}
                    dataKey="amount"
                    nameKey="category_name"
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    innerRadius={45}
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
                  <Tooltip
                    formatter={(value: number) => formatINR(value)}
                    contentStyle={{
                      background: '#0F0F1A',
                      border: '1px solid rgba(255,255,255,0.08)',
                      borderRadius: '12px',
                      fontSize: '12px',
                      color: '#F1F5F9',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>

              <div className="overflow-y-auto max-h-56 space-y-2 pr-1">
                {categories.map((cat, idx) => {
                  const color = cat.color ?? CHART_COLORS[idx % CHART_COLORS.length]
                  return (
                    <div key={cat.category_name} className="flex items-center gap-3">
                      <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                      <span className="text-sm text-[#F1F5F9] flex-1 truncate">
                        {cat.icon ? `${cat.icon} ` : ''}{cat.category_name}
                      </span>
                      <div className="w-20 h-1 rounded-full bg-white/[0.06] flex-shrink-0">
                        <div className="h-1 rounded-full" style={{ width: `${Math.min(cat.percentage, 100)}%`, backgroundColor: color }} />
                      </div>
                      <span className="text-xs text-[#64748B] w-8 text-right flex-shrink-0">
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

          {monthSummary && (
            <div className="mt-5 pt-4 border-t border-white/[0.06] flex gap-6 text-sm flex-wrap">
              <span className="text-[#64748B]">
                Income <span className="text-[#10B981] font-semibold ml-1">{formatINR(monthSummary.total_credit)}</span>
              </span>
              <span className="text-[#64748B]">
                Expenses <span className="text-[#F43F5E] font-semibold ml-1">{formatINR(monthSummary.total_debit)}</span>
              </span>
              <span className="text-[#64748B]">
                Investments <span className="text-[#6366F1] font-semibold ml-1">{formatINR(monthSummary.investments_total ?? 0)}</span>
              </span>
              <span className="text-[#64748B]">
                Net <span className="text-[#F1F5F9] font-semibold ml-1">{formatINR(monthSummary.net)}</span>
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
