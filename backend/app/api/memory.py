"""API endpoints for the unified memory graph system."""

from fastapi import APIRouter, HTTPException

from app.models.graph import (
    EdgeCreate,
    EdgeType,
    Event,
    EventCreate,
    EventStatus,
    EventUpdate,
    GraphContext,
    GraphNode,
    NodeType,
    Note,
    NoteCreate,
    NoteUpdate,
)
from app.services import CyclicDependencyError, InvalidEdgeTypeError, get_memory_graph

router = APIRouter(prefix="/memory", tags=["memory"])


# ==================== Event Endpoints ====================


@router.post("/events", response_model=Event)
async def create_event(data: EventCreate):
    """Create a new event."""
    graph = get_memory_graph()
    return await graph.create_event(data)


@router.get("/events", response_model=list[Event])
async def list_events(status: EventStatus | None = None):
    """List all events, optionally filtered by status."""
    graph = get_memory_graph()
    return graph.get_all_events(status)


@router.get("/events/{event_id}", response_model=Event)
async def get_event(event_id: str):
    """Get a specific event by ID."""
    graph = get_memory_graph()
    event = graph.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.patch("/events/{event_id}", response_model=Event)
async def update_event(event_id: str, data: EventUpdate):
    """Update an existing event."""
    graph = get_memory_graph()
    event = await graph.update_event(event_id, data)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.delete("/events/{event_id}")
async def delete_event(event_id: str):
    """Delete an event."""
    graph = get_memory_graph()
    if not graph.get_event(event_id):
        raise HTTPException(status_code=404, detail="Event not found")
    graph.delete_event(event_id)
    return {"message": "Event deleted"}


@router.get("/events/{event_id}/context")
async def get_event_context(event_id: str):
    """Get execution context for an event."""
    graph = get_memory_graph()
    context = graph.get_event_execution_context(event_id)
    if not context:
        raise HTTPException(status_code=404, detail="Event not found")
    return context


# ==================== Note Endpoints ====================


@router.post("/notes", response_model=Note)
async def create_note(data: NoteCreate):
    """Create a new note."""
    graph = get_memory_graph()
    return await graph.create_note(data)


@router.get("/notes", response_model=list[Note])
async def list_notes():
    """List all notes."""
    graph = get_memory_graph()
    return graph.get_all_notes()


@router.get("/notes/{note_id}", response_model=Note)
async def get_note(note_id: str):
    """Get a specific note by ID."""
    graph = get_memory_graph()
    note = graph.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.patch("/notes/{note_id}", response_model=Note)
async def update_note(note_id: str, data: NoteUpdate):
    """Update an existing note."""
    graph = get_memory_graph()
    note = await graph.update_note(note_id, data)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.delete("/notes/{note_id}")
async def delete_note(note_id: str):
    """Delete a note."""
    graph = get_memory_graph()
    if not graph.get_note(note_id):
        raise HTTPException(status_code=404, detail="Note not found")
    graph.delete_note(note_id)
    return {"message": "Note deleted"}


# ==================== Edge Endpoints ====================


@router.post("/edges")
async def create_edge(data: EdgeCreate):
    """Create an edge between two nodes."""
    graph = get_memory_graph()
    try:
        edge = graph.link_nodes(data)
        return {
            "source_id": edge.source_id,
            "target_id": edge.target_id,
            "edge_type": edge.edge_type.value,
            "created_at": edge.created_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidEdgeTypeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CyclicDependencyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/edges")
async def delete_edge(source_id: str, target_id: str, edge_type: EdgeType):
    """Delete an edge between two nodes."""
    graph = get_memory_graph()
    graph.unlink_nodes(source_id, target_id, edge_type)
    return {"message": "Edge deleted"}


@router.get("/nodes/{node_id}/edges")
async def get_node_edges(
    node_id: str,
    edge_type: EdgeType | None = None,
    direction: str = "both",
):
    """Get edges connected to a node."""
    graph = get_memory_graph()
    edges = graph.get_node_edges(node_id, edge_type, direction)
    return [
        {
            "source_id": e.source_id,
            "target_id": e.target_id,
            "edge_type": e.edge_type.value,
            "created_at": e.created_at.isoformat(),
        }
        for e in edges
    ]


# ==================== Context & Search Endpoints ====================


@router.get("/nodes/{node_id}/context", response_model=GraphContext)
async def get_node_context(node_id: str):
    """Get full context for a node."""
    graph = get_memory_graph()
    context = graph.resolve_context(node_id)
    if not context:
        raise HTTPException(status_code=404, detail="Node not found")
    return context


@router.get("/search", response_model=list[GraphNode])
async def search_nodes(
    query: str,
    limit: int = 10,
    node_type: NodeType | None = None,
    rerank: bool = True,
):
    """Search for nodes using semantic similarity."""
    graph = get_memory_graph()
    return await graph.search(query, limit, node_type, rerank)


@router.get("/nodes/{node_id}/related", response_model=list[GraphNode])
async def find_related_nodes(
    node_id: str,
    limit: int = 5,
    same_type: bool = True,
):
    """Find nodes semantically related to a given node."""
    graph = get_memory_graph()
    return await graph.find_related(node_id, limit, same_type)


# ==================== Statistics Endpoint ====================


@router.get("/stats")
async def get_stats():
    """Get statistics about the memory graph."""
    graph = get_memory_graph()
    return graph.get_stats()
