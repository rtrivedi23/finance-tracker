import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload as UploadIcon, FileText, CheckCircle2, AlertCircle, X, Eye } from 'lucide-react'
import { Link } from 'react-router-dom'
import clsx from 'clsx'
import { uploadStatement } from '../api/upload'
import type { UploadResponse } from '../api/types'
import { format, parseISO } from 'date-fns'

const SUPPORTED_BANKS = [
  'HDFC Bank', 'ICICI Bank', 'SBI', 'Axis Bank', 'Kotak Bank', 'Yes Bank', 'IndusInd',
]

export default function Upload() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [result, setResult] = useState<UploadResponse | null>(null)
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: uploadStatement,
    onSuccess: (data) => {
      setResult(data)
      setSelectedFile(null)
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['transaction-stats'] })
      queryClient.invalidateQueries({ queryKey: ['recent-transactions'] })
      queryClient.invalidateQueries({ queryKey: ['category-breakdown'] })
      queryClient.invalidateQueries({ queryKey: ['pillars'] })
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
    },
  })

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        setSelectedFile(acceptedFiles[0])
        setResult(null)
        mutation.reset()
      }
    },
    [mutation]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    multiple: false,
  })

  const handleUpload = () => {
    if (selectedFile) mutation.mutate(selectedFile)
  }

  const handleClear = () => {
    setSelectedFile(null)
    setResult(null)
    mutation.reset()
  }

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-[#F1F5F9]">Import Statement</h1>
        <p className="text-sm text-[#64748B] mt-1">
          Upload your bank statement to automatically parse and categorize transactions.
        </p>
      </div>

      {/* Success Card */}
      {result && (
        <div className="glass-card overflow-hidden">
          {/* Green gradient top bar */}
          <div className="h-1.5 w-full bg-gradient-to-r from-[#10B981] to-[#059669]" />
          <div className="p-6">
            <div className="flex items-start gap-4">
              <div className="w-11 h-11 rounded-xl bg-[#10B981]/10 flex items-center justify-center flex-shrink-0">
                <CheckCircle2 className="w-6 h-6 text-[#10B981]" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-[#F1F5F9] text-lg">Upload Successful!</h3>
                <div className="mt-4 space-y-2.5 text-sm">
                  <div className="flex gap-2">
                    <span className="text-[#64748B] w-32 flex-shrink-0">Bank</span>
                    <span className="text-[#F1F5F9] font-medium">{result.bank_name}</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-[#64748B] w-32 flex-shrink-0">File</span>
                    <span className="text-[#F1F5F9]">{result.filename}</span>
                  </div>
                  {(result as any).duplicate ? (
                    <div className="flex gap-2">
                      <span className="text-[#64748B] w-32 flex-shrink-0">Status</span>
                      <span className="text-[#F59E0B] font-medium">Already imported previously</span>
                    </div>
                  ) : (
                    <div className="flex gap-2">
                      <span className="text-[#64748B] w-32 flex-shrink-0">Transactions</span>
                      <span className="text-[#10B981] font-semibold">
                        {result.transaction_count} imported
                      </span>
                    </div>
                  )}
                  {result.period_from && result.period_to && (
                    <div className="flex gap-2">
                      <span className="text-[#64748B] w-32 flex-shrink-0">Date Range</span>
                      <span className="text-[#F1F5F9]">
                        {format(parseISO(result.period_from), 'dd MMM yyyy')} —{' '}
                        {format(parseISO(result.period_to), 'dd MMM yyyy')}
                      </span>
                    </div>
                  )}
                  <div className="flex gap-2">
                    <span className="text-[#64748B] w-32 flex-shrink-0">Parse Status</span>
                    <span
                      className={clsx(
                        'font-medium capitalize',
                        result.parse_status === 'success'
                          ? 'text-[#10B981]'
                          : 'text-[#F59E0B]'
                      )}
                    >
                      {result.parse_status}
                    </span>
                  </div>
                </div>

                {(result.parse_warnings ?? []).length > 0 && (
                  <div className="mt-4 rounded-xl border border-[#F59E0B]/20 bg-[#F59E0B]/[0.06] p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertCircle className="w-4 h-4 text-[#F59E0B]" />
                      <span className="text-sm font-medium text-[#F59E0B]">Warnings</span>
                    </div>
                    <ul className="text-xs text-[#F59E0B]/80 space-y-1 list-disc list-inside">
                      {result.parse_warnings.map((w, i) => (
                        <li key={i}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="flex gap-3 mt-6">
                  <Link to="/transactions" className="btn-primary flex items-center gap-2">
                    <Eye className="w-4 h-4" />
                    View Transactions
                  </Link>
                  <button onClick={handleClear} className="btn-ghost">
                    Upload Another
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {mutation.isError && (
        <div className="glass-card border border-[#F43F5E]/20 bg-[#F43F5E]/[0.04] p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-[#F43F5E] flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-[#F43F5E]">Upload failed</p>
            <p className="text-sm text-[#F43F5E]/70 mt-0.5">{mutation.error?.message}</p>
          </div>
        </div>
      )}

      {/* Drop Zone */}
      {!result && (
        <div className="glass-card p-6 space-y-4">
          <div
            {...getRootProps()}
            className={clsx(
              'border-2 border-dashed rounded-2xl p-14 text-center cursor-pointer transition-all',
              isDragActive
                ? 'border-[#7C3AED] bg-[#7C3AED]/[0.06]'
                : 'border-white/20 hover:border-white/30 hover:bg-white/[0.02]'
            )}
          >
            <input {...getInputProps()} />
            <div className="flex flex-col items-center gap-4">
              <div
                className={clsx(
                  'w-16 h-16 rounded-2xl flex items-center justify-center transition-colors',
                  isDragActive ? 'bg-[#7C3AED]/20' : 'bg-white/[0.06]'
                )}
              >
                <UploadIcon
                  className={clsx(
                    'w-8 h-8 transition-colors',
                    isDragActive ? 'text-[#7C3AED]' : 'text-[#64748B]'
                  )}
                />
              </div>
              {isDragActive ? (
                <p className="text-[#7C3AED] font-semibold text-lg">Drop your file here</p>
              ) : (
                <>
                  <div>
                    <p className="text-[#F1F5F9] font-semibold text-base">
                      Drop your bank statement here
                    </p>
                    <p className="text-[#64748B] text-sm mt-1">or click to browse files</p>
                  </div>
                  <p className="text-xs text-[#64748B] px-4 py-2 rounded-full bg-white/[0.04] border border-white/[0.06]">
                    Supports PDF, CSV, XLSX
                  </p>
                </>
              )}
            </div>
          </div>

          {/* Selected File */}
          {selectedFile && (
            <div className="flex items-center justify-between bg-[#7C3AED]/[0.08] border border-[#7C3AED]/20 rounded-xl px-4 py-3">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-[#7C3AED]/20 flex items-center justify-center">
                  <FileText className="w-5 h-5 text-[#7C3AED]" />
                </div>
                <div>
                  <p className="text-sm font-medium text-[#F1F5F9]">{selectedFile.name}</p>
                  <p className="text-xs text-[#64748B]">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); handleClear() }}
                className="text-[#64748B] hover:text-[#F1F5F9] transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Upload Button */}
          <button
            onClick={handleUpload}
            disabled={!selectedFile || mutation.isPending}
            className={clsx(
              'w-full py-3 rounded-xl text-sm font-semibold transition-all',
              selectedFile && !mutation.isPending
                ? 'btn-primary'
                : 'bg-white/[0.04] text-[#64748B] cursor-not-allowed border border-white/[0.06]'
            )}
          >
            {mutation.isPending ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                Uploading & Processing...
              </span>
            ) : (
              'Upload Statement'
            )}
          </button>
        </div>
      )}

      {/* Supported Banks */}
      <div>
        <p className="text-xs text-[#64748B] mb-3 label-tag">Supported Banks</p>
        <div className="flex flex-wrap gap-2">
          {SUPPORTED_BANKS.map((bank) => (
            <span
              key={bank}
              className="text-xs px-3 py-1.5 rounded-full bg-white/[0.04] border border-white/[0.08] text-[#64748B]"
            >
              {bank}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
