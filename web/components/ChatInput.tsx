
"use client";

import { useState, useRef } from "react";
import { Send, Plus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

interface ChatInputProps {
  onSendMessage: (message: string, file?: File) => void;
  isLoading: boolean;
}

export function ChatInput({ onSendMessage, isLoading }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSendMessage = async () => {
    if (!message.trim() && !file) return;

    if (file) {
      const formData = new FormData();
      formData.append("file", file);

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
        
        // Send message with file context
        onSendMessage(message, file);

      } catch (error) {
        console.error("Error uploading file:", error);
        toast.error(`Failed to upload "${file.name}"`);
      } finally {
        setFile(null);
        setMessage("");
      }
    } else {
      onSendMessage(message);
      setMessage("");
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setFile(event.target.files[0]);
    }
  };

  const handleFileRemove = () => {
    setFile(null);
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
        <div className="flex items-center justify-between p-2 mb-2 bg-gray-100 rounded-lg">
          <span className="text-sm">{file.name}</span>
          <Button variant="ghost" size="icon" onClick={handleFileRemove}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}
      <div className="relative flex items-center">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => fileInputRef.current?.click()}
          className="mr-2"
        >
          <Plus className="h-5 w-5" />
        </Button>
        <Input
          placeholder="Ask a question or upload a file..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          className="flex-1 pr-12"
        />
        <div className="absolute inset-y-0 right-0 flex items-center">
          <Button onClick={handleSendMessage} disabled={isLoading}>
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
    </div>
  );
}
