"""MemoryGraph - Core class for the unified graph memory system.

Combines graph structure (LanceDB) with semantic embeddings for:
- Event graph traversal (process execution)
- Knowledge graph exploration (context retrieval)
"""

from app.models.graph import (
    Edge,
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
from app.services.database import DatabaseService, get_database_service
from app.services.embedding import EmbeddingService, get_embedding_service


class MemoryGraph:
    """Main interface for the unified memory graph system.

    Provides:
    - CRUD operations for Events and Notes
    - Edge management with validation
    - Context resolution for Agent operations
    - Semantic search with reranking
    """

    def __init__(
        self,
        db_service: DatabaseService | None = None,
        embedding_service: EmbeddingService | None = None,
    ):
        self.db = db_service or get_database_service()
        self.embedding = embedding_service or get_embedding_service()

    # ==================== Event Operations ====================

    async def create_event(self, data: EventCreate) -> Event:
        """Create a new event with embedding."""
        event = Event(
            content=data.content,
            metadata=data.metadata,
            due_date=data.due_date,
            priority=data.priority,
        )

        # Generate embedding
        event.embedding = await self.embedding.embed_text(event.content)

        return self.db.add_node(event)  # type: ignore

    async def update_event(self, event_id: str, data: EventUpdate) -> Event | None:
        """Update an existing event."""
        event = self.db.get_node(event_id)
        if not event or not isinstance(event, Event):
            return None

        # Update fields
        if data.content is not None:
            event.content = data.content
            # Re-generate embedding if content changed
            event.embedding = await self.embedding.embed_text(event.content)
        if data.metadata is not None:
            event.metadata = data.metadata
        if data.status is not None:
            event.status = data.status
        if data.due_date is not None:
            event.due_date = data.due_date
        if data.priority is not None:
            event.priority = data.priority

        return self.db.update_node(event)  # type: ignore

    def get_event(self, event_id: str) -> Event | None:
        """Get an event by ID."""
        node = self.db.get_node(event_id)
        if node and isinstance(node, Event):
            return node
        return None

    def get_all_events(self, status: EventStatus | None = None) -> list[Event]:
        """Get all events, optionally filtered by status."""
        return self.db.get_events(status)

    def delete_event(self, event_id: str) -> bool:
        """Delete an event and its related edges."""
        return self.db.delete_node(event_id)

    # ==================== Note Operations ====================

    async def create_note(self, data: NoteCreate) -> Note:
        """Create a new note with embedding."""
        note = Note(
            content=data.content,
            metadata=data.metadata,
            title=data.title,
            tags=data.tags,
            source=data.source,
        )

        # Generate embedding from title + content
        text_for_embedding = f"{note.title}\n{note.content}" if note.title else note.content
        note.embedding = await self.embedding.embed_text(text_for_embedding)

        return self.db.add_node(note)  # type: ignore

    async def update_note(self, note_id: str, data: NoteUpdate) -> Note | None:
        """Update an existing note."""
        note = self.db.get_node(note_id)
        if not note or not isinstance(note, Note):
            return None

        content_changed = False
        if data.content is not None:
            note.content = data.content
            content_changed = True
        if data.metadata is not None:
            note.metadata = data.metadata
        if data.title is not None:
            note.title = data.title
            content_changed = True
        if data.tags is not None:
            note.tags = data.tags
        if data.source is not None:
            note.source = data.source

        # Re-generate embedding if content or title changed
        if content_changed:
            text_for_embedding = f"{note.title}\n{note.content}" if note.title else note.content
            note.embedding = await self.embedding.embed_text(text_for_embedding)

        return self.db.update_node(note)  # type: ignore

    def get_note(self, note_id: str) -> Note | None:
        """Get a note by ID."""
        node = self.db.get_node(note_id)
        if node and isinstance(node, Note):
            return node
        return None

    def get_all_notes(self) -> list[Note]:
        """Get all notes."""
        return self.db.get_notes()

    def delete_note(self, note_id: str) -> bool:
        """Delete a note and its related edges."""
        return self.db.delete_node(note_id)

    # ==================== Edge Operations ====================

    def link_nodes(self, data: EdgeCreate) -> Edge:
        """Create an edge between two nodes."""
        edge = Edge(
            source_id=data.source_id,
            target_id=data.target_id,
            edge_type=data.edge_type,
        )
        return self.db.add_edge(edge)

    def unlink_nodes(self, source_id: str, target_id: str, edge_type: EdgeType) -> bool:
        """Remove an edge between two nodes."""
        return self.db.delete_edge(source_id, target_id, edge_type)

    def get_node_edges(
        self,
        node_id: str,
        edge_type: EdgeType | None = None,
        direction: str = "both",
    ) -> list[Edge]:
        """Get edges connected to a node."""
        edges = []
        if direction in ("outgoing", "both"):
            edges.extend(self.db.get_edges(source_id=node_id, edge_type=edge_type))
        if direction in ("incoming", "both"):
            edges.extend(self.db.get_edges(target_id=node_id, edge_type=edge_type))
        return edges

    # ==================== Context Resolution ====================

    def resolve_context(self, node_id: str) -> GraphContext | None:
        """Get full context for a node (for Agent operations).

        Retrieves:
        - The main node
        - Dependencies (DEPENDS_ON edges)
        - Subtasks (PART_OF edges)
        - References (REFERENCES edges)
        - Produces (PRODUCES edges)
        """
        main = self.db.get_node(node_id)
        if not main:
            return None

        return GraphContext(
            main=main,
            dependencies=self.db.get_neighbors(node_id, EdgeType.DEPENDS_ON, "incoming"),
            subtasks=self.db.get_neighbors(node_id, EdgeType.PART_OF, "incoming"),
            references=self.db.get_neighbors(node_id, EdgeType.REFERENCES, "both"),
            produces=self.db.get_neighbors(node_id, EdgeType.PRODUCES, "outgoing"),
        )

    def get_event_execution_context(self, event_id: str) -> dict | None:
        """Get context for executing an event (task).

        Returns blocking dependencies, context notes, and subtasks.
        """
        event = self.get_event(event_id)
        if not event:
            return None

        # Check blocking dependencies
        blockers = self.db.get_predecessors(event_id, EdgeType.DEPENDS_ON)
        blocking = [e for e in blockers if isinstance(e, Event) and e.status != EventStatus.DONE]

        # Get reference notes
        references = self.db.get_successors(event_id, EdgeType.REFERENCES)
        context_notes = [n for n in references if isinstance(n, Note)]

        # Get subtasks
        subtasks = self.db.get_predecessors(event_id, EdgeType.PART_OF)
        sub_events = [e for e in subtasks if isinstance(e, Event)]

        return {
            "event": event,
            "blocking_dependencies": blocking,
            "context_notes": context_notes,
            "subtasks": sub_events,
            "can_execute": len(blocking) == 0,
        }

    # ==================== Semantic Search ====================

    async def search(
        self,
        query: str,
        limit: int = 10,
        node_type: NodeType | None = None,
        rerank: bool = True,
    ) -> list[GraphNode]:
        """Search for nodes using semantic similarity.

        Args:
            query: Search query text
            limit: Maximum number of results
            node_type: Filter by node type
            rerank: Whether to use reranking for better results

        Returns:
            List of nodes sorted by relevance
        """
        # Generate query embedding
        query_embedding = await self.embedding.embed_text(query)

        # Vector search
        results = self.db.search_by_vector(query_embedding, limit * 2, node_type)

        if not results:
            return []

        nodes = [node for node, _ in results]

        # Optional reranking
        if rerank and len(nodes) > 1:
            documents = [node.content for node in nodes]
            reranked = await self.embedding.rerank(query, documents, top_n=limit)
            # Reorder nodes based on reranking
            reranked_nodes = []
            for item in reranked:
                idx = item["index"]
                if idx < len(nodes):
                    reranked_nodes.append(nodes[idx])
            return reranked_nodes

        return nodes[:limit]

    async def find_related(
        self,
        node_id: str,
        limit: int = 5,
        same_type: bool = True,
    ) -> list[GraphNode]:
        """Find nodes semantically related to a given node."""
        node = self.db.get_node(node_id)
        if not node or not node.embedding:
            return []

        node_type = node.type if same_type else None
        results = self.db.search_by_vector(node.embedding, limit + 1, node_type)

        # Filter out the source node
        return [n for n, _ in results if n.id != node_id][:limit]

    # ==================== Graph Statistics ====================

    def get_stats(self) -> dict:
        """Get statistics about the memory graph."""
        all_nodes = self.db.get_all_nodes()
        all_edges = self.db.get_edges()

        events = [n for n in all_nodes if isinstance(n, Event)]
        notes = [n for n in all_nodes if isinstance(n, Note)]

        event_status_counts = {}
        for event in events:
            status = event.status.value
            event_status_counts[status] = event_status_counts.get(status, 0) + 1

        edge_type_counts = {}
        for edge in all_edges:
            etype = edge.edge_type.value
            edge_type_counts[etype] = edge_type_counts.get(etype, 0) + 1

        return {
            "total_nodes": len(all_nodes),
            "total_events": len(events),
            "total_notes": len(notes),
            "total_edges": len(all_edges),
            "event_status_counts": event_status_counts,
            "edge_type_counts": edge_type_counts,
        }


# Singleton instance
_memory_graph: MemoryGraph | None = None


def get_memory_graph() -> MemoryGraph:
    """Get the singleton MemoryGraph instance."""
    global _memory_graph
    if _memory_graph is None:
        _memory_graph = MemoryGraph()
    return _memory_graph
