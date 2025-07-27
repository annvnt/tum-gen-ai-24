"use client";

import { useState, useEffect } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload,
  Search,
  FileText,
  Database,
  Clock,
  CheckCircle,
  XCircle,
  RefreshCw,
  Download,
  Trash2,
  FileSpreadsheet,
  FileQuestion,
  Eye,
  EyeOff,
  Filter,
  Calendar,
  TrendingUp,
  BarChart3,
  Sparkles,
  Plus,
  FileUp,
  Settings,
  Share2,
  Archive,
  Star,
  MoreVertical,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { formatDistanceToNow, format } from "date-fns";

interface KnowledgeFile {
  id: string;
  filename: string;
  uploaded_at: string;
  file_size: number;
  vector_processed: boolean;
  vector_status?: string;
  processed_at?: string;
  file_type: string;
  content_preview?: string;
}

interface VectorStats {
  total_files: number;
  total_vectors: number;
  collection_info: any;
  processing_stats: any;
}

export function KnowledgeBaseManager() {
  const [files, setFiles] = useState<KnowledgeFile[]>([]);
  const [stats, setStats] = useState<VectorStats | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<KnowledgeFile[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingFiles, setProcessingFiles] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadKnowledgeBase();
    loadStats();
  }, []);

  const loadKnowledgeBase = async () => {
    setIsLoading(true);
    try {
      const response = await fetch("/api/enhanced/files/available?limit=100");
      const data = await response.json();
      setFiles(data.files || []);
    } catch (error) {
      console.error("Error loading knowledge base:", error);
      toast.error("Failed to load knowledge base");
    } finally {
      setIsLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch("/api/vector/stats");
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error("Error loading stats:", error);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = event.target.files;
    if (!fileList) return;

    const files = Array.from(fileList);
    for (const file of files) {
      await uploadFile(file);
    }
  };

  const uploadFile = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    setUploadProgress(0);
    try {
      const response = await fetch("/api/financial/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const data = await response.json();
      toast.success(`File "${file.name}" uploaded successfully`);
      
      // Start vector processing
      await processFileForVectors(data.file_id);
      
      loadKnowledgeBase();
      loadStats();
    } catch (error) {
      console.error("Error uploading file:", error);
      toast.error(`Failed to upload "${file.name}"`);
    } finally {
      setUploadProgress(0);
    }
  };

  const processFileForVectors = async (fileId: string) => {
    setProcessingFiles((prev) => new Set(prev).add(fileId));
    
    try {
      const response = await fetch("/api/vector/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_id: fileId,
          metadata: { source: "knowledge_base" },
        }),
      });

      if (response.ok) {
        toast.success("Vector processing started");
        
        // Poll for processing status
        const checkStatus = async () => {
          try {
            const statusResponse = await fetch(`/api/vector/status/${fileId}`);
            const statusData = await statusResponse.json();
            
            if (statusData.status === "completed") {
              toast.success("File processed and ready for search");
              loadKnowledgeBase();
              setProcessingFiles((prev) => {
                const newSet = new Set(prev);
                newSet.delete(fileId);
                return newSet;
              });
            } else if (statusData.status === "processing") {
              setTimeout(checkStatus, 2000);
            } else {
              toast.error("Vector processing failed");
              setProcessingFiles((prev) => {
                const newSet = new Set(prev);
                newSet.delete(fileId);
                return newSet;
              });
            }
          } catch (error) {
            console.error("Error checking status:", error);
          }
        };

        setTimeout(checkStatus, 1000);
      }
    } catch (error) {
      console.error("Error processing file:", error);
      toast.error("Failed to start vector processing");
      setProcessingFiles((prev) => {
        const newSet = new Set(prev);
        newSet.delete(fileId);
        return newSet;
      });
    }
  };

  const searchKnowledgeBase = async (query: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    try {
      const response = await fetch("/api/enhanced/files/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          search_type: "semantic",
          limit: 20,
        }),
      });
      const data = await response.json();
      setSearchResults(data.results || []);
    } catch (error) {
      console.error("Error searching knowledge base:", error);
      toast.error("Search failed");
    }
  };

  const deleteFile = async (fileId: string) => {
    try {
      const response = await fetch(`/api/financial/file/${fileId}`, {
        method: "DELETE",
      });

      if (response.ok) {
        toast.success("File deleted successfully");
        loadKnowledgeBase();
        loadStats();
      } else {
        toast.error("Failed to delete file");
      }
    } catch (error) {
      console.error("Error deleting file:", error);
      toast.error("Failed to delete file");
    }
  };

  const downloadFile = async (fileId: string) => {
    try {
      const file = files.find((f) => f.id === fileId);
      if (!file) return;

      // For Excel files, use the existing export endpoint
      if (file.filename.endsWith('.xlsx') || file.filename.endsWith('.xls')) {
        // This would need to be adapted based on your backend
        const response = await fetch(`/api/financial/export/${fileId}`);
        if (response.ok) {
          const blob = await response.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `report_${file.filename}`;
          a.click();
          URL.revokeObjectURL(url);
        }
      }
    } catch (error) {
      console.error("Error downloading file:", error);
      toast.error("Failed to download file");
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const getStatusIcon = (file: KnowledgeFile) => {
    if (processingFiles.has(file.id)) {
      return <RefreshCw className="h-4 w-4 animate-spin text-blue-500" />;
    }
    if (file.vector_processed) {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    }
    return <Clock className="h-4 w-4 text-gray-400" />;
  };

  const getStatusBadge = (file: KnowledgeFile) => {
    if (processingFiles.has(file.id)) {
      return <Badge variant="outline" className="bg-blue-50 text-blue-700">Processing</Badge>;
    }
    if (file.vector_processed) {
      return <Badge variant="outline" className="bg-green-50 text-green-700">Ready</Badge>;
    }
    return <Badge variant="outline" className="bg-gray-50 text-gray-700">Pending</Badge>;
  };

  const FileCard = ({ file }: { file: KnowledgeFile }) => (
    <Card className="p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1">
          <div className="p-2 bg-gray-100 rounded-lg">
            <FileText className="h-5 w-5 text-gray-600" />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-medium truncate">{file.filename}</h4>
            <p className="text-sm text-gray-500">
              {formatFileSize(file.file_size)} • {new Date(file.uploaded_at).toLocaleDateString()}
            </p>
            <div className="flex items-center gap-2 mt-1">
              {getStatusIcon(file)}
              {getStatusBadge(file)}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => downloadFile(file.id)}
            disabled={!file.vector_processed}
          >
            <Download className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => deleteFile(file.id)}
            className="text-red-600 hover:text-red-700"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </Card>
  );

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Knowledge Base</h1>
          <p className="text-gray-600">Manage and search your financial documents</p>
        </div>
        <Button
          onClick={() => document.getElementById("file-upload")?.click()}
          className="gap-2"
        >
          <Upload className="h-4 w-4" />
          Upload Files
        </Button>
        <input
          id="file-upload"
          type="file"
          multiple
          accept=".xlsx,.xls,.csv"
          onChange={handleFileUpload}
          className="hidden"
        />
      </div>

      {/* Stats */}
      {stats && (
        <Card className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <div className="flex items-center gap-2">
                <Database className="h-5 w-5 text-blue-500" />
                <span className="text-2xl font-bold">{stats.total_files}</span>
              </div>
              <p className="text-sm text-gray-600">Total Files</p>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <Search className="h-5 w-5 text-green-500" />
                <span className="text-2xl font-bold">{stats.total_vectors}</span>
              </div>
              <p className="text-sm text-gray-600">Total Vectors</p>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <span className="text-2xl font-bold">
                  {files.filter((f) => f.vector_processed).length}
                </span>
              </div>
              <p className="text-sm text-gray-600">Processed</p>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-orange-500" />
                <span className="text-2xl font-bold">
                  {files.filter((f) => !f.vector_processed).length}
                </span>
              </div>
              <p className="text-sm text-gray-600">Pending</p>
            </div>
          </div>
        </Card>
      )}

      <Tabs defaultValue="files" className="w-full">
        <TabsList>
          <TabsTrigger value="files">All Files</TabsTrigger>
          <TabsTrigger value="search">Search</TabsTrigger>
          <TabsTrigger value="upload">Upload</TabsTrigger>
        </TabsList>

        <TabsContent value="files" className="space-y-4">
          <div className="flex items-center gap-4">
            <Input
              placeholder="Search files..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                if (e.target.value.trim()) {
                  searchKnowledgeBase(e.target.value);
                }
              }}
              className="max-w-md"
            />
            <Button
              variant="outline"
              onClick={loadKnowledgeBase}
              disabled={isLoading}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>

          <ScrollArea className="h-[500px]">
            <div className="space-y-3">
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
                </div>
              ) : files.length > 0 ? (
                files.map((file) => <FileCard key={file.id} file={file} />)
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No files uploaded yet. Start by uploading some documents!
                </div>
              )}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="search" className="space-y-4">
          <div className="flex items-center gap-4">
            <Input
              placeholder="Search knowledge base..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                searchKnowledgeBase(e.target.value);
              }}
              className="max-w-md"
            />
          </div>

          <ScrollArea className="h-[500px]">
            <div className="space-y-3">
              {searchResults.length > 0 ? (
                searchResults.map((file) => <FileCard key={file.id} file={file} />)
              ) : (
                <div className="text-center py-8 text-gray-500">
                  {searchQuery ? "No results found" : "Start typing to search..."}
                </div>
              )}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="upload" className="space-y-4">
          <Card className="p-8">
            <div className="text-center space-y-4"
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                const files = Array.from(e.dataTransfer.files);
                files.forEach(uploadFile);
              }}
            >
              <div className="p-6 border-2 border-dashed border-gray-300 rounded-lg hover:border-gray-400 transition-colors">
                <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <h3 className="text-lg font-medium mb-2">Upload Financial Documents</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Drag and drop Excel files here, or click to browse
                </p>
                <Button
                  onClick={() => document.getElementById("file-upload")?.click()}
                  variant="outline"
                >
                  Choose Files
                </Button>
                <input
                  id="file-upload"
                  type="file"
                  multiple
                  accept=".xlsx,.xls,.csv"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </div>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}