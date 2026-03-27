import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Target, X } from 'lucide-react'
import { getBudgetsVsActual, createBudget, deleteBudget } from '../api/budgets'
import { getCategories } from '../api/categories'
import { formatINR } from '../utils/currency'
import type { BudgetVsActual } from '../api/types'
import clsx from 'clsx'

function ProgressBar({ percentage }: { percentage: number }) {
  const clamped = Math.min(percentage, 100)
  const barColor =
    percentage >= 100
      ? '#F43F5E'
      : percentage >= 90
      ? '#F97316'
      : percentage >= 70
      ? '#F59E0B'
      : '#7C3AED'

  return (
    <div className="w-full rounded-full h-1.5" style={{ background: 'rgba(255,255,255,0.06)' }}>
      <div
        className="h-1.5 rounded-full transition-all duration-500"
        style={{ width: `${clamped}%`, backgroundColor: barColor }}
      />
    </div>
  )
}

function BudgetCard({
  budget,
  onDelete,
}: {
  budget: BudgetVsActual
  onDelete: (id: number) => void
}) {
  const pct = budget.percentage

  return (
    <div className="glass-card p-5">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-2">
          {budget.category_icon && (
            <span className="text-xl">{budget.category_icon}</span>
          )}
          <div>
            <p className="font-semibold text-[#F1F5F9]">
              {budget.category_name ?? `Category #${budget.category_id}`}
            </p>
            <p className="text-xs text-[#64748B] capitalize mt-0.5">{budget.period_type}</p>
          </div>
        </div>
        <button
          onClick={() => onDelete(budget.id)}
          className="text-[#64748B] hover:text-[#F43F5E] transition-colors p-1"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      <ProgressBar percentage={pct} />

      <div className="flex items-center justify-between mt-3">
        <p className="text-sm text-[#64748B]">
          <span className="font-semibold text-[#F1F5F9]">{formatINR(budget.actual)}</span>{' '}
          of{' '}
          <span className="font-semibold text-[#F1F5F9]">{formatINR(budget.amount)}</span>
        </p>
        <span
          className={clsx(
            'text-xs font-semibold px-2 py-0.5 rounded-full',
            pct >= 100
              ? 'bg-[#F43F5E]/10 text-[#F43F5E]'
              : pct >= 70
              ? 'bg-[#F59E0B]/10 text-[#F59E0B]'
              : 'bg-[#10B981]/10 text-[#10B981]'
          )}
        >
          {pct.toFixed(0)}% used
        </span>
      </div>

      {pct >= 100 && (
        <p className="text-xs text-[#F43F5E] mt-2 font-medium">
          Over budget by {formatINR(budget.actual - budget.amount)}
        </p>
      )}
    </div>
  )
}

function AddBudgetModal({
  onClose,
  onSave,
  isPending,
}: {
  onClose: () => void
  onSave: (data: { category_id: number; amount: number; period_type: string }) => void
  isPending: boolean
}) {
  const categoriesQuery = useQuery({ queryKey: ['categories'], queryFn: getCategories })

  const [categoryId, setCategoryId] = useState('')
  const [amount, setAmount] = useState('')
  const period = 'monthly'

  const categories = categoriesQuery.data ?? []

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!categoryId || !amount) return
    onSave({ category_id: Number(categoryId), amount: parseFloat(amount), period_type: period })
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="glass-card w-full max-w-md shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.06]">
          <h2 className="text-base font-semibold text-[#F1F5F9]">Add Budget</h2>
          <button onClick={onClose} className="text-[#64748B] hover:text-[#F1F5F9] transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-medium text-[#64748B] mb-1.5 label-tag">Category</label>
            <select
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              required
              className="select-dark"
            >
              <option value="">Select a category</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.icon ? `${c.icon} ` : ''}{c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-[#64748B] mb-1.5 label-tag">Budget Amount (₹)</label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="e.g. 10000"
              required
              min={1}
              className="input-dark"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-[#64748B] mb-1.5 label-tag">Period</label>
            <div className="input-dark text-[#64748B] cursor-not-allowed">Monthly</div>
          </div>

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="flex-1 btn-ghost">
              Cancel
            </button>
            <button
              type="submit"
              disabled={isPending || !categoryId || !amount}
              className="flex-1 btn-primary disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              {isPending ? 'Saving...' : 'Save Budget'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function Budgets() {
  const [showModal, setShowModal] = useState(false)
  const queryClient = useQueryClient()

  const budgetsQuery = useQuery({
    queryKey: ['budgets-vs-actual'],
    queryFn: getBudgetsVsActual,
  })

  const createMutation = useMutation({
    mutationFn: createBudget,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgets-vs-actual'] })
      setShowModal(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteBudget,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgets-vs-actual'] })
    },
  })

  const budgets = budgetsQuery.data ?? []

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#F1F5F9]">Budgets</h1>
          <p className="text-sm text-[#64748B] mt-0.5">Track your monthly spending limits</p>
        </div>
        <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Add Budget
        </button>
      </div>

      {budgetsQuery.isLoading ? (
        <div className="grid grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="glass-card p-5 h-36 animate-pulse">
              <div className="h-3 bg-white/[0.06] rounded w-1/2 mb-3" />
              <div className="h-1.5 bg-white/[0.06] rounded mb-3" />
              <div className="h-3 bg-white/[0.06] rounded w-2/3" />
            </div>
          ))}
        </div>
      ) : budgets.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-16 h-16 bg-white/[0.04] border border-white/[0.08] rounded-2xl flex items-center justify-center mb-4">
            <Target className="w-8 h-8 text-[#64748B]" />
          </div>
          <h3 className="text-lg font-semibold text-[#F1F5F9] mb-1">No budgets set</h3>
          <p className="text-[#64748B] text-sm max-w-sm mb-6">
            Set budgets to track your spending limits and stay on top of your finances.
          </p>
          <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Add Your First Budget
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-4">
          {budgets.map((budget) => (
            <BudgetCard
              key={budget.id}
              budget={budget}
              onDelete={(id) => deleteMutation.mutate(id)}
            />
          ))}
        </div>
      )}

      {showModal && (
        <AddBudgetModal
          onClose={() => setShowModal(false)}
          onSave={(data) => createMutation.mutate(data)}
          isPending={createMutation.isPending}
        />
      )}
    </div>
  )
}
