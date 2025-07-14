"use client";

import { useState, useEffect } from "react";
import { ChatInterface } from "@/components/ChatInterface";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";

export default function Home() {
  const [financialReport, setFinancialReport] = useState(null);

  useEffect(() => {
    // Check for financial report in localStorage
    const storedReport = localStorage.getItem('financialReport');
    if (storedReport) {
      try {
        setFinancialReport(JSON.parse(storedReport));
        localStorage.removeItem('financialReport'); // Clear after loading
      } catch (error) {
        console.error('Error parsing financial report:', error);
      }
    }
  }, []);

  const closeFnancialReport = () => {
    setFinancialReport(null);
  };

  if (financialReport) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold text-gray-900">Financial Analysis Report</h1>
            <Button
              variant="outline"
              onClick={closeFnancialReport}
              className="flex items-center gap-2"
            >
              <X className="h-4 w-4" />
              Back to Chat
            </Button>
          </div>
          
          {/* Financial Report Content */}
          <div className="space-y-6">
            {/* Summary */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">Executive Summary</h2>
              <div className="whitespace-pre-wrap text-gray-700">
                {financialReport.summary}
              </div>
            </div>

            {/* Tables */}
            {financialReport.tables && (
              <div className="grid gap-6">
                {financialReport.tables.balanceSheet && financialReport.tables.balanceSheet.length > 0 && (
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-lg font-semibold mb-4">Balance Sheet</h3>
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Item</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Current Year</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Previous Year</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {financialReport.tables.balanceSheet.map((item, index) => (
                            <tr key={index}>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.indicator}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">{item.currentYear}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">{item.previousYear}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {financialReport.tables.incomeStatement && financialReport.tables.incomeStatement.length > 0 && (
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-lg font-semibold mb-4">Income Statement</h3>
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Item</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Current Year</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Previous Year</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {financialReport.tables.incomeStatement.map((item, index) => (
                            <tr key={index}>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.indicator}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">{item.currentYear}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">{item.previousYear}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {financialReport.tables.cashFlowStatement && financialReport.tables.cashFlowStatement.length > 0 && (
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-lg font-semibold mb-4">Cash Flow Statement</h3>
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Item</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Current Year</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Previous Year</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {financialReport.tables.cashFlowStatement.map((item, index) => (
                            <tr key={index}>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.indicator}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">{item.currentYear}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">{item.previousYear}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50">
      <ChatInterface />
    </div>
  );
}