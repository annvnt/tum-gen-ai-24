'use client'

import React, { useCallback, useState } from 'react'
import { Upload, FileSpreadsheet, Loader2 } from 'lucide-react'
import { FinancialReport } from '../types/financial'

interface FileUploadProps {
  onReportGenerated: (report: FinancialReport) => void
  loading: boolean
  setLoading: (loading: boolean) => void
}

export default function FileUpload({ onReportGenerated, loading, setLoading }: FileUploadProps) {
  const [isDragActive, setIsDragActive] = useState(false)

  const handleFileUpload = useCallback(async (file: File) => {
    setLoading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('/api/financial/upload', {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (data.success) {
        onReportGenerated(data.report)
      } else {
        alert('Error: ' + data.error)
      }
    } catch (error) {
      console.error('Upload error:', error)
      alert('Failed to upload file. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [onReportGenerated, setLoading])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragActive(false)
    
    const files = e.dataTransfer.files
    if (files.length > 0) {
      const file = files[0]
      if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        handleFileUpload(file)
      } else {
        alert('Please upload an Excel file (.xlsx or .xls)')
      }
    }
  }, [handleFileUpload])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragActive(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragActive(false)
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileUpload(files[0])
    }
  }, [handleFileUpload])

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
          ${loading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
        onClick={() => {
          if (!loading) {
            document.getElementById('file-input')?.click()
          }
        }}
      >
        <input
          id="file-input"
          type="file"
          accept=".xlsx,.xls"
          onChange={handleFileSelect}
          className="hidden"
          disabled={loading}
        />
        
        <div className="flex flex-col items-center">
          {loading ? (
            <>
              <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" />
              <p className="text-lg font-medium text-gray-700">Processing your file...</p>
              <p className="text-sm text-gray-500 mt-2">This may take a few moments</p>
            </>
          ) : (
            <>
              <div className="mb-4">
                {isDragActive ? (
                  <FileSpreadsheet className="w-12 h-12 text-blue-500" />
                ) : (
                  <Upload className="w-12 h-12 text-gray-400" />
                )}
              </div>
              <p className="text-lg font-medium text-gray-700">
                {isDragActive ? 'Drop your Excel file here' : 'Drag & drop your Excel file here'}
              </p>
              <p className="text-sm text-gray-500 mt-2">or click to select file</p>
              <p className="text-xs text-gray-400 mt-4">Supported formats: .xlsx, .xls</p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}