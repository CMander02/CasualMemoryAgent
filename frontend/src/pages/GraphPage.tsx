import { useEffect, useState, useRef } from "react"
import { Share2, RefreshCw, ZoomIn, ZoomOut, Maximize2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface GraphNode {
  id: string
  type: "event" | "note"
  content: string
  title?: string
  status?: string
}

interface GraphEdge {
  source_id: string
  target_id: string
  edge_type: string
}

interface Stats {
  total_nodes: number
  total_edges: number
  event_status_counts: Record<string, number>
  edge_type_counts: Record<string, number>
}

export function GraphPage() {
  const [nodes, setNodes] = useState<GraphNode[]>([])
  const [edges, setEdges] = useState<GraphEdge[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [zoom, setZoom] = useState(1)
  const canvasRef = useRef<HTMLDivElement>(null)

  const fetchGraphData = async () => {
    setIsLoading(true)
    try {
      const [eventsRes, notesRes, statsRes] = await Promise.all([
        fetch("/api/memory/events"),
        fetch("/api/memory/notes"),
        fetch("/api/memory/stats"),
      ])

      if (eventsRes.ok && notesRes.ok) {
        const events = await eventsRes.json()
        const notes = await notesRes.json()
        setNodes([...events, ...notes])
      }

      if (statsRes.ok) {
        const statsData = await statsRes.json()
        setStats(statsData)
      }

      // Fetch edges for all nodes
      const allEdges: GraphEdge[] = []
      // For demo, we'll just show the stats - in production you'd fetch actual edges
    } catch (error) {
      console.error("Failed to fetch graph data:", error)
    }
    setIsLoading(false)
  }

  useEffect(() => {
    fetchGraphData()
  }, [])

  // Simple force-directed layout simulation
  const getNodePositions = () => {
    const positions: Record<string, { x: number; y: number }> = {}
    const centerX = 400
    const centerY = 300
    const radius = 200

    nodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / nodes.length
      const jitter = Math.random() * 50 - 25
      positions[node.id] = {
        x: centerX + (radius + jitter) * Math.cos(angle),
        y: centerY + (radius + jitter) * Math.sin(angle),
      }
    })

    return positions
  }

  const nodePositions = getNodePositions()

  return (
    <div className="flex h-full flex-col p-6">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Graph View</h1>
          <p className="text-sm text-muted-foreground">
            Visualize connections between memories and events
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" onClick={() => setZoom(z => Math.max(0.5, z - 0.1))}>
            <ZoomOut className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" onClick={() => setZoom(z => Math.min(2, z + 0.1))}>
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" onClick={fetchGraphData}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="flex flex-1 gap-4 min-h-0">
        {/* Graph canvas */}
        <Card className="flex-1 flex flex-col overflow-hidden">
          <CardContent className="flex-1 p-0 relative">
            {isLoading ? (
              <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
                Loading graph...
              </div>
            ) : nodes.length === 0 ? (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground">
                <Share2 className="mb-2 h-12 w-12 opacity-30" />
                <p>No nodes in the graph</p>
                <p className="text-xs">Create events or notes to visualize connections</p>
              </div>
            ) : (
              <div
                ref={canvasRef}
                className="absolute inset-0 overflow-auto"
                style={{ transform: `scale(${zoom})`, transformOrigin: "center" }}
              >
                <svg className="w-full h-full min-w-[800px] min-h-[600px]">
                  {/* Grid background */}
                  <defs>
                    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                      <path
                        d="M 40 0 L 0 0 0 40"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="0.5"
                        className="text-border/30"
                      />
                    </pattern>
                  </defs>
                  <rect width="100%" height="100%" fill="url(#grid)" />

                  {/* Edges */}
                  {edges.map((edge, i) => {
                    const source = nodePositions[edge.source_id]
                    const target = nodePositions[edge.target_id]
                    if (!source || !target) return null
                    return (
                      <line
                        key={i}
                        x1={source.x}
                        y1={source.y}
                        x2={target.x}
                        y2={target.y}
                        stroke="currentColor"
                        strokeWidth="1"
                        className="text-border"
                        markerEnd="url(#arrow)"
                      />
                    )
                  })}

                  {/* Arrow marker */}
                  <defs>
                    <marker
                      id="arrow"
                      viewBox="0 0 10 10"
                      refX="10"
                      refY="5"
                      markerWidth="6"
                      markerHeight="6"
                      orient="auto-start-reverse"
                    >
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor" className="text-border" />
                    </marker>
                  </defs>

                  {/* Nodes */}
                  {nodes.map((node) => {
                    const pos = nodePositions[node.id]
                    if (!pos) return null
                    const isEvent = node.type === "event"
                    const isSelected = selectedNode?.id === node.id
                    return (
                      <g
                        key={node.id}
                        transform={`translate(${pos.x}, ${pos.y})`}
                        onClick={() => setSelectedNode(node)}
                        className="cursor-pointer"
                      >
                        {/* Glow effect for selected */}
                        {isSelected && (
                          <circle
                            r="35"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            className="text-primary animate-pulse"
                          />
                        )}
                        {/* Node circle */}
                        <circle
                          r="24"
                          fill="currentColor"
                          className={cn(
                            "transition-colors",
                            isEvent ? "text-chart-3" : "text-primary",
                            isSelected && "text-primary"
                          )}
                        />
                        {/* Inner circle */}
                        <circle r="20" fill="currentColor" className="text-card" />
                        {/* Icon */}
                        <text
                          textAnchor="middle"
                          dominantBaseline="central"
                          className={cn(
                            "text-xs font-mono fill-current",
                            isEvent ? "text-chart-3" : "text-primary"
                          )}
                        >
                          {isEvent ? "E" : "N"}
                        </text>
                        {/* Label */}
                        <text
                          y="40"
                          textAnchor="middle"
                          className="text-[10px] fill-current text-muted-foreground"
                        >
                          {(node.title || node.content).slice(0, 15)}
                          {(node.title || node.content).length > 15 ? "..." : ""}
                        </text>
                      </g>
                    )
                  })}
                </svg>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Sidebar */}
        <div className="w-72 space-y-4 shrink-0">
          {/* Stats */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Graph Statistics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Total Nodes</span>
                <span className="font-mono">{stats?.total_nodes ?? 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Total Edges</span>
                <span className="font-mono">{stats?.total_edges ?? 0}</span>
              </div>
              <div className="pt-2 border-t space-y-1">
                <p className="text-xs text-muted-foreground mb-1">Edge Types</p>
                {stats?.edge_type_counts && Object.entries(stats.edge_type_counts).map(([type, count]) => (
                  <div key={type} className="flex justify-between text-xs">
                    <span className="text-muted-foreground">{type}</span>
                    <span className="font-mono">{count}</span>
                  </div>
                ))}
                {(!stats?.edge_type_counts || Object.keys(stats.edge_type_counts).length === 0) && (
                  <p className="text-xs text-muted-foreground">No edges yet</p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Selected node details */}
          {selectedNode && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Selected Node</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div>
                  <p className="text-xs text-muted-foreground">Type</p>
                  <p className={cn(
                    "text-sm font-medium",
                    selectedNode.type === "event" ? "text-chart-3" : "text-primary"
                  )}>
                    {selectedNode.type === "event" ? "Event" : "Note"}
                  </p>
                </div>
                {selectedNode.title && (
                  <div>
                    <p className="text-xs text-muted-foreground">Title</p>
                    <p className="text-sm">{selectedNode.title}</p>
                  </div>
                )}
                <div>
                  <p className="text-xs text-muted-foreground">Content</p>
                  <p className="text-sm line-clamp-4">{selectedNode.content}</p>
                </div>
                {selectedNode.status && (
                  <div>
                    <p className="text-xs text-muted-foreground">Status</p>
                    <p className="text-sm">{selectedNode.status}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Legend */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Legend</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="h-4 w-4 rounded-full bg-chart-3" />
                <span className="text-sm text-muted-foreground">Event Node</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-4 w-4 rounded-full bg-primary" />
                <span className="text-sm text-muted-foreground">Note Node</span>
              </div>
              <div className="flex items-center gap-2 pt-2 border-t">
                <div className="h-0.5 w-8 bg-border" />
                <span className="text-sm text-muted-foreground">Connection</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
