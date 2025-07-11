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
  // SendHorizontal ,
} from "lucide-react";
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


export function ChatInterface() {
  const navigate = useNavigate();
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

    // <div className="flex flex-col gap-16 w-full h-screen relative">
    //   {/* Settings Button */}
    //   <div className="absolute top-4 right-4 z-10">
    //     <Button
    //       variant="ghost"
    //       size="sm"
    //       onClick={() => navigate("/knowledge-base")}
    //       className="p-3 bg-white/80 backdrop-blur-sm hover:bg-white shadow-lg rounded-xl border border-gray-200 transition-all duration-200"
    //     >
    //       <Settings className="h-4 w-4 text-gray-600" />
    //     </Button>
    //   </div>
    <SidebarProvider>
      <AppSidebar variant="inset" />
      <SidebarInset>
        <SiteHeader />
        <div className="flex flex-1 flex-col">
          <div className="@container/main flex flex-1 flex-col gap-2">
            <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
                {/* Title */}
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
                        <div className="max-w-ml mx-auto">
                          Upload your data, and let AI generate clear, compliant financial reports — faster than ever.
                        </div>
                      </div>

                      {/* File upload */}
                      <div className="border-2 border-dashed border-muted 
                            p-8 flex flex-col items-center justify-center text-center 
                            w-full h-full max-w-7xl min-h-80 cursor-pointer pb-8
                            bg-muted/10 hover:bg-muted/50 hover:border-ring transition-colors 
                            ">
                        <p>
                          Drag & drop your file here or click below to upload
                          <br />
                          (.json, .csv, .xlsx, .pdf)</p>
                        <Button variant="outline" size="default">Upload File</Button>
                      </div>

                      {/* Input area */}
                      <div className="w-full max-w-7xl">
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
                      </div>

                      {/* Capabilities grid
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
                        </div> */}
                    </div>
                  ) : (
                    <div className="max-w-4xl mx-auto py-8 px-6 space-y-8">
                      {messages.map((msg, index) => (
                        <div
                          key={index}
                          className={`flex ${msg.type === "user" ? "justify-end" : "justify-start"
                            }`}
                        >
                          <div
                            className={`max-w-[75%] p-6 rounded-3xl shadow-lg ${msg.type === "user"
                              ? "bg-gray-900 text-white"
                              : "bg-white text-gray-800 border border-gray-100"
                              }`}
                          >
                            <p className="text-base leading-relaxed">{msg.content}</p>
                            <p
                              className={`text-xs mt-3 ${msg.type === "user" ? "text-gray-400" : "text-gray-500"
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
                      <div className="flex items-end">
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
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
    // </div>

  );
}


