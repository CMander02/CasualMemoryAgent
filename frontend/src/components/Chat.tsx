import { useRef, useEffect } from "react"
import { Send, Brain, Trash2, Save, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useChatApi } from "@/hooks/use-chat-api"
import { cn } from "@/lib/utils"

export function Chat() {
  const {
    messages,
    input,
    isLoading,
    useMemory,
    setUseMemory,
    handleInputChange,
    handleSubmit,
    clearMessages,
    saveToMemory,
  } = useChatApi()
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const handleSaveConversation = async () => {
    if (messages.length === 0) return
    const content = messages
      .map((m) => `${m.role === "user" ? "User" : "Assistant"}: ${m.content}`)
      .join("\n\n")
    const success = await saveToMemory(content, "Chat Conversation", ["chat", "conversation"])
    if (success) {
      alert("Conversation saved to memory!")
    }
  }

  return (
    <Card className="flex h-full flex-col bg-card/50 backdrop-blur">
      {/* Header */}
      <CardHeader className="flex flex-row items-center justify-between border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium">AI Assistant</span>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant={useMemory ? "default" : "outline"}
            size="sm"
            onClick={() => setUseMemory(!useMemory)}
            className={cn(
              "h-8 gap-1.5 text-xs",
              useMemory && "bg-primary/90 hover:bg-primary"
            )}
          >
            <Brain className="h-3.5 w-3.5" />
            Memory {useMemory ? "On" : "Off"}
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleSaveConversation}
            disabled={messages.length === 0}
            className="h-8 w-8"
            title="Save conversation to memory"
          >
            <Save className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={clearMessages}
            disabled={messages.length === 0}
            className="h-8 w-8"
            title="Clear conversation"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </CardHeader>

      {/* Messages */}
      <CardContent className="flex-1 p-0 overflow-hidden">
        <ScrollArea className="h-full p-4" ref={scrollRef}>
          <div className="space-y-4">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="relative mb-4">
                  <div className="absolute inset-0 rounded-full bg-primary/20 blur-xl" />
                  <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                    <Sparkles className="h-8 w-8 text-primary" />
                  </div>
                </div>
                <h3 className="font-mono text-lg font-medium">Start a Conversation</h3>
                <p className="mt-1 max-w-sm text-sm text-muted-foreground">
                  {useMemory
                    ? "Memory is enabled. The AI will use relevant context from your notes."
                    : "Ask anything. Enable Memory to enhance responses with your saved knowledge."}
                </p>
              </div>
            )}
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "flex",
                  message.role === "user" ? "justify-end" : "justify-start"
                )}
              >
                <div
                  className={cn(
                    "rounded-2xl px-4 py-2.5 max-w-[85%]",
                    message.role === "user"
                      ? "bg-primary text-primary-foreground rounded-br-md"
                      : "bg-muted rounded-bl-md"
                  )}
                >
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">
                    {message.content}
                  </p>
                </div>
              </div>
            ))}
            {isLoading && messages[messages.length - 1]?.role === "user" && (
              <div className="flex justify-start">
                <div className="bg-muted rounded-2xl rounded-bl-md px-4 py-2.5">
                  <div className="flex items-center gap-1.5">
                    <div className="h-2 w-2 rounded-full bg-primary/60 animate-pulse" />
                    <div className="h-2 w-2 rounded-full bg-primary/60 animate-pulse [animation-delay:150ms]" />
                    <div className="h-2 w-2 rounded-full bg-primary/60 animate-pulse [animation-delay:300ms]" />
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>

      {/* Input */}
      <CardFooter className="border-t p-4">
        <form onSubmit={handleSubmit} className="flex w-full gap-2">
          <Input
            value={input}
            onChange={handleInputChange}
            placeholder={useMemory ? "Ask with memory context..." : "Type a message..."}
            disabled={isLoading}
            className="flex-1 bg-background"
          />
          <Button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="shrink-0"
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </CardFooter>
    </Card>
  )
}
