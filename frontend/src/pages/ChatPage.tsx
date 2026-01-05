import { Chat } from "@/components/Chat"

export function ChatPage() {
  return (
    <div className="flex h-full flex-col p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">Chat</h1>
        <p className="text-sm text-muted-foreground">
          Interact with the AI assistant with memory augmentation
        </p>
      </div>
      <div className="flex-1 min-h-0">
        <Chat />
      </div>
    </div>
  )
}
