import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface FileUploadResponse {
  file_id: string;
  filename: string;
  size: number;
  content_type: string;
  upload_url?: string;
}

export interface FileInfo {
  id: string;
  filename: string;
  uploaded_at: string;
  file_size: number;
  vector_processed: boolean;
  vector_status?: string;
  processed_at?: string;
  file_type: string;
  content_preview?: string;
  relevance_score?: number;
}

export interface SearchResult {
  id: string;
  filename: string;
  relevance_score: number;
  excerpt?: string;
  metadata?: Record<string, any>;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'bot' | 'system';
  content: string;
  timestamp: string;
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
}

export interface ChatSession {
  id: string;
  title: string;
  lastMessage: string;
  messageCount: number;
  selectedFiles: string[];
}

export interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  sections: string[];
}

export interface ReportStatus {
  report_id: string;
  status: 'generating' | 'completed' | 'error';
  progress?: number;
  download_url?: string;
  error?: string;
}

export interface VectorStats {
  total_files: number;
  total_vectors: number;
  collection_info: any;
  processing_stats: any;
}

class ApiClient {
  private client = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // File Management
  async uploadFile(file: File, onProgress?: (progress: number) => void): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post('/api/financial/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });

    return response.data;
  }

  async getAvailableFiles(limit = 50): Promise<FileInfo[]> {
    const response = await this.client.get(`/api/enhanced/files/available?limit=${limit}`);
    return response.data.files || [];
  }

  async deleteFile(fileId: string): Promise<void> {
    await this.client.delete(`/api/financial/file/${fileId}`);
  }

  async downloadFile(fileId: string): Promise<Blob> {
    const response = await this.client.get(`/api/financial/export/${fileId}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // Vector Processing
  async processFileForVectors(fileId: string): Promise<void> {
    await this.client.post('/api/vector/process', {
      file_id: fileId,
      metadata: { source: 'web_upload' },
    });
  }

  async getVectorStatus(fileId: string): Promise<{
    status: string;
    progress?: number;
    error?: string;
  }> {
    const response = await this.client.get(`/api/vector/status/${fileId}`);
    return response.data;
  }

  async getVectorStats(): Promise<VectorStats> {
    const response = await this.client.get('/api/vector/stats');
    return response.data;
  }

  // Search
  async searchFiles(query: string, options: {
    search_type?: 'semantic' | 'keyword' | 'hybrid';
    limit?: number;
    file_types?: string[];
  } = {}): Promise<SearchResult[]> {
    const response = await this.client.post('/api/enhanced/files/search', {
      query,
      search_type: options.search_type || 'semantic',
      limit: options.limit || 10,
      file_types: options.file_types,
    });
    return response.data.results || [];
  }

  async autoSelectFiles(context: string, options: {
    max_files?: number;
    criteria?: {
      prefer_processed?: boolean;
      prefer_recent?: boolean;
      file_types?: string[];
    };
  } = {}): Promise<FileInfo[]> {
    const response = await this.client.post('/api/enhanced/files/auto-select', {
      context,
      max_files: options.max_files || 5,
      criteria: options.criteria || { prefer_processed: true, prefer_recent: true },
    });
    return response.data.selected_files || [];
  }

  // Chat
  async sendMessage(message: string, options: {
    session_id?: string;
    context?: {
      file_ids?: string[];
      selection_criteria?: any;
      show_sources?: boolean;
    };
  } = {}): Promise<ChatMessage> {
    const response = await this.client.post('/api/enhanced/chat', {
      message,
      session_id: options.session_id,
      context: options.context,
    });
    return response.data;
  }

  async getChatSessions(): Promise<ChatSession[]> {
    const response = await this.client.get('/api/chat/sessions');
    return response.data.sessions || [];
  }

  async getChatHistory(sessionId: string): Promise<ChatMessage[]> {
    const response = await this.client.get(`/api/chat/history/${sessionId}`);
    return response.data.messages || [];
  }

  async deleteChatSession(sessionId: string): Promise<void> {
    await this.client.delete(`/api/chat/sessions/${sessionId}`);
  }

  // Reports
  async getReportTemplates(): Promise<ReportTemplate[]> {
    const response = await this.client.get('/api/enhanced/reports/templates');
    return response.data.templates || [];
  }

  async generateReport(options: {
    file_ids: string[];
    template: string;
    title?: string;
    description?: string;
  }): Promise<ReportStatus> {
    const response = await this.client.post('/api/enhanced/reports/generate', options);
    return response.data;
  }

  async getReportStatus(reportId: string): Promise<ReportStatus> {
    const response = await this.client.get(`/api/financial/report/${reportId}`);
    return response.data;
  }

  async downloadReport(reportId: string): Promise<Blob> {
    const response = await this.client.get(`/api/financial/export/${reportId}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // Analytics
  async getFileAnalytics(fileId: string): Promise<{
    overview: any;
    trends: any;
    insights: any[];
  }> {
    const response = await this.client.get(`/api/analytics/file/${fileId}`);
    return response.data;
  }

  async getPortfolioAnalytics(fileIds: string[]): Promise<{
    combined_overview: any;
    portfolio_trends: any;
    recommendations: any[];
  }> {
    const response = await this.client.post('/api/analytics/portfolio', { file_ids: fileIds });
    return response.data;
  }

  // Error handling
  handleError(error: any): string {
    if (error.response) {
      // Server responded with error
      return error.response.data?.detail || error.response.statusText;
    } else if (error.request) {
      // Request made but no response
      return 'Network error. Please check your connection.';
    } else {
      // Something else happened
      return 'An unexpected error occurred.';
    }
  }
}

export const apiClient = new ApiClient();

// Export individual functions for convenience
export const {
  uploadFile,
  getAvailableFiles,
  deleteFile,
  downloadFile,
  processFileForVectors,
  getVectorStatus,
  getVectorStats,
  searchFiles,
  autoSelectFiles,
  sendMessage,
  getChatSessions,
  getChatHistory,
  deleteChatSession,
  getReportTemplates,
  generateReport,
  getReportStatus,
  downloadReport,
  getFileAnalytics,
  getPortfolioAnalytics,
} = apiClient;