"use client";

import { useState, useEffect, useRef } from "react";
import {
  Send,
  Paperclip,
  Search,
  FileText,
  BarChart3,
  Download,
  AlertCircle,
  CheckCircle,
  Clock,
  X,
  Plus,
  FileUp,
  RefreshCw,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

interface FileInfo {
  id: string;
  filename: string;
  uploaded_at: string;
  vector_processed: boolean;
  vector_status?: string;
  file_type: string;
  size_category: string;
  relevance_score?: number;
}

interface ChatMessage {
  type: "user" | "bot" | "system";
  content: string;
  timestamp: Date;
  metadata?: any;
}

interface ReportStatus {
  report_id: string;
  status: "generating" | "completed" | "error";
  download_url?: string;
  error?: string;
}

export function EnhancedChatInterface() {
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [availableFiles, setAvailableFiles] = useState<FileInfo[]>([]);
  const [searchResults, setSearchResults] = useState<FileInfo[]>([]);
  const [showFileSelector, setShowFileSelector] = useState(false);
  const [showReportDialog, setShowReportDialog] = useState(false);
  const [reportStatus, setReportStatus] = useState<ReportStatus | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [reportTemplate, setReportTemplate] = useState("comprehensive");
  const [reportTemplates, setReportTemplates] = useState<any[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize session
  useEffect(() => {
    setSessionId(localStorage.getItem("chat_session_id") || generateSessionId());
    loadAvailableFiles();
    loadReportTemplates();
  }, []);

  // Save session ID
  useEffect(() => {
    if (sessionId) {
      localStorage.setItem("chat_session_id", sessionId);
    }
  }, [sessionId]);

  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const generateSessionId = () => {
    return `session_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
  };

  const loadAvailableFiles = async () => {
    try {
      const response = await fetch("/api/enhanced/files/available?limit=50");
      const data = await response.json();
      setAvailableFiles(data.files || []);
    } catch (error) {
      console.error("Error loading files:", error);
      toast.error("Failed to load available files");
    }
  };

  const loadReportTemplates = async () => {
    try {
      const response = await fetch("/api/enhanced/reports/templates");
      const data = await response.json();
      setReportTemplates(data.templates || []);
    } catch (error) {
      console.error("Error loading templates:", error);
    }
  };

  const searchFiles = async (query: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const response = await fetch("/api/enhanced/files/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          search_type: "semantic",
          limit: 10,
        }),
      });
      const data = await response.json();
      setSearchResults(data.results || []);
    } catch (error) {
      console.error("Error searching files:", error);
      toast.error("Failed to search files");
    } finally {
      setIsSearching(false);
    }
  };

  const autoSelectFiles = async (context: string) => {
    try {
      const response = await fetch("/api/enhanced/files/auto-select", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          context,
          max_files: 3,
          criteria: { prefer_processed: true, prefer_recent: true },
        }),
      });
      const data = await response.json();
      const fileIds = data.selected_files.map((f: any) => f.id);
      setSelectedFiles(fileIds);
      
      if (fileIds.length > 0) {
        toast.success(`Auto-selected ${fileIds.length} relevant file(s)`);
      }
    } catch (error) {
      console.error("Error auto-selecting files:", error);
    }
  };

  const handleSend = async () => {
    if (!message.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      type: "user",
      content: message,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentMessage = message;
    setMessage("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/enhanced/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: currentMessage,
          session_id: sessionId,
          context: {
            file_ids: selectedFiles,
            selection_criteria: { prefer_processed: true },
          },
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      const botMessage: ChatMessage = {
        type: "bot",
        content: data.response,
        timestamp: new Date(),
        metadata: {
          status: data.status,
          report_id: data.report_id,
          download_url: data.download_url,
          files_included: data.files_included,
          analysis_results: data.analysis_results,
          search_results: data.search_results,
        },
      };

      setMessages((prev) => [...prev, botMessage]);

      // Handle special responses
      if (data.status === "report_generated" && data.report_id) {
        setReportStatus({
          report_id: data.report_id,
          status: "completed",
          download_url: data.download_url,
        });
        toast.success("Report generated successfully!");
      }

    } catch (error) {
      console.error("Chat error:", error);
      const errorMessage: ChatMessage = {
        type: "bot",
        content: "Sorry, I encountered an error while processing your message. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    if (selectedFiles.length === 0) {
      toast.error("Please select files to generate a report");
      return;
    }

    const reportId = `report_${Date.now()}`;
    setReportStatus({ report_id: reportId, status: "generating" });
    setShowReportDialog(false);

    try {
      const response = await fetch("/api/enhanced/reports/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_ids: selectedFiles,
          template: reportTemplate,
        }),
      });

      const data = await response.json();
      
      if (response.ok) {
        toast.success("Report generation started!");
        
        // Poll for report completion
        const checkStatus = async () => {
          try {
            const statusResponse = await fetch(`/api/financial/report/${data.report_id}`);
            if (statusResponse.ok) {
              setReportStatus({
                report_id: data.report_id,
                status: "completed",
                download_url: `/api/financial/export/${data.report_id}`,
              });
              toast.success("Report ready for download!");
            }
          } catch (error) {
            console.error("Error checking report status:", error);
          }
        };

        setTimeout(checkStatus, 5000); // Check after 5 seconds
      } else {
        throw new Error(data.detail || "Failed to start report generation");
      }
    } catch (error) {
      console.error("Error generating report:", error);
      setReportStatus({
        report_id: reportId,
        status: "error",
        error: error instanceof Error ? error.message : "Unknown error",
      });
      toast.error("Failed to generate report");
    }
  };

  const handleFileSelection = (fileId: string) => {
    setSelectedFiles((prev) =>
      prev.includes(fileId)
        ? prev.filter((id) => id !== fileId)
        : [...prev, fileId]
    );
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const getFileIcon = (fileType: string) => {
    switch (fileType) {
      case "excel":
        return <BarChart3 className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  const FileSelector = () => (
    <Dialog open={showFileSelector} onOpenChange={setShowFileSelector}>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Select Files for Analysis</DialogTitle>
          <DialogDescription>
            Choose files to include in your analysis or report generation
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search files..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                searchFiles(e.target.value);
              }}
              className="pl-9"
            />
          </div>

          <Tabs defaultValue="all">
            <TabsList>
              <TabsTrigger value="all">All Files</TabsTrigger>
              <TabsTrigger value="selected">Selected ({selectedFiles.length})</TabsTrigger>
              <TabsTrigger value="search">Search Results</TabsTrigger>
            </TabsList>

            <TabsContent value="all" className="max-h-96 overflow-y-auto">
              <div className="space-y-2">
                {availableFiles.map((file) => (
                  <Card
                    key={file.id}
                    className={`p-4 cursor-pointer transition-all ${
                      selectedFiles.includes(file.id)
                        ? "border-teal-500 bg-teal-50"
                        : "hover:border-gray-300"
                    }`}
                    onClick={() => handleFileSelection(file.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {getFileIcon(file.file_type)}
                        <div>
                          <p className="font-medium">{file.filename}</p>
                          <p className="text-sm text-gray-500">
                            {new Date(file.uploaded_at).toLocaleDateString()} •
                            {file.vector_processed ? (
                              <span className="text-green-600 ml-1">Processed</span>
                            ) : (
                              <span className="text-orange-600 ml-1">Not processed</span>
                            )}
                          </p>
                        </div>
                      </div>
                      {selectedFiles.includes(file.id) && (
                        <CheckCircle className="h-5 w-5 text-teal-600" />
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="selected" className="max-h-96 overflow-y-auto">
              <div className="space-y-2">
                {availableFiles
                  .filter((file) => selectedFiles.includes(file.id))
                  .map((file) => (
                    <Card key={file.id} className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {getFileIcon(file.file_type)}
                          <span>{file.filename}</span>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleFileSelection(file.id)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </Card>
                  ))}
              </div>
            </TabsContent>

            <TabsContent value="search" className="max-h-96 overflow-y-auto">
              <div className="space-y-2">
                {isSearching ? (
                  <div className="flex items-center justify-center py-8">
                    <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
                  </div>
                ) : searchResults.length > 0 ? (
                  searchResults.map((file) => (
                    <Card
                      key={file.id}
                      className={`p-4 cursor-pointer transition-all ${
                        selectedFiles.includes(file.id)
                          ? "border-teal-500 bg-teal-50"
                          : "hover:border-gray-300"
                      }`}
                      onClick={() => handleFileSelection(file.id)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {getFileIcon(file.file_type)}
                          <div>
                            <p className="font-medium">{file.filename}</p>
                            <p className="text-sm text-gray-500">
                              Relevance: {(file.relevance_score || 0).toFixed(2)}
                            </p>
                          </div>
                        </div>
                        {selectedFiles.includes(file.id) && (
                          <CheckCircle className="h-5 w-5 text-teal-600" />
                        )}
                      </div>
                    </Card>
                  ))
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    No files found matching your search
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowFileSelector(false)}>
              Cancel
            </Button>
            <Button onClick={() => setShowFileSelector(false)}>
              Select Files ({selectedFiles.length})
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );

  const ReportDialog = () => (
    <Dialog open={showReportDialog} onOpenChange={setShowReportDialog}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Generate Financial Report</DialogTitle>
          <DialogDescription>
            Create a comprehensive PDF report from your selected files
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">Report Template</label>
            <Select value={reportTemplate} onValueChange={setReportTemplate}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {reportTemplates.map((template) => (
                  <SelectItem key={template.id} value={template.id}>
                    {template.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-sm font-medium">Selected Files</label>
            <div className="space-y-2">
              {selectedFiles.map((fileId) => {
                const file = availableFiles.find((f) => f.id === fileId);
                return file ? (
                  <div key={fileId} className="text-sm text-gray-600">
                    • {file.filename}
                  </div>
                ) : null;
              })}
            </div>
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowReportDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleGenerateReport} disabled={selectedFiles.length === 0}>
              Generate Report
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-4 py-3">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold">Financial Assistant</h1>
            <p className="text-sm text-gray-500">
              {selectedFiles.length > 0
                ? `${selectedFiles.length} file(s) selected`
                : "Upload and analyze financial documents"}
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFileSelector(true)}
            >
              <FileText className="h-4 w-4 mr-2" />
              Select Files
            </Button>
            <Button
              size="sm"
              onClick={() => setShowReportDialog(true)}
              disabled={selectedFiles.length === 0}
            >
              <Download className="h-4 w-4 mr-2" />
              Generate Report
            </Button>
          </div>
        </div>
      </div>

      {/* Report Status */}
      {reportStatus && (
        <div className="bg-white border-b px-4 py-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {reportStatus.status === "generating" && (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span className="text-sm">Generating report...</span>
                </>
              )}
              {reportStatus.status === "completed" && (
                <>
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span className="text-sm">Report ready!</span>
                </>
              )}
              {reportStatus.status === "error" && (
                <>
                  <AlertCircle className="h-4 w-4 text-red-500" />
                  <span className="text-sm text-red-600">{reportStatus.error}</span>
                </>
              )}
            </div>
            {reportStatus.status === "completed" && reportStatus.download_url && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => window.open(reportStatus.download_url, "_blank")}
              >
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Messages Area */}
      <ScrollArea className="flex-1 px-4 py-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="text-center mb-8">
              <div className="p-4 bg-teal-100 rounded-full w-16 h-16 mx-auto mb-4">
                <BarChart3 className="h-8 w-8 text-teal-600" />
              </div>
              <h2 className="text-2xl font-semibold mb-2">Welcome to Financial Assistant</h2>
              <p className="text-gray-600 mb-6">
                Upload financial documents and ask questions about your data
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4 max-w-md">
              <Card
                className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => {
                  setMessage("List all available files");
                  handleSend();
                }}
              >
                <FileText className="h-6 w-6 mb-2" />
                <p className="text-sm font-medium">List Files</p>
              </Card>
              <Card
                className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => {
                  setMessage("Generate a comprehensive report");
                  handleSend();
                }}
              >
                <Download className="h-6 w-6 mb-2" />
                <p className="text-sm font-medium">Generate Report</p>
              </Card>
            </div>
          </div>
        ) : (
          <div className="space-y-4 max-w-4xl mx-auto">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex ${
                  msg.type === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[80%] p-4 rounded-lg ${
                    msg.type === "user"
                      ? "bg-teal-600 text-white"
                      : "bg-white border border-gray-200"
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  {msg.metadata?.files_included && (
                    <div className="mt-2 text-xs opacity-75">
                      Files: {msg.metadata.files_included.length}
                    </div>
                  )}
                  {msg.metadata?.report_id && (
                    <div className="mt-2 text-xs opacity-75">
                      Report ID: {msg.metadata.report_id}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="max-w-[80%] p-4 rounded-lg bg-white border border-gray-200">
                  <div className="flex items-center space-x-2">
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span className="text-sm text-gray-500">Processing...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </ScrollArea>

      {/* Input Area */}
      <div className="bg-white border-t px-4 py-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about your financial data..."
                className="pr-12"
              />
            </div>
            <Button onClick={handleSend} disabled={!message.trim() || isLoading}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Dialogs */}
      <FileSelector />
      <ReportDialog />
    </div>
  );
}