"use client";

import { useState, useRef, useEffect } from "react";
import {
  Send,
  Paperclip,
  Search,
  Mic,
  FileText,
  Calendar,
  BarChart3,
  Calculator,
  Settings,
  Upload,
  Database,
  ArrowLeft,
  Cloud,
  Check,
  X,
  Trash2,
  Eye,
  Download,
  SendHorizontal,
} from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { useRouter } from "next/navigation";
import { Textarea } from "@/components/ui/textarea";
import { AppSidebar } from "@/components/app-sidebar";
import { SiteHeader } from "@/components/site-header";
import {
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar";
import { ScrollArea } from "@/components/ui/scroll-area";

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  status: "uploading" | "processing" | "completed" | "error";
  progress: number;
  uploadedAt: Date;
  pages?: number;
}

export function ChatInterface() {
  const router = useRouter();
  
  // File upload state
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  
  // Chat state
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<
    Array<{ type: "user" | "bot"; content: string; timestamp: Date }>
  >([]);
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  // File upload handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    processFiles(droppedFiles);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    processFiles(selectedFiles);
  };

  const processFiles = (fileList: File[]) => {
    const newFiles: UploadedFile[] = fileList.map((file) => ({
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      type: file.type,
      status: "uploading",
      progress: 0,
      uploadedAt: new Date(),
      pages: Math.floor(Math.random() * 50) + 1,
    }));

    // Add new files on top first
    setFiles((prev) => [...newFiles, ...prev]);

    // Then simulate upload progress
    newFiles.forEach((newFile) => {
      let progress = 0;

      const interval = setInterval(() => {
        progress += 20;

        setFiles((prev) =>
          prev.map((f) =>
            f.id === newFile.id
              ? {
                ...f,
                progress: progress > 100 ? 100 : progress,
                status: progress >= 100 ? "completed" : "uploading",
              }
              : f
          )
        );

        if (progress >= 100) {
          clearInterval(interval);
        }
      }, 300);
    });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const getFileIcon = (type: string) => {
    if (type.includes("pdf")) return "📄";
    if (type.includes("word") || type.includes("document")) return "📝";
    if (type.includes("text")) return "📄";
    if (type.includes("json")) return "🔧";
    return "📁";
  };

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const filteredFiles = files.filter((file) =>
    file.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const completedFiles = files.filter((f) => f.status === "completed");
  const totalSize = completedFiles.reduce((sum, f) => sum + f.size, 0);

  // Chat handlers
  const handleSend = async () => {
    if (!message.trim() || isLoading) return;

    const userMessage = {
      type: "user" as const,
      content: message,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentMessage = message;
    setMessage("");
    setIsLoading(true);

    try {
      // Call the chat API
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: currentMessage }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      const botResponse = {
        type: "bot" as const,
        content: data.response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botResponse]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorResponse = {
        type: "bot" as const,
        content: "Sorry, I encountered an error while processing your message. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorResponse]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Capabilities
  const capabilities = [
    {
      icon: FileText,
      label: "Generate Financial Report",
      color: "bg-[hsl(var(--chart-1)/0.2)]",
      textColor: "text-[hsl(var(--chart-1))]",
    },
    {
      icon: BarChart3,
      label: "Analyse my Financial Report",
      color: "bg-[hsl(var(--chart-2)/0.2)]",
      textColor: "text-[hsl(var(--chart-2))]",
    },
    {
      icon: Calculator,
      label: "Calculate tax estimates",
      color: "bg-[hsl(var(--chart-3)/0.2)]",
      textColor: "text-[hsl(var(--chart-3))]",
    },
  ];

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);



  return (
    <SidebarProvider>
      <AppSidebar variant="inset" />
      <SidebarInset>
        <SiteHeader />
        <div className="flex flex-1 flex-col">
          <div className="@container/main flex flex-1 flex-col gap-2">
            <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
              {/* Settings Button */}
              <div className="absolute top-4 right-4 z-10">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => router.push("/knowledge-base")}
                  className="p-3 bg-white/80 backdrop-blur-sm hover:bg-white shadow-lg rounded-xl border border-gray-200 transition-all duration-200"
                >
                  <Settings className="h-4 w-4 text-gray-600" />
                </Button>
              </div>

              <div className="flex justify-center gap-16 lg:py-8 md:py-8 md:px-8 sm:py-4 sm:px-4">
                {messages.length === 0 ? (
                  <div className="flex flex-col flex-nowrap items-center h-full gap-16">
                    {/* Main heading */}
                    <div className="text-center">
                      <h1>Turn Numbers into Insight — Instantly.</h1>
                      <div className="max-w-ml mx-auto text-lg">
                        Upload your data, and let AI generate clear, compliant financial reports — faster than ever.
                      </div>
                    </div>

                    {/* Files Management */}
                    <div className="flex flex-row gap-8 justify-items-start text-center w-full">
                      {/* File upload */}
                      <div
                        className={`border-2 border-dashed border-muted p-8 flex flex-col items-center justify-center text-center gap-4 h-full max-w-7xl min-h-80 cursor-pointer pb-8 bg-muted/20 hover:bg-muted/60 hover:border-ring transition-colors transition-all duration-500 w-full ${
                          isDragging ? "bg-primary/5 border-ring" : ""
                        }`}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                      >
                        <Cloud className="h-8 w-8 text-primary" />
                        <p>
                          Drag & drop your file here or click below to upload
                          <br />
                          (pdf, csv, xlsx, txt, doc, docx, json)
                        </p>
                        <Button
                          variant="outline"
                          size="default"
                          onClick={() => document.getElementById("file-input")?.click()}
                        >
                          Upload File
                        </Button>
                        <input
                          id="file-input"
                          type="file"
                          multiple
                          accept=".pdf, .csv, .xlsx, .txt, .doc, .docx, .json"
                          onChange={handleFileSelect}
                          className="hidden"
                        />
                      </div>

                      <div className={`flex flex-col ${files.length > 0 ? "w-full block" : "hidden"}`}>
                        <Card className="p-4 border-1 shadow-sm">
                          <div className="flex items-center justify-items-start mb-4">
                            <h2>Uploaded files</h2>
                          </div>
                          <ScrollArea className="h-60 pr-4">
                            <div className="space-y-3">
                              {filteredFiles.length === 0 ? (
                                <div className="text-center">
                                  <div className="p-4 bg-gray-100 w-16 h-16 mx-auto mb-4">
                                    <FileText className="h-8 w-8 text-gray-400" />
                                  </div>
                                  <p className="text-gray-500">No documents found</p>
                                </div>
                              ) : (
                                filteredFiles.map((file) => (
                                  <div
                                    key={file.id}
                                    className="flex items-center justify-center min-w-100 gap-4 p-4 bg-muted/20 hover:bg-muted/60 transition-colors"
                                  >
                                    <div className="flex-shrink-0">
                                      <div className="text-2xl">{getFileIcon(file.type)}</div>
                                    </div>

                                    <div className="flex-1 min-w-0">
                                      <div className="flex items-center gap-2 mb-1 w-full">
                                        <div className="text-left max-w-60 truncate">
                                          {file.name}
                                        </div>
                                        {file.status === "completed" && (
                                          <div className="p-1 bg-green-100 rounded-full">
                                            <Check className="h-2 w-2 text-green-600" />
                                          </div>
                                        )}
                                      </div>

                                      <p className="flex items-center gap-4 whitespace-nowrap">
                                        <span>{formatFileSize(file.size)}</span>
                                        {file.pages && <span>{file.pages} pages</span>}
                                        <span>Uploaded {formatDate(file.uploadedAt)}</span>
                                      </p>

                                      {file.status === "uploading" && (
                                        <div className="mt-2">
                                          <Progress value={file.progress} className="h-1" />
                                          <p className="mt-1">{file.progress}% uploaded</p>
                                        </div>
                                      )}
                                    </div>

                                    <div className="flex items-center gap-2">
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => removeFile(file.id)}
                                        className="text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg p-2"
                                      >
                                        <Trash2 className="h-4 w-4" />
                                      </Button>
                                    </div>
                                  </div>
                                ))
                              )}
                            </div>
                          </ScrollArea>
                        </Card>
                      </div>
                    </div>

                    {/* Chat Input */}
                    <div className="flex flex-col gap-4 w-full max-w-7xl">
                      <div className="relative group">
                        <Textarea
                          rows={4}
                          value={message}
                          onChange={(e) => setMessage(e.target.value)}
                          onKeyDown={handleKeyPress}
                          placeholder="Generate a new report from your data, upload your own, or ask me about any financial matters..."
                          className="w-full max-h-24 pr-12 text-base shadow-md transition-all duration-300 resize-none"
                        />
                        <Button
                          onClick={handleSend}
                          disabled={isLoading}
                          size="icon"
                          variant="ghost"
                          className="absolute top-1/2 right-3 -translate-y-1/2"
                        >
                          <SendHorizontal size={24} strokeWidth={2} />
                        </Button>
                      </div>

                      {/* Capabilities grid */}
                      <div className={`flex gap-4 justify-center items-center ${files.length > 0 ? "w-full max-w-7xl" : "hidden"} transition-opacity`}>
                        {capabilities.map((capability, index) => {
                          const Icon = capability.icon;
                          return (
                            <Button
                              variant="secondary"
                              key={index}
                              className="group relative transition-opacity"
                              onClick={() => setMessage(capability.label)}
                            >
                              <div className="relative flex items-center gap-4">
                                <Icon className={`h-4 w-4 ${capability.textColor}`} />
                                <div className="transition-colors duration-500">
                                  {capability.label}
                                </div>
                              </div>
                            </Button>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col h-screen overflow-hidden">
                    {/* Scrollable chat area */}
                    <ScrollArea className="flex-1 overflow-y-auto">
                      <div className="space-y-6 px-4 py-8">
                        {messages.map((msg, index) => (
                          <div
                            key={index}
                            className={`flex ${msg.type === "user" ? "justify-end" : "justify-start"}`}
                          >
                            <div className="max-w-[75%] p-4 rounded-md bg-muted text-foreground shadow">
                              <p>{msg.content}</p>
                              <p className="text-xs mt-2 text-muted-foreground">
                                {msg.timestamp.toLocaleTimeString()}
                              </p>
                            </div>
                          </div>
                        ))}
                        {isLoading && (
                          <div className="flex justify-start">
                            <div className="max-w-[75%] p-4 rounded-md bg-muted text-foreground shadow">
                              <div className="flex items-center space-x-2">
                                <div className="flex space-x-1">
                                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                                </div>
                                <span className="text-sm text-gray-500">AI is thinking...</span>
                              </div>
                            </div>
                          </div>
                        )}
                        <div ref={bottomRef} />
                      </div>
                    </ScrollArea>

                    {/* Fixed input at bottom */}
                    <div className="border-t border-border bg-background px-4 py-4">
                      <div className="max-w-4xl mx-auto">
                        <div className="relative group">
                          <Textarea
                            rows={4}
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            onKeyDown={handleKeyPress}
                            placeholder="Add a follow up..."
                            className="w-full pr-12 max-h-24 resize-none overflow-y-auto shadow"
                          />
                          <Button
                            onClick={handleSend}
                            disabled={isLoading}
                            size="icon"
                            variant="ghost"
                            className="absolute top-1/2 right-3 -translate-y-1/2"
                          >
                            <SendHorizontal size={24} />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
