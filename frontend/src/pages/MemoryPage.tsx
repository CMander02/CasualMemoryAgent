import { useEffect, useState } from "react"
import { Brain, Search, Plus, FileText, Tag, Trash2, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"

interface Note {
  id: string
  title: string
  content: string
  tags: string[]
  created_at: string
  updated_at: string
}

interface Stats {
  total_nodes: number
  total_events: number
  total_notes: number
  total_edges: number
}

export function MemoryPage() {
  const [notes, setNotes] = useState<Note[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [selectedNote, setSelectedNote] = useState<Note | null>(null)

  const fetchNotes = async () => {
    try {
      const response = await fetch("/api/memory/notes")
      if (response.ok) {
        const data = await response.json()
        setNotes(data)
      }
    } catch (error) {
      console.error("Failed to fetch notes:", error)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await fetch("/api/memory/stats")
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (error) {
      console.error("Failed to fetch stats:", error)
    }
  }

  const searchNotes = async () => {
    if (!searchQuery.trim()) {
      fetchNotes()
      return
    }
    try {
      const response = await fetch(
        `/api/memory/search?query=${encodeURIComponent(searchQuery)}&node_type=note&limit=20`
      )
      if (response.ok) {
        const data = await response.json()
        setNotes(data)
      }
    } catch (error) {
      console.error("Failed to search notes:", error)
    }
  }

  const deleteNote = async (noteId: string) => {
    try {
      const response = await fetch(`/api/memory/notes/${noteId}`, {
        method: "DELETE",
      })
      if (response.ok) {
        setNotes(notes.filter((n) => n.id !== noteId))
        if (selectedNote?.id === noteId) {
          setSelectedNote(null)
        }
        fetchStats()
      }
    } catch (error) {
      console.error("Failed to delete note:", error)
    }
  }

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true)
      await Promise.all([fetchNotes(), fetchStats()])
      setIsLoading(false)
    }
    loadData()
  }, [])

  const filteredNotes = notes

  return (
    <div className="flex h-full flex-col p-6">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Memory</h1>
          <p className="text-sm text-muted-foreground">
            Browse and manage your knowledge notes
          </p>
        </div>
        <Button
          variant="outline"
          size="icon"
          onClick={() => {
            fetchNotes()
            fetchStats()
          }}
          className="shrink-0"
        >
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      {/* Stats cards */}
      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="bg-card/50 backdrop-blur">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Nodes
            </CardTitle>
            <Brain className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-mono">
              {stats?.total_nodes ?? "—"}
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card/50 backdrop-blur">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Notes
            </CardTitle>
            <FileText className="h-4 w-4 text-chart-2" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-mono">
              {stats?.total_notes ?? "—"}
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card/50 backdrop-blur">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Events
            </CardTitle>
            <Tag className="h-4 w-4 text-chart-3" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-mono">
              {stats?.total_events ?? "—"}
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card/50 backdrop-blur">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Connections
            </CardTitle>
            <div className="h-4 w-4 rounded-full bg-chart-4" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-mono">
              {stats?.total_edges ?? "—"}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="mb-4 flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search notes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && searchNotes()}
            className="pl-9"
          />
        </div>
        <Button onClick={searchNotes}>Search</Button>
      </div>

      {/* Notes list */}
      <div className="flex flex-1 gap-4 min-h-0">
        <Card className="flex-1 flex flex-col">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">
              Notes ({filteredNotes.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 p-0">
            <ScrollArea className="h-full px-4 pb-4">
              {isLoading ? (
                <div className="flex items-center justify-center py-8 text-muted-foreground">
                  Loading...
                </div>
              ) : filteredNotes.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
                  <Brain className="mb-2 h-8 w-8 opacity-50" />
                  <p>No notes yet</p>
                  <p className="text-xs">Save conversations to memory to see them here</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredNotes.map((note) => (
                    <div
                      key={note.id}
                      onClick={() => setSelectedNote(note)}
                      className={cn(
                        "group cursor-pointer rounded-lg border p-3 transition-all hover:border-primary/50 hover:bg-muted/50",
                        selectedNote?.id === note.id && "border-primary bg-muted/50"
                      )}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0 flex-1">
                          <h3 className="truncate font-medium text-sm">
                            {note.title || "Untitled Note"}
                          </h3>
                          <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                            {note.content}
                          </p>
                          {note.tags && note.tags.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1">
                              {note.tags.slice(0, 3).map((tag) => (
                                <span
                                  key={tag}
                                  className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary"
                                >
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 opacity-0 group-hover:opacity-100 shrink-0"
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteNote(note.id)
                          }}
                        >
                          <Trash2 className="h-3.5 w-3.5 text-destructive" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Note detail */}
        {selectedNote && (
          <Card className="w-96 flex flex-col shrink-0">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Note Details</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-auto">
              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold">{selectedNote.title || "Untitled"}</h3>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Created: {new Date(selectedNote.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="text-sm whitespace-pre-wrap">{selectedNote.content}</div>
                {selectedNote.tags && selectedNote.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {selectedNote.tags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
