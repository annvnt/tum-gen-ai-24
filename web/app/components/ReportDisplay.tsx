'use client'

import React from 'react'
import { FinancialReport, FinancialIndicator } from '../types/financial'
import { Download, TrendingUp, TrendingDown } from 'lucide-react'
interface ReportDisplayProps {
  report: FinancialReport
}

export default function ReportDisplay({ report }: ReportDisplayProps) {
  const handleDownload = async () => {
    try {
      const response = await fetch(`/api/financial/export/${report.reportId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        throw new Error('Failed to download report')
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `financial-report-${report.reportId}.xlsx`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Download error:', error)
      alert('Failed to download report')
    }
  }

  const renderTable = (title: string, data: FinancialIndicator[]) => {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-semibold mb-4 text-gray-800">{title}</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Indicator
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Current Year
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Previous Year
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Change
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.map((item, index) => {
                const current = parseFloat(String(item.currentYear).replace(/[^0-9.-]/g, '')) || 0
                const previous = parseFloat(String(item.previousYear).replace(/[^0-9.-]/g, '')) || 0
                const change = previous !== 0 ? ((current - previous) / Math.abs(previous)) * 100 : 0
                
                return (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {item.indicator}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {item.currentYear}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      {item.previousYear}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                      <div className="flex items-center justify-end">
                        {change > 0 ? (
                          <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
                        ) : change < 0 ? (
                          <TrendingDown className="w-4 h-4 text-red-500 mr-1" />
                        ) : null}
                        <span className={change > 0 ? 'text-green-600' : change < 0 ? 'text-red-600' : 'text-gray-600'}>
                          {change.toFixed(1)}%
                        </span>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-start mb-4">
          <h2 className="text-2xl font-bold text-gray-800">Financial Analysis Report</h2>
          <button
            onClick={handleDownload}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            <Download className="w-4 h-4" />
            Download Excel
          </button>
        </div>
        <div className="prose max-w-none">
          <h3 className="text-lg font-semibold mb-2">Executive Summary</h3>
          <div className="whitespace-pre-wrap text-gray-700">{report.summary}</div>
        </div>
      </div>

      <div className="space-y-6">
        {renderTable('Balance Sheet', report.tables.balanceSheet)}
        {renderTable('Income Statement', report.tables.incomeStatement)}
        {renderTable('Cash Flow Statement', report.tables.cashFlowStatement)}
      </div>
    </div>
  )
}