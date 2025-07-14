"use client";

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
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { useRouter } from "next/navigation";

export function ChatInterface() {
  const router = useRouter();
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
                {message.trim() && (
                  <Button
                    onClick={handleSend}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 h-10 w-10 p-0 bg-teal-600 hover:bg-teal-700 rounded-xl shadow-lg transition-all duration-200"
                  >
                    <Send className="h-4 w-4 text-white" />
                  </Button>
                )}
              </div>

              {/* Action buttons */}
              <div className="flex items-center justify-center gap-3 mt-6">
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
                  <p className="text-base leading-relaxed">{msg.content}</p>
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
          </div>
        )}
      </div>

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
                  className="h-14 text-base border-2 border-gray-200 rounded-2xl bg-white focus:border-teal-300 focus:shadow-lg transition-all duration-300 pl-6 pr-4"
                />
              </div>
              <Button
                onClick={handleSend}
                disabled={!message.trim()}
                className="h-14 w-14 p-0 bg-teal-600 hover:bg-teal-700 disabled:bg-gray-300 rounded-2xl shadow-lg transition-all duration-200"
              >
                <Send className="h-5 w-5 text-white" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
