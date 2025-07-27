"use client";

import { useState, useRef } from "react";
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
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

// Adjusted Message type
interface Message {
    type: "user" | "bot";
    content: string;
    timestamp: Date;
    file?: { name: string };
}

export function ChatInterface() {
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSend = async () => {
    const userMessageText = message;
    const userFile = file;

    if (!userMessageText.trim() && !userFile) return;

    setIsLoading(true);

    // Add user message to UI immediately
    const userMessageUI: Message = {
      type: "user",
      content: userMessageText,
      timestamp: new Date(),
      file: userFile ? { name: userFile.name } : undefined,
    };
    setMessages((prev) => [...prev, userMessageUI]);

    // Reset input fields
    setMessage("");
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }

    try {
      let botResponseContent = "";

      // If there's a file, upload and analyze it first.
      if (userFile) {
        const formData = new FormData();
        formData.append("file", userFile);

        // Use the financial upload endpoint
        const uploadResponse = await fetch("/api/financial/upload", {
          method: "POST",
          body: formData,
        });

        if (!uploadResponse.ok) {
          const errorData = await uploadResponse.json();
          throw new Error(errorData.error || "File analysis failed");
        }

        const result = await uploadResponse.json();
        if (result.success && result.report) {
          toast.success(`File "${userFile.name}" analyzed successfully.`);
          botResponseContent = result.report.summary; // Use the summary as the bot's response
        } else {
          throw new Error(result.error || "Analysis did not return a report.");
        }
      }

      // If there was also a text message, send it to the chat agent for a follow-up response.
      if (userMessageText.trim()) {
        const chatResponse = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: userMessageText }),
        });

        if (!chatResponse.ok) {
          throw new Error("Chat API request failed.");
        }

        const chatData = await chatResponse.json();
        
        // Combine the analysis summary with the chat response.
        if (botResponseContent) {
          botResponseContent += `\n\n**Regarding your message:**\n${chatData.response}`;
        } else {
          botResponseContent = chatData.response;
        }
      }

      if (!botResponseContent) {
        // This case should not happen if the function is exited at the start
        // but as a fallback.
        botResponseContent = "I'm not sure how to respond to that. Please try again.";
      }

      const botMessage: Message = {
        type: "bot",
        content: botResponseContent,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMessage]);

    } catch (error) {
      const errorMessage: Message = {
        type: "bot",
        content: `An error occurred: ${(error as Error).message}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      toast.error((error as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setFile(event.target.files[0]);
    }
  };

  const handleFileRemove = () => {
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
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
      label: "Analyze financial reports",
      color: "bg-blue-200",
      textColor: "text-blue-700",
    },
    {
      icon: Calculator,
      label: "Calculate tax estimates",
      color: "bg-emerald-200",
      textColor: "text-emerald-700",
    },
    {
      icon: BarChart3,
      label: "Review budget analysis",
      color: "bg-purple-200",
      textColor: "text-purple-700",
    },
    {
      icon: Calendar,
      label: "Plan quarterly reviews",
      color: "bg-orange-200",
      textColor: "text-orange-700",
    },
  ];

  return (
    <div className="flex flex-col h-screen relative">
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

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto bg-gray-50">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full px-4">
            {/* Main heading */}
            <div className="text-center mb-12">
              <div className="mb-6">
                <div className="p-4 bg-teal-200 rounded-3xl w-20 h-20 mx-auto shadow-lg">
                  <Calculator className="h-12 w-12 text-teal-700" />
                </div>
              </div>
              <h1 className="text-4xl font-semibold text-gray-900 mb-3">
                What can I help with?
              </h1>
              <p className="text-gray-600 text-lg max-w-md mx-auto">
                Your intelligent accounting assistant powered by AI
              </p>
            </div>

            {/* Input area */}
            <div className="w-full max-w-2xl mb-12">
              <div className="relative group">
                <Input
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask about accounting, taxes, or financial planning..."
                  className="w-full h-16 pl-6 pr-16 text-lg border-2 border-gray-200 rounded-2xl bg-white shadow-md focus:shadow-lg focus:border-teal-300 focus:ring-0 focus:ring-offset-0 focus:outline-none transition-all duration-300 placeholder:text-gray-400"
                />
                { (message.trim() || file) && (
                  <Button
                    onClick={handleSend}
                    disabled={isLoading}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 h-10 w-10 p-0 bg-teal-600 hover:bg-teal-700 disabled:bg-gray-400 rounded-xl shadow-lg transition-all duration-200"
                  >
                    <Send className="h-4 w-4 text-white" />
                  </Button>
                )}
              </div>
              {file && (
                <div className="flex items-center justify-between p-2 mt-2 bg-gray-100 rounded-lg text-sm">
                  <span>{file.name}</span>
                  <Button variant="ghost" size="icon" onClick={handleFileRemove} className="h-6 w-6">
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              )}

              {/* Action buttons */}
              <div className="flex items-center justify-center gap-3 mt-6">
                <Button
                  variant="ghost"
                  onClick={() => fileInputRef.current?.click()}
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
              </div>
            </div>

            {/* Capabilities grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-2xl">
              {capabilities.map((capability, index) => {
                const Icon = capability.icon;
                return (
                  <Card
                    key={index}
                    className="group relative p-6 cursor-pointer border-0 bg-white shadow-lg hover:shadow-xl transition-all duration-300 rounded-2xl overflow-hidden"
                    onClick={() => setMessage(capability.label)}
                  >
                    <div
                      className={`absolute inset-0 ${capability.color} opacity-0 group-hover:opacity-10 transition-opacity duration-300`}
                    />
                    <div className="relative flex items-center gap-4">
                      <div
                        className={`p-3 rounded-xl ${capability.color} shadow-lg`}
                      >
                        <Icon className={`h-5 w-5 ${capability.textColor}`} />
                      </div>
                      <span className="text-base font-medium text-gray-800 group-hover:text-gray-900 transition-colors duration-200">
                        {capability.label}
                      </span>
                    </div>
                  </Card>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto py-8 px-6 space-y-8">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex ${
                  msg.type === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[75%] p-6 rounded-3xl shadow-lg ${
                    msg.type === "user"
                      ? "bg-gray-900 text-white"
                      : "bg-white text-gray-800 border border-gray-100"
                  }`}
                >
                  <p className="text-base leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  {msg.file && (
                    <div className="mt-2 text-xs opacity-80 text-gray-400">
                      Attached: {msg.file.name}
                    </div>
                  )}
                  <p
                    className={`text-xs mt-3 ${
                      msg.type === "user" ? "text-gray-400" : "text-gray-500"
                    }`}
                  >
                    {msg.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="max-w-[75%] p-6 rounded-3xl shadow-lg bg-white text-gray-800 border border-gray-100">
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
          </div>
        )}
      </div>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
      />

      {/* Input Area - for when there are messages */}
      {messages.length > 0 && (
        <div className="border-t border-gray-100 bg-white/80 backdrop-blur-sm">
          <div className="max-w-4xl mx-auto p-6">
            <div className="flex gap-4 items-end">
              <div className="flex-1 relative">
                <Input
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask a follow-up question..."
                  className="h-14 text-base border-2 border-gray-200 rounded-2xl bg-white focus:border-teal-300 focus:shadow-lg transition-all duration-300 pl-14 pr-4"
                />
                 <div className="absolute left-3 top-1/2 -translate-y-1/2 flex gap-2">
                  <Button variant="ghost" size="icon" onClick={() => fileInputRef.current?.click()}>
                    <Paperclip className="h-5 w-5" />
                  </Button>
                </div>
              </div>
              <Button
                onClick={handleSend}
                disabled={(!message.trim() && !file) || isLoading}
                className="h-14 w-14 p-0 bg-teal-600 hover:bg-teal-700 disabled:bg-gray-300 rounded-2xl shadow-lg transition-all duration-200"
              >
                <Send className="h-5 w-5 text-white" />
              </Button>
            </div>
             {file && (
              <div className="flex items-center justify-between p-2 mt-2 bg-gray-100 rounded-lg text-sm">
                <span>{file.name}</span>
                <Button variant="ghost" size="icon" onClick={handleFileRemove} className="h-6 w-6">
                  <X className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
