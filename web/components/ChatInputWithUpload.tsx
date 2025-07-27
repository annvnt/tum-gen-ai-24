"use client";

import { useState, useRef } from "react";
import { Send, Plus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

interface ChatInputWithUploadProps {
  onSendMessage: (message: string, fileId?: string, fileName?: string) => void;
  isLoading: boolean;
}

export function ChatInputWithUpload({ onSendMessage, isLoading }: ChatInputWithUploadProps) {
  const [message, setMessage] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSendMessage = async () => {
    if (!message.trim() && !file) return;

    let fileId: string | undefined = undefined;
    let fileName: string | undefined = undefined;

    if (file) {
      const formData = new FormData();
      formData.append("file", file);

      try {
        const response = await fetch("/api/financial/upload", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Upload failed");
        }

        const data = await response.json();
        fileId = data.file_id;
        fileName = data.filename;
        toast.success(`File "${fileName}" uploaded successfully.`);
        
        // Pass the message along with the new fileId
        onSendMessage(message, fileId, fileName);

      } catch (error) {
        console.error("Error uploading file:", error);
        toast.error(`Failed to upload "${file.name}": ${(error as Error).message}`);
        // Don't send message if file upload fails
        return;
      } finally {
        // Clear file and message after attempting to send
        setFile(null);
        setMessage("");
      }
    } else {
      // Send message without a file
      onSendMessage(message);
      setMessage("");
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      const selectedFile = event.target.files[0];
      // Optional: Add file size/type validation here if needed
      setFile(selectedFile);
    }
  };

  const handleFileRemove = () => {
    setFile(null);
    if(fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="p-4 bg-white border-t border-gray-200">
      {file && (
        <div className="flex items-center justify-between p-2 mb-2 bg-gray-100 rounded-lg text-sm">
          <span>{file.name}</span>
          <Button variant="ghost" size="icon" onClick={handleFileRemove} className="h-6 w-6">
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}
      <div className="relative flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading}
        >
          <Plus className="h-5 w-5" />
        </Button>
        <Input
          placeholder="Ask a question or upload a file..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
          className="flex-1"
        />
        <Button onClick={handleSendMessage} disabled={isLoading || (!message.trim() && !file)}>
          <Send className="h-5 w-5" />
        </Button>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
          accept=".xlsx,.xls,.csv,.pdf,.docx,.txt"
        />
      </div>
    </div>
  );
}
