import { useState } from "react";
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
  // SendHorizontal ,
} from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { SendHorizonal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { useNavigate } from "react-router-dom";
import { Textarea } from "./ui/textarea";
// ShadCN Dashboard Template  
import { AppSidebar } from "@/components/app-sidebar"
import { ChartAreaInteractive } from "@/components/chart-area-interactive"
import { DataTable } from "@/components/data-table"
import { SectionCards } from "@/components/section-cards"
import { SiteHeader } from "@/components/site-header"
import {
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useRef, useEffect } from "react";



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
  const navigate = useNavigate();
  // File upload
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<UploadedFile[]>([
    // {
    //   id: "1",
    //   name: "Financial Report Q3 2024.pdf",
    //   size: 2048000,
    //   type: "application/pdf",
    //   status: "completed",
    //   progress: 100,
    //   uploadedAt: new Date("2024-01-15"),
    //   pages: 24,
    // },
    // {
    //   id: "2",
    //   name: "Tax Guidelines 2024.docx",
    //   size: 1024000,
    //   type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    //   status: "completed",
    //   progress: 100,
    //   uploadedAt: new Date("2024-01-10"),
    //   pages: 12,
    // },
    // {
    //   id: "3",
    //   name: "Company Policies.txt",
    //   size: 51200,
    //   type: "text/plain",
    //   status: "completed",
    //   progress: 100,
    //   uploadedAt: new Date("2024-01-05"),
    // },
  ]);
  const [searchTerm, setSearchTerm] = useState("");

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

  // Others

  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<
    Array<{ type: "user" | "bot"; content: string; timestamp: Date }>
  >([]);

  const handleSend = () => {
    if (!message.trim()) return;

    const newMessage = {
      type: "user" as const,
      content: message,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, newMessage]);
    setMessage("");

    // Simulate bot response
    setTimeout(() => {
      const botResponse = {
        type: "bot" as const,
        content:
          "I'm your AI accounting assistant. I can help you with financial calculations, tax questions, bookkeeping guidance, and more. What would you like to know?",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botResponse]);
    }, 1000);

  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const capabilities = [
    {
      icon: FileText,
      label: "Generate Financial Report ",
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
    // {
    //   icon: Calendar,
    //   label: "Plan quarterly reviews",
    //   color: "bg-orange-200",
    //   textColor: "text-orange-700",
    // },
  ];

  const bottomRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])



  return (
    <SidebarProvider>
      <AppSidebar variant="inset" />
      <SidebarInset  >
        <SiteHeader />
        {/* Settings Button */}
        {/* <div className="absolute top-4 right-4 z-10">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate("/knowledge-base")}
            className="p-3 bg-white/80 backdrop-blur-sm hover:bg-white shadow-lg rounded-xl border border-gray-200 transition-all duration-200"
          >
            <Settings className="h-4 w-4 text-gray-600" />
          </Button>
        </div> */}
        <div className="flex flex-1 flex-col">
          <div className="@container/main flex flex-1 flex-col gap-2">
            <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">

              {/*----------------------------------------------- Title ------------------------------------------------ */}
              <div className="flex justify-center gap-16 lg:py-8 md:py-8 md:px-8 sm:py-4 sm:px-4">
                {messages.length === 0 ? (
                  <div className="flex flex-col flex-nowrap items-center  h-full gap-16">
                    {/* Main heading */}
                    <div className="text-center">
                      {/* <div className="p-4 rounded-3xl w-20 h-20 mx-auto shadow-lg">
                          <Calculator className="h-12 w-12 text-primary" />
                          </div> */}
                      <h1>
                        Turn Numbers into Insight — Instantly.
                      </h1>
                      <div className="max-w-ml mx-auto text-lg">
                        Upload your data, and let AI generate clear, compliant financial reports — faster than ever.
                      </div>
                    </div>


                    {/* ------------------------------------------------ Files Management ------------------------------------------------ */}
                    <div className="flex flex-row gap-8  justify-items-start text-center w-full ">
                      {/* File upload */}
                      <div
                        className={`border-2 border-dashed border-muted
                                    p-8 flex flex-col items-center justify-center text-center gap-4
                                    h-full max-w-7xl min-h-80 cursor-pointer pb-8
                                    bg-muted/20 hover:bg-muted/60 hover:border-ring transition-colors
                                    transition-all duration-500
                                    ${files.length > 0 ? "w-full" : "w-full"} 
                                    ${isDragging
                            ? "bg-primary/5 border-ring" : ""
                          }
                                  `}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                      >
                        <Cloud className="h-8 w-8 text-primary" />
                        <p>
                          Drag & drop your file here or click below to upload
                          <br />
                          (pdf, csv, xlsx, txt, doc, docx, json)</p>
                        <Button
                          variant="outline" size="default"
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
                            <h2 className="">
                              Uploaded files
                            </h2>
                            {/* <div className="flex justify-end items-center gap-3">
                            <div className="relative">
                              <Search className="h-4 w-4 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
                              <Input
                                placeholder="Search documents..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="pl-10 h-9 w-64 border-gray-200 rounded-xl bg-gray-50 focus:border-teal-300"
                              />
                            </div>
                          </div> */}
                          </div>
                          <ScrollArea className="h-60 pr-4">
                            <div className="space-y-3">
                              {filteredFiles.length === 0 ? (
                                <div className="text-center ">
                                  <div className="p-4 bg-gray-100 w-16 h-16 mx-auto mb-4">
                                    <FileText className="h-8 w-8 text-gray-400" />
                                  </div>
                                  <p className="text-gray-500">No documents found</p>
                                </div>
                              ) : (
                                filteredFiles.map((file) => (
                                  <div
                                    key={file.id}
                                    className="flex items-center justify-center min-w-100 gap-4 p-4 bg-muted/20  hover:hover:bg-muted/60 transition-colors"
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

                                      <p className="flex items-center gap-4 whitespace-nowrap ">
                                        <span>{formatFileSize(file.size)}</span>
                                        {file.pages && <span>{file.pages} pages</span>}
                                        <span>Uploaded {formatDate(file.uploadedAt)}</span>
                                      </p>

                                      {file.status === "uploading" && (
                                        <div className="mt-2">
                                          <Progress value={file.progress} className="h-1" />
                                          <p className="mt-1">
                                            {file.progress}% uploaded
                                          </p>
                                        </div>
                                      )}
                                    </div>

                                    <div className="flex items-center gap-2">
                                      {/* NOTE: May click on filename instead to simplify elements

                                  {file.status === "completed" && (
                                    <>
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        className="text-gray-500 hover:text-teal-600 hover:bg-primary/60 rounded-lg p-2"
                                      >
                                        <Eye className="h-4 w-4" />
                                      </Button>
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        className="text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg p-2"
                                      >
                                        <Download className="h-4 w-4" />
                                      </Button>
                                    </>
                                  )} */}
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



                    {/* ------------------------------------------------ Chat ------------------------------------------------*/}
                    <div className="flex flex-col gap-4 w-full max-w-7xl">
                      <div className="relative group">
                        <Textarea
                          rows={4}
                          value={message}
                          onChange={(e) => setMessage(e.target.value)}
                          onKeyPress={handleKeyPress}
                          placeholder="Generate a new report from your data, upload your own, or ask me about any financial matters..."
                          // className="w-full max-h-24  pr-12 text-lg shadow-md transition-all duration-300 placeholder:text-gray-400 resize-none"
                          className="w-full max-h-24 pr-12 text-base shadow-md transition-all duration-300  resize-none "
                        />
                        {/* {message.trim() && ( */}
                        <Button
                          onClick={handleSend}
                          size="icon"
                          variant="ghost"
                          className="absolute top-1/2 right-3 -translate-y-1/2"
                        >
                          <SendHorizonal size={48} strokeWidth={3} />
                        </Button>
                        {/* )} */}
                      </div>



                      {/* Action buttons */}
                      {/* <div className="flex items-center justify-center gap-3 mt-6">
                        <Button
                          variant="ghost"
                          className="h-10 px-4 text-sm text-gray-600 hover:text-teal-700 hover:bg-teal-50 rounded-xl transition-all duration-200"
                        >
                          <Paperclip className="h-4 w-4 mr-2" />
                          Attach
                        </Button>
                        <Button
                          variant="ghost"
                          className="h-10 px-4 text-sm text-gray-600 hover:text-teal-700 hover:bg-teal-50 rounded-xl transition-all duration-200"
                        >
                          <Search className="h-4 w-4 mr-2" />
                          Search
                        </Button>
                        <Button
                          variant="ghost"
                          className="h-10 px-4 text-sm text-gray-600 hover:text-teal-700 hover:bg-teal-50 rounded-xl transition-all duration-200"
                        >
                          <Mic className="h-4 w-4 mr-2" />
                          Voice
                        </Button>
                        </div> */}

                      {/* {/* Capabilities grid */}
                      {/* <div className={`flex flex-col ${files.length > 0 ? "w-1/2 block" : "hidden"}`}> */}
                      <div className={`flex gap-4 justify-center items-center ${files.length > 0 ? "w-full max-w-7xl " : "hidden"} transition-opacity`}>
                        {capabilities.map((capability, index) => {
                          const Icon = capability.icon;
                          return (
                            <Button
                              variant="secondary"
                              key={index}
                              className="group relative tansition-opacity"
                              // border-0 bg-white shadow-lg hover:shadow-xl transition-all duration-300 rounded-2xl overflow-hidden
                              onClick={() => setMessage(capability.label)}
                            >
                              {/* <div
                                  className={`absolute inset-0 ${capability.color} opacity-0 group-hover:opacity-10 transition-opacity duration-300`}
                                /> */}
                              <div className="relative flex items-center gap-4">
                                <div
                                  className={``} // p-3 rounded-xl ${capability.color} shadow-lg
                                >
                                  <Icon className={`h-4 w-4 ${capability.textColor}`} />
                                </div>
                                <div className="transition-colors duration-500">
                                  {/* group-hover:text-gray-900 transition-colors duration-200   */}
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
                  <div className="flex flex-col h-screen  overflow-hidden">
                    {/* Scrollable chat area */}
                    <ScrollArea className="flex-1 overflow-y-auto">
                      <div className="space-y-6 px-4 py-8">
                        {messages.map((msg, index) => (
                          <div key={index} className={`flex ${msg.type === "user" ? "justify-end" : "justify-start"}`}>
                            <div className="max-w-[75%] p-4 rounded-md bg-muted text-foreground shadow">
                              <p>{msg.content}</p>
                              <p className="text-xs mt-2 text-muted-foreground">
                                {msg.timestamp.toLocaleTimeString()}
                              </p>
                            </div>
                          </div>
                        ))}
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
                            size="icon"
                            variant="ghost"
                            className="absolute top-1/2 right-3 -translate-y-1/2"
                          >
                            <SendHorizonal size={24} />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>



                )}
              </div>

              {/* Input Area - for when there are messages */}
              {/* {messages.length > 0 && (  */}
              {/* // <div className="backdrop-blur-sm">
                //   <div className="w-full max-w-4xl mx-auto">
                //     <div className="flex flex-col gap-4 relative group items-center justify-top">
                //         <Textarea
                //           value={message}
                //           rows={4}
                //           onChange={(e) => setMessage(e.target.value)}
                //           onKeyPress={handleKeyPress}
                //           placeholder="Ask a follow-up question..."
                //           className="w-full max-h-24 pr-12 shadow-md transition-all duration-300  resize-none 
                //           overflow-y-auto scrollbar-thin scrollbar-thumb-muted-foreground scrollbar-track-muted"
                //           //h-14 text-base border-2 border-gray-200  bg-white focus:border-teal-300 focus:shadow-lg transition-all duration-300 pl-6 pr-4
                //         />
                //         <Button
                //           onClick={handleSend}
                //           size="icon"
                //           variant="ghost"
                //           className="absolute top-1/2 right-3 -translate-y-1/2"
                //         >
                //           <SendHorizonal size={48} strokeWidth={3} />
                //         </Button>                    
                //     </div>
                //   </div>
                // </div>
              // ) */}

            </div>
          </div>
        </div>

      </SidebarInset>
    </SidebarProvider>
  );
}


