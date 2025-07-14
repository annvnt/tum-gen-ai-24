'use client'

import React, { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileSpreadsheet, Loader2 } from 'lucide-react'
import axios from 'axios'
import { FinancialReport } from '../types/financial'

interface FileUploadProps {
  onReportGenerated: (report: FinancialReport) => void
  loading: boolean
  setLoading: (loading: boolean) => void
}

export default function FileUpload({ onReportGenerated, loading, setLoading }: FileUploadProps) {
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    setLoading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post('/api/financial/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      if (response.data.success) {
        onReportGenerated(response.data.report)
      } else {
        alert('Error: ' + response.data.error)
      }
    } catch (error) {
      console.error('Upload error:', error)
      alert('Failed to upload file. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [onReportGenerated, setLoading])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    maxFiles: 1,
    disabled: loading,
  })

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
          ${loading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />
        
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