"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
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
  Mic, 
  StopCircle,
  Image,
  FileSpreadsheet,
  FileQuestion,
  Sparkles,
  Bot,
  User,
  Settings,
  Share2,
  Copy,
  ThumbsUp,
  ThumbsDown,
  MoreVertical,
  Menu,
  MessageSquare,
  Zap,
  TrendingUp,
  PieChart,
  Calendar,
  Filter,
  Star,
  Archive,
  Trash2,
  Eye,
  EyeOff,
  Maximize2,
  Minimize2
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";

interface FileInfo {
  id: string;
  filename: string;
  uploaded_at: string;
  vector_processed: boolean;
  vector_status?: string;
  file_type: string;
  size_category: string;
  relevance_score?: number;
  file_size: number;
  preview?: string;
}

interface ChatMessage {
  id: string;
  type: "user" | "bot" | "system";
  content: string;
  timestamp: Date;
  metadata?: {
    status?: string;
    report_id?: string;
    download_url?: string;
    files_included?: string[];
    analysis_results?: any;
    search_results?: any;
    confidence?: number;
    sources?: Array<{
      file_id: string;
      filename: string;
      relevance: number;
      excerpt?: string;
    }>;
  };
  attachments?: FileInfo[];
  reactions?: {
    liked?: boolean;
    disliked?: boolean;
  };
}

interface ReportStatus {
  report_id: string;
  status: "generating" | "completed" | "error";
  download_url?: string;
  error?: string;
  progress?: number;
}

interface UploadProgress {
  fileId: string;
  filename: string;
  progress: number;
  status: "uploading" | "processing" | "completed" | "error";
  error?: string;
}

interface ChatSession {
  id: string;
  title: string;
  lastMessage: Date;
  messageCount: number;
  selectedFiles: string[];
}

export function AdvancedChatInterface() {
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
  const [uploadProgress, setUploadProgress] = useState<UploadProgress[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  const [autoProcessFiles, setAutoProcessFiles] = useState(true);
  const [maxContextFiles, setMaxContextFiles] = useState(5);
  const [showSourceExcerpts, setShowSourceExcerpts] = useState(true);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Initialize session
  useEffect(() => {
    const savedSessionId = localStorage.getItem("chat_session_id");
    const newSessionId = savedSessionId || generateSessionId();
    setSessionId(newSessionId);
    
    if (!savedSessionId) {
      localStorage.setItem("chat_session_id", newSessionId);
    }
    
    loadAvailableFiles();
    loadReportTemplates();
    loadChatSessions();
    loadUserPreferences();
  }, []);

  // Save user preferences
  const loadUserPreferences = () => {
    const prefs = localStorage.getItem("chat_preferences");
    if (prefs) {
      const { autoProcess, maxFiles, showSources } = JSON.parse(prefs);
      setAutoProcessFiles(autoProcess ?? true);
      setMaxContextFiles(maxFiles ?? 5);
      setShowSourceExcerpts(showSources ?? true);
    }
  };

  const saveUserPreferences = () => {
    localStorage.setItem("chat_preferences", JSON.stringify({
      autoProcess: autoProcessFiles,
      maxFiles: maxContextFiles,
      showSources: showSourceExcerpts
    }));
  };

  useEffect(() => {
    saveUserPreferences();
  }, [autoProcessFiles, maxContextFiles, showSourceExcerpts]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Load chat sessions
  const loadChatSessions = async () => {
    try {
      const response = await fetch("/api/chat/sessions");
      const data = await response.json();
      setChatSessions(data.sessions || []);
    } catch (error) {
      console.error("Error loading sessions:", error);
    }
  };

  const generateSessionId = () => {
    return `session_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
  };

  // File upload with drag and drop
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    for (const file of acceptedFiles) {
      await uploadFile(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
      "text/csv": [".csv"],
      "application/pdf": [".pdf"]
    },
    maxFiles: 10,
    maxSize: 50 * 1024 * 1024, // 50MB
  });

  const uploadFile = async (file: File) => {
    const fileId = `file_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
    const uploadItem: UploadProgress = {
      fileId,
      filename: file.name,
      progress: 0,
      status: "uploading"
    };
    
    setUploadProgress(prev => [...prev, uploadItem]);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/api/financial/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const data = await response.json();
      
      setUploadProgress(prev => 
        prev.map(item => 
          item.fileId === fileId 
            ? { ...item, status: "processing", progress: 100 }
            : item
        )
      );

      if (autoProcessFiles) {
        await processFileForVectors(data.file_id, fileId);
      }

      toast.success(`File "${file.name}" uploaded successfully`);
      loadAvailableFiles();
      
      // Remove from progress after 3 seconds
      setTimeout(() => {
        setUploadProgress(prev => prev.filter(item => item.fileId !== fileId));
      }, 3000);

    } catch (error) {
      console.error("Error uploading file:", error);
      setUploadProgress(prev => 
        prev.map(item => 
          item.fileId === fileId 
            ? { ...item, status: "error", error: "Upload failed" }
            : item
        )
      );
      toast.error(`Failed to upload "${file.name}"`);
    }
  };

  const processFileForVectors = async (fileId: string, uploadId: string) => {
    try {
      const response = await fetch("/api/vector/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_id: fileId,
          metadata: { source: "chat_upload" },
        }),
      });

      if (response.ok) {
        // Poll for completion
        const checkStatus = async () => {
          try {
            const statusResponse = await fetch(`/api/vector/status/${fileId}`);
            const statusData = await statusResponse.json();
            
            if (statusData.status === "completed") {
              toast.success("File processed and ready for analysis");
              loadAvailableFiles();
            } else if (statusData.status === "processing") {
              setTimeout(checkStatus, 2000);
            }
          } catch (error) {
            console.error("Error checking status:", error);
          }
        };

        setTimeout(checkStatus, 1000);
      }
    } catch (error) {
      console.error("Error processing file:", error);
    }
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
          max_files: maxContextFiles,
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
      id: `msg_${Date.now()}_user`,
      type: "user",
      content: message,
      timestamp: new Date(),
      attachments: availableFiles.filter(f => selectedFiles.includes(f.id)),
    };

    setMessages(prev => [...prev, userMessage]);
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
            show_sources: showSourceExcerpts,
          },
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      const botMessage: ChatMessage = {
        id: `msg_${Date.now()}_bot`,
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
          confidence: data.confidence,
          sources: data.sources,
        },
      };

      setMessages(prev => [...prev, botMessage]);

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
        id: `msg_${Date.now()}_error`,
        type: "bot",
        content: "Sorry, I encountered an error while processing your message. Please try again.",
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
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
    setReportStatus({ report_id: reportId, status: "generating", progress: 0 });
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

        setTimeout(checkStatus, 5000);
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
    setSelectedFiles(prev =>
      prev.includes(fileId)
        ? prev.filter(id => id !== fileId)
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
      case "pdf":
        return <FileText className="h-4 w-4" />;
      case "csv":
        return <FileSpreadsheet className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  const toggleReaction = (messageId: string, reaction: 'liked' | 'disliked') => {
    setMessages(prev => prev.map(msg => {
      if (msg.id === messageId) {
        return {
          ...msg,
          reactions: {
            ...msg.reactions,
            [reaction]: !msg.reactions?.[reaction]
          }
        };
      }
      return msg;
    }));
  };

  const copyMessage = (content: string) => {
    navigator.clipboard.writeText(content);
    toast.success("Message copied to clipboard");
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      {/* Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            exit={{ x: -300 }}
            transition={{ type: "spring", damping: 20 }}
            className="w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col"
          >
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Sessions</h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSidebarOpen(false)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <ScrollArea className="flex-1">
              <div className="p-4 space-y-2">
                {chatSessions.map(session => (
                  <Card
                    key={session.id}
                    className={cn(
                      "p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors",
                      session.id === sessionId && "bg-teal-50 dark:bg-teal-900/20 border-teal-200"
                    )}
                  >
                    <div>
                      <p className="font-medium text-sm truncate">{session.title}</p>
                      <p className="text-xs text-gray-500">
                        {formatDistanceToNow(session.lastMessage, { addSuffix: true })}
                      </p>
                    </div>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSidebarOpen(!sidebarOpen)}
              >
                <Menu className="h-4 w-4" />
              </Button>
              <div>
                <h1 className="text-lg font-semibold">Financial AI Assistant</h1>
                <p className="text-sm text-gray-500">
                  {selectedFiles.length > 0
                    ? `${selectedFiles.length} file(s) selected`
                    : "Ready to analyze your documents"}
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowFileSelector(true)}
              >
                <FileText className="h-4 w-4 mr-2" />
                Files
              </Button>
              <Button
                size="sm"
                onClick={() => setShowReportDialog(true)}
                disabled={selectedFiles.length === 0}
              >
                <Download className="h-4 w-4 mr-2" />
                Report
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowSettings(true)}
              >
                <Settings className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Upload Progress */}
        <AnimatePresence>
          {uploadProgress.length > 0 && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="bg-blue-50 dark:bg-blue-900/20 border-b border-blue-200 dark:border-blue-800 px-4 py-2"
            >
              <div className="space-y-2">
                {uploadProgress.map(item => (
                  <div key={item.fileId} className="flex items-center gap-3">
                    <FileText className="h-4 w-4 text-blue-600" />
                    <div className="flex-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium">{item.filename}</span>
                        <span className="text-gray-500">
                          {item.status === "uploading" && "Uploading..."}
                          {item.status === "processing" && "Processing..."}
                          {item.status === "completed" && "Complete"}
                          {item.status === "error" && "Error"}
                        </span>
                      </div>
                      <Progress value={item.progress} className="h-2" />
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Report Status */}
        <AnimatePresence>
          {reportStatus && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-2"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {reportStatus.status === "generating" && (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      <span className="text-sm">Generating report...</span>
                      {reportStatus.progress && (
                        <Progress value={reportStatus.progress} className="w-32 h-2" />
                      )}
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
            </motion.div>
          )}
        </AnimatePresence>

        {/* Messages Area */}
        <div className="flex-1 relative">
          <ScrollArea className="h-full px-4 py-4">
            <div className="max-w-4xl mx-auto space-y-4">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full px-4">
                  <div className="text-center mb-8">
                    <motion.div
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ duration: 0.5 }}
                      className="p-4 bg-gradient-to-br from-teal-100 to-blue-100 dark:from-teal-900/30 dark:to-blue-900/30 rounded-full w-20 h-20 mx-auto mb-6"
                    >
                      <Bot className="h-12 w-12 text-teal-600 dark:text-teal-400" />
                    </motion.div>
                    <h2 className="text-3xl font-bold mb-3">Welcome to Financial AI</h2>
                    <p className="text-gray-600 dark:text-gray-400 mb-8 max-w-md">
                      Upload financial documents and ask questions about your data. 
                      I can analyze trends, generate reports, and provide insights.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-4xl">
                    <Card
                      className="p-6 cursor-pointer hover:shadow-lg transition-all hover:scale-105"
                      onClick={() => {
                        setMessage("List all available financial documents");
                        handleSend();
                      }}
                    >
                      <FileText className="h-8 w-8 mb-3 text-blue-500" />
                      <h3 className="font-semibold mb-2">List Documents</h3>
                      <p className="text-sm text-gray-600">View all uploaded financial files</p>
                    </Card>
                    <Card
                      className="p-6 cursor-pointer hover:shadow-lg transition-all hover:scale-105"
                      onClick={() => {
                        setMessage("Generate a comprehensive financial analysis report");
                        handleSend();
                      }}
                    >
                      <BarChart3 className="h-8 w-8 mb-3 text-green-500" />
                      <h3 className="font-semibold mb-2">Generate Report</h3>
                      <p className="text-sm text-gray-600">Create detailed financial reports</p>
                    </Card>
                    <Card
                      className="p-6 cursor-pointer hover:shadow-lg transition-all hover:scale-105"
                      onClick={() => {
                        setMessage("Analyze trends and patterns in my financial data");
                        handleSend();
                      }}
                    >
                      <TrendingUp className="h-8 w-8 mb-3 text-purple-500" />
                      <h3 className="font-semibold mb-2">Analyze Trends</h3>
                      <p className="text-sm text-gray-600">Identify patterns and insights</p>
                    </Card>
                  </div>

                  {/* Drop Zone */}
                  <div
                    {...getRootProps()}
                    className={cn(
                      "mt-8 p-8 border-2 border-dashed rounded-lg transition-all cursor-pointer",
                      isDragActive 
                        ? "border-teal-500 bg-teal-50 dark:bg-teal-900/20" 
                        : "border-gray-300 dark:border-gray-600 hover:border-gray-400"
                    )}
                  >
                    <input {...getInputProps()} />
                    <FileUp className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                    <p className="text-lg font-medium mb-2">
                      {isDragActive ? "Drop files here" : "Upload Financial Documents"}
                    </p>
                    <p className="text-sm text-gray-600">
                      Drag & drop Excel, CSV, or PDF files here to get started
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {messages.map((msg, index) => (
                    <motion.div
                      key={msg.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: index * 0.1 }}
                      className={cn(
                        "flex gap-4",
                        msg.type === "user" ? "justify-end" : "justify-start"
                      )}
                    >
                      {msg.type === "bot" && (
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-blue-500 flex items-center justify-center flex-shrink-0">
                          <Bot className="h-4 w-4 text-white" />
                        </div>
                      )}
                      
                      <div className={cn(
                        "max-w-[80%] rounded-2xl px-4 py-3",
                        msg.type === "user" 
                          ? "bg-gradient-to-r from-teal-500 to-blue-500 text-white" 
                          : "bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600"
                      )}>
                        <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                        
                        {msg.metadata?.sources && showSourceExcerpts && (
                          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
                            <p className="text-xs font-medium mb-2">Sources:</p>
                            <div className="space-y-1">
                              {msg.metadata.sources.slice(0, 3).map((source, idx) => (
                                <div key={idx} className="text-xs opacity-75 bg-gray-100 dark:bg-gray-600 rounded px-2 py-1">
                                  <span className="font-medium">{source.filename}</span>
                                  {source.excerpt && (
                                    <span className="ml-1">- {source.excerpt}</span>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        <div className="flex items-center justify-between mt-2">
                          <span className="text-xs opacity-75">
                            {formatDistanceToNow(msg.timestamp, { addSuffix: true })}
                          </span>
                          
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 px-2"
                              onClick={() => copyMessage(msg.content)}
                            >
                              <Copy className="h-3 w-3" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 px-2"
                              onClick={() => toggleReaction(msg.id, 'liked')}
                            >
                              <ThumbsUp className={cn("h-3 w-3", msg.reactions?.liked && "fill-current")} />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 px-2"
                              onClick={() => toggleReaction(msg.id, 'disliked')}
                            >
                              <ThumbsDown className={cn("h-3 w-3", msg.reactions?.disliked && "fill-current")} />
                            </Button>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                  
                  {isLoading && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex gap-4 justify-start"
                    >
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-blue-500 flex items-center justify-center flex-shrink-0">
                        <Bot className="h-4 w-4 text-white" />
                      </div>
                      <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-2xl px-4 py-3">
                        <div className="flex items-center space-x-2">
                          <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                          >
                            <RefreshCw className="h-4 w-4" />
                          </motion.div>
                          <span className="text-sm text-gray-500">Analyzing your data...</span>
                        </div>
                      </div>
                    </motion.div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>
          </ScrollArea>

          {/* Drag Overlay */}
          <AnimatePresence>
            {isDragActive && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 bg-teal-500/10 backdrop-blur-sm flex items-center justify-center z-50"
              >
                <Card className="p-8 text-center bg-white dark:bg-gray-800">
                  <FileUp className="h-16 w-16 mx-auto mb-4 text-teal-500" />
                  <h3 className="text-xl font-semibold mb-2">Drop files to upload</h3>
                  <p className="text-gray-600">Excel, CSV, or PDF files accepted</p>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Input Area */}
        <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-4 py-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <Textarea
                  ref={textareaRef}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask about your financial data..."
                  className="min-h-[44px] max-h-[120px] pr-12 resize-none"
                  rows={1}
                />
                <Button
                  variant="ghost"
                  size="sm"
                  className="absolute right-2 bottom-2 h-8 w-8 p-0"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Paperclip className="h-4 w-4" />
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".xlsx,.xls,.csv,.pdf"
                  onChange={(e) => {
                    const files = Array.from(e.target.files || []);
                    files.forEach(uploadFile);
                  }}
                  className="hidden"
                />
              </div>
              <Button 
                onClick={handleSend} 
                disabled={!message.trim() || isLoading}
                className="h-10 w-10 p-0"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
            
            {/* Selected Files Bar */}
            {selectedFiles.length > 0 && (
              <div className="mt-2 flex items-center gap-2 flex-wrap">
                <span className="text-xs text-gray-500">Context:</span>
                {selectedFiles.slice(0, 3).map(fileId => {
                  const file = availableFiles.find(f => f.id === fileId);
                  return file ? (
                    <Badge key={fileId} variant="secondary" className="text-xs">
                      {file.filename}
                    </Badge>
                  ) : null;
                })}
                {selectedFiles.length > 3 && (
                  <Badge variant="outline" className="text-xs">
                    +{selectedFiles.length - 3} more
                  </Badge>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* File Selector Dialog */}
      <Dialog open={showFileSelector} onOpenChange={setShowFileSelector}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Select Files for Analysis</DialogTitle>
            <DialogDescription>
              Choose files to include in your analysis or report generation
            </DialogDescription>
          </DialogHeader>

          <FileSelectorContent />
        </DialogContent>
      </Dialog>

      {/* Report Generator Dialog */}
      <Dialog open={showReportDialog} onOpenChange={setShowReportDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Generate Financial Report</DialogTitle>
            <DialogDescription>
              Create a comprehensive PDF report from your selected financial documents
            </DialogDescription>
          </DialogHeader>

          <ReportGeneratorContent />
        </DialogContent>
      </Dialog>

      {/* Settings Dialog */}
      <Dialog open={showSettings} onOpenChange={setShowSettings}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Chat Settings</DialogTitle>
            <DialogDescription>
              Customize your chat experience and preferences
            </DialogDescription>
          </DialogHeader>

          <SettingsContent />
        </DialogContent>
      </Dialog>
    </div>
  );

  function FileSelectorContent() {
    return (
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
                  className={cn(
                    "p-4 cursor-pointer transition-all",
                    selectedFiles.includes(file.id)
                      ? "border-teal-500 bg-teal-50 dark:bg-teal-900/20"
                      : "hover:border-gray-300 dark:hover:border-gray-600"
                  )}
                  onClick={() => handleFileSelection(file.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {getFileIcon(file.file_type)}
                      <div>
                        <p className="font-medium">{file.filename}</p>
                        <p className="text-sm text-gray-500">
                          {new Date(file.uploaded_at).toLocaleDateString()} • {formatFileSize(file.file_size)}
                          {file.vector_processed ? (
                            <span className="text-green-600 ml-1">Ready</span>
                          ) : (
                            <span className="text-orange-600 ml-1">Processing</span>
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
                    className={cn(
                      "p-4 cursor-pointer transition-all",
                      selectedFiles.includes(file.id)
                        ? "border-teal-500 bg-teal-50 dark:bg-teal-900/20"
                        : "hover:border-gray-300 dark:hover:border-gray-600"
                    )}
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
    );
  }

  function ReportGeneratorContent() {
    return (
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
          <label className="text-sm font-medium mb-2 block">Selected Files</label>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {selectedFiles.map((fileId) => {
              const file = availableFiles.find((f) => f.id === fileId);
              return file ? (
                <div key={fileId} className="flex items-center gap-2 text-sm p-2 bg-gray-50 rounded">
                  {getFileIcon(file.file_type)}
                  <span>{file.filename}</span>
                  <Badge variant="outline">{formatFileSize(file.file_size)}</Badge>
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
    );
  }

  function SettingsContent() {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <Label htmlFor="auto-process">Auto-process uploaded files</Label>
            <p className="text-sm text-gray-500">
              Automatically process files for vector search after upload
            </p>
          </div>
          <Switch
            id="auto-process"
            checked={autoProcessFiles}
            onCheckedChange={setAutoProcessFiles}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="max-context">Max context files: {maxContextFiles}</Label>
          <Slider
            id="max-context"
            min={1}
            max={10}
            step={1}
            value={[maxContextFiles]}
            onValueChange={([value]) => setMaxContextFiles(value)}
          />
          <p className="text-sm text-gray-500">
            Maximum number of files to include in analysis context
          </p>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label htmlFor="show-sources">Show source excerpts</Label>
            <p className="text-sm text-gray-500">
              Display relevant excerpts from source documents
            </p>
          </div>
          <Switch
            id="show-sources"
            checked={showSourceExcerpts}
            onCheckedChange={setShowSourceExcerpts}
          />
        </div>

        <div className="pt-4 border-t">
          <Button onClick={() => setShowSettings(false)}>
            Save Settings
          </Button>
        </div>
      </div>
    );
  }

  function formatFileSize(bytes: number): string {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }
}