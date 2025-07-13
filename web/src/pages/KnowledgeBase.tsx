import { useState } from "react";
import {
  Upload,
  FileText,
  Database,
  Settings,
  ArrowLeft,
  Cloud,
  Check,
  X,
  Trash2,
  Eye,
  Download,
  Search,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { useNavigate } from "react-router-dom";

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

export default function KnowledgeBase() {
  const navigate = useNavigate();
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<UploadedFile[]>([
    {
      id: "1",
      name: "Financial Report Q3 2024.pdf",
      size: 2048000,
      type: "application/pdf",
      status: "completed",
      progress: 100,
      uploadedAt: new Date("2024-01-15"),
      pages: 24,
    },
    {
      id: "2",
      name: "Tax Guidelines 2024.docx",
      size: 1024000,
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      status: "completed",
      progress: 100,
      uploadedAt: new Date("2024-01-10"),
      pages: 12,
    },
    {
      id: "3",
      name: "Company Policies.txt",
      size: 51200,
      type: "text/plain",
      status: "completed",
      progress: 100,
      uploadedAt: new Date("2024-01-05"),
    },
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

    setFiles((prev) => [...newFiles, ...prev]);// add new files on top

    // Simulate upload progress
    newFiles.forEach((file) => {
      const interval = setInterval(() => {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === file.id && f.progress < 100
              ? { ...f, progress: f.progress + 20 }
              : f
          )
        );
      }, 300);

      setTimeout(() => {
        clearInterval(interval);
        setFiles((prev) =>
          prev.map((f) =>
            f.id === file.id ? { ...f, status: "completed", progress: 100 } : f
          )
        );
      }, 1500);
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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate("/")}
                className="hover:bg-gray-100 rounded-xl"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Chat
              </Button>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-200 rounded-xl">
                  <Settings className="h-5 w-5 text-purple-700" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">
                    Knowledge Base
                  </h1>
                  <p className="text-gray-600 text-sm">
                    {completedFiles.length} documents •{" "}
                    {formatFileSize(totalSize)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Upload Section */}
          <div className="lg:col-span-1">
            <Card className="p-6 border-0 shadow-sm rounded-2xl bg-white">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Upload Documents
              </h2>

              <div
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 ${
                  isDragging
                    ? "border-teal-400 bg-teal-50"
                    : "border-gray-300 hover:border-teal-300 hover:bg-teal-50/50"
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <div className="mb-4">
                  <div className="p-3 bg-teal-200 rounded-xl w-12 h-12 mx-auto">
                    <Cloud className="h-6 w-6 text-teal-700" />
                  </div>
                </div>

                <h3 className="text-sm font-medium text-gray-900 mb-2">
                  Drop files here
                </h3>
                <p className="text-xs text-gray-500 mb-4">
                  PDF, DOC, TXT, JSON up to 10MB
                </p>

                <Button
                  size="sm"
                  className="bg-teal-600 hover:bg-teal-700 text-white rounded-xl"
                  onClick={() => document.getElementById("file-input")?.click()}
                >
                  <Upload className="h-4 w-4 mr-2" />
                  Browse Files
                </Button>
                <input
                  id="file-input"
                  type="file"
                  multiple
                  accept=".pdf,.txt,.doc,.docx,.json"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>
            </Card>
          </div>

          {/* File Management */}
          <div className="lg:col-span-2">
            <Card className="p-6 border-0 shadow-sm rounded-2xl bg-white">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900">
                  Manage Knowledge Base
                </h2>
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <Search className="h-4 w-4 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
                    <Input
                      placeholder="Search documents..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 h-9 w-64 border-gray-200 rounded-xl bg-gray-50 focus:border-teal-300"
                    />
                  </div>
                </div>
              </div>

              {/* <div className="space-y-3">
                {filteredFiles.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="p-4 bg-gray-100 rounded-xl w-16 h-16 mx-auto mb-4">
                      <FileText className="h-8 w-8 text-gray-400" />
                    </div>
                    <p className="text-gray-500">No documents found</p>
                  </div>
                ) : (
                  filteredFiles.map((file) => (
                    <div
                      key={file.id}
                      className="flex items-center gap-4 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex-shrink-0">
                        <div className="text-2xl">{getFileIcon(file.type)}</div>
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-medium text-gray-900 truncate">
                            {file.name}
                          </h3>
                          {file.status === "completed" && (
                            <div className="p-1 bg-green-100 rounded-full">
                              <Check className="h-3 w-3 text-green-600" />
                            </div>
                          )}
                        </div>

                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          <span>{formatFileSize(file.size)}</span>
                          {file.pages && <span>{file.pages} pages</span>}
                          <span>Uploaded {formatDate(file.uploadedAt)}</span>
                        </div>

                        {file.status === "uploading" && (
                          <div className="mt-2">
                            <Progress value={file.progress} className="h-1" />
                            <p className="text-xs text-gray-500 mt-1">
                              {file.progress}% uploaded
                            </p>
                          </div>
                        )}
                      </div>

                      <div className="flex items-center gap-2">
                        {file.status === "completed" && (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-gray-500 hover:text-teal-600 hover:bg-teal-50 rounded-lg p-2"
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
                        )}
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
              </div> */}
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

