import { useEffect, useState } from "react"
import {
  CalendarCheck,
  Plus,
  Clock,
  CheckCircle2,
  Circle,
  Loader2,
  Archive,
  Trash2,
  RefreshCw,
  ChevronRight,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"

type EventStatus = "pending" | "in_progress" | "done" | "archived"

interface Event {
  id: string
  content: string
  status: EventStatus
  priority: number
  due_date: string | null
  created_at: string
  updated_at: string
}

const statusConfig: Record<EventStatus, { icon: typeof Circle; label: string; color: string }> = {
  pending: { icon: Circle, label: "Pending", color: "text-muted-foreground" },
  in_progress: { icon: Loader2, label: "In Progress", color: "text-chart-3" },
  done: { icon: CheckCircle2, label: "Done", color: "text-chart-2" },
  archived: { icon: Archive, label: "Archived", color: "text-muted-foreground/50" },
}

export function EventsPage() {
  const [events, setEvents] = useState<Event[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [newEventContent, setNewEventContent] = useState("")
  const [filter, setFilter] = useState<EventStatus | "all">("all")
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null)

  const fetchEvents = async (status?: EventStatus) => {
    try {
      const url = status ? `/api/memory/events?status=${status}` : "/api/memory/events"
      const response = await fetch(url)
      if (response.ok) {
        const data = await response.json()
        setEvents(data)
      }
    } catch (error) {
      console.error("Failed to fetch events:", error)
    }
  }

  const createEvent = async () => {
    if (!newEventContent.trim()) return
    try {
      const response = await fetch("/api/memory/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: newEventContent }),
      })
      if (response.ok) {
        setNewEventContent("")
        fetchEvents()
      }
    } catch (error) {
      console.error("Failed to create event:", error)
    }
  }

  const updateEventStatus = async (eventId: string, status: EventStatus) => {
    try {
      const response = await fetch(`/api/memory/events/${eventId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      })
      if (response.ok) {
        fetchEvents()
        if (selectedEvent?.id === eventId) {
          const updated = await response.json()
          setSelectedEvent(updated)
        }
      }
    } catch (error) {
      console.error("Failed to update event:", error)
    }
  }

  const deleteEvent = async (eventId: string) => {
    try {
      const response = await fetch(`/api/memory/events/${eventId}`, {
        method: "DELETE",
      })
      if (response.ok) {
        setEvents(events.filter((e) => e.id !== eventId))
        if (selectedEvent?.id === eventId) {
          setSelectedEvent(null)
        }
      }
    } catch (error) {
      console.error("Failed to delete event:", error)
    }
  }

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true)
      await fetchEvents()
      setIsLoading(false)
    }
    loadData()
  }, [])

  const filteredEvents = filter === "all" ? events : events.filter((e) => e.status === filter)

  const statusCounts = events.reduce(
    (acc, event) => {
      acc[event.status] = (acc[event.status] || 0) + 1
      return acc
    },
    {} as Record<string, number>
  )

  return (
    <div className="flex h-full flex-col p-6">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Events</h1>
          <p className="text-sm text-muted-foreground">
            Manage tasks and track progress in the event graph
          </p>
        </div>
        <Button
          variant="outline"
          size="icon"
          onClick={() => fetchEvents()}
          className="shrink-0"
        >
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      {/* Status filters */}
      <div className="mb-4 flex flex-wrap gap-2">
        <Button
          variant={filter === "all" ? "default" : "outline"}
          size="sm"
          onClick={() => setFilter("all")}
          className="h-8"
        >
          All ({events.length})
        </Button>
        {(Object.keys(statusConfig) as EventStatus[]).map((status) => {
          const config = statusConfig[status]
          const count = statusCounts[status] || 0
          return (
            <Button
              key={status}
              variant={filter === status ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter(status)}
              className={cn("h-8 gap-1.5", filter !== status && config.color)}
            >
              <config.icon className="h-3.5 w-3.5" />
              {config.label} ({count})
            </Button>
          )
        })}
      </div>

      {/* Add new event */}
      <div className="mb-4 flex gap-2">
        <Input
          placeholder="Add a new event..."
          value={newEventContent}
          onChange={(e) => setNewEventContent(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && createEvent()}
          className="flex-1"
        />
        <Button onClick={createEvent} disabled={!newEventContent.trim()}>
          <Plus className="mr-2 h-4 w-4" />
          Add Event
        </Button>
      </div>

      {/* Events list */}
      <div className="flex flex-1 gap-4 min-h-0">
        <Card className="flex-1 flex flex-col">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">
              Events ({filteredEvents.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 p-0">
            <ScrollArea className="h-full px-4 pb-4">
              {isLoading ? (
                <div className="flex items-center justify-center py-8 text-muted-foreground">
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Loading...
                </div>
              ) : filteredEvents.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
                  <CalendarCheck className="mb-2 h-8 w-8 opacity-50" />
                  <p>No events yet</p>
                  <p className="text-xs">Create an event to get started</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredEvents.map((event) => {
                    const config = statusConfig[event.status]
                    return (
                      <div
                        key={event.id}
                        onClick={() => setSelectedEvent(event)}
                        className={cn(
                          "group flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition-all hover:border-primary/50 hover:bg-muted/50",
                          selectedEvent?.id === event.id && "border-primary bg-muted/50"
                        )}
                      >
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            const nextStatus: Record<EventStatus, EventStatus> = {
                              pending: "in_progress",
                              in_progress: "done",
                              done: "archived",
                              archived: "pending",
                            }
                            updateEventStatus(event.id, nextStatus[event.status])
                          }}
                          className={cn(
                            "mt-0.5 shrink-0 transition-colors hover:text-primary",
                            config.color
                          )}
                        >
                          <config.icon
                            className={cn(
                              "h-5 w-5",
                              event.status === "in_progress" && "animate-spin"
                            )}
                          />
                        </button>
                        <div className="min-w-0 flex-1">
                          <p
                            className={cn(
                              "text-sm",
                              event.status === "done" && "line-through text-muted-foreground",
                              event.status === "archived" && "text-muted-foreground/50"
                            )}
                          >
                            {event.content}
                          </p>
                          <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                            {event.priority > 0 && (
                              <span className="text-chart-5">Priority: {event.priority}</span>
                            )}
                            {event.due_date && (
                              <span className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {new Date(event.due_date).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 opacity-0 group-hover:opacity-100 shrink-0"
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteEvent(event.id)
                          }}
                        >
                          <Trash2 className="h-3.5 w-3.5 text-destructive" />
                        </Button>
                      </div>
                    )
                  })}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Event detail */}
        {selectedEvent && (
          <Card className="w-80 flex flex-col shrink-0">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Event Details</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-auto space-y-4">
              <div>
                <p className="text-sm font-medium">{selectedEvent.content}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Created: {new Date(selectedEvent.created_at).toLocaleString()}
                </p>
              </div>

              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">Status</p>
                <div className="flex flex-wrap gap-1">
                  {(Object.keys(statusConfig) as EventStatus[]).map((status) => {
                    const config = statusConfig[status]
                    return (
                      <Button
                        key={status}
                        variant={selectedEvent.status === status ? "default" : "outline"}
                        size="sm"
                        onClick={() => updateEventStatus(selectedEvent.id, status)}
                        className="h-7 text-xs gap-1"
                      >
                        <config.icon className="h-3 w-3" />
                        {config.label}
                      </Button>
                    )
                  })}
                </div>
              </div>

              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">Dependencies</p>
                <p className="text-xs text-muted-foreground">
                  No dependencies configured
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
