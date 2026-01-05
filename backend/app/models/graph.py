"""Unified graph memory system models.

Based on the design principle that Note (笔记) and Event (事件) are projections
of the same physical structure (graph nodes) in different semantic dimensions.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """Types of nodes in the memory graph."""

    EVENT = "event"
    NOTE = "note"


class EventStatus(str, Enum):
    """Status of an event node."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"


class EdgeType(str, Enum):
    """Types of edges in the memory graph.

    Minimal edge types with content-based semantics:
    - Graph structure records relationship existence and direction
    - Semantic details are expressed in node content itself
    - LLM Agent reads content and naturally understands semantics
    """

    DEPENDS_ON = "depends_on"  # Temporal dependency (Event -> Event)
    PART_OF = "part_of"  # Hierarchical containment (Event -> Event)
    REFERENCES = "references"  # Reference association (Any -> Any)
    PRODUCES = "produces"  # Causal output (Event <-> Note)


class GraphNode(BaseModel):
    """Base class for all graph nodes."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    type: NodeType
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] | None = None


class Event(GraphNode):
    """Event node - represents a task or action in the process graph.

    Agent follows the event graph to complete tasks.
    """

    type: NodeType = NodeType.EVENT
    status: EventStatus = EventStatus.PENDING
    due_date: datetime | None = None
    priority: int = 0


class Note(GraphNode):
    """Note node - represents knowledge in the knowledge network.

    Agent follows the note graph to understand context.
    """

    type: NodeType = NodeType.NOTE
    title: str = ""
    tags: list[str] = Field(default_factory=list)
    source: str | None = None


class Edge(BaseModel):
    """Edge connecting two nodes in the memory graph."""

    source_id: str
    target_id: str
    edge_type: EdgeType
    created_at: datetime = Field(default_factory=datetime.now)


# Valid edge type combinations
VALID_EDGE_TYPES: dict[tuple[NodeType, NodeType], list[EdgeType]] = {
    (NodeType.EVENT, NodeType.EVENT): [EdgeType.DEPENDS_ON, EdgeType.PART_OF],
    (NodeType.NOTE, NodeType.NOTE): [EdgeType.REFERENCES],
    (NodeType.EVENT, NodeType.NOTE): [EdgeType.REFERENCES, EdgeType.PRODUCES],
    (NodeType.NOTE, NodeType.EVENT): [EdgeType.REFERENCES, EdgeType.PRODUCES],
}


# Request/Response models for API
class NodeCreate(BaseModel):
    """Base model for creating a node."""

    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class EventCreate(NodeCreate):
    """Model for creating an event."""

    due_date: datetime | None = None
    priority: int = 0


class NoteCreate(NodeCreate):
    """Model for creating a note."""

    title: str = ""
    tags: list[str] = Field(default_factory=list)
    source: str | None = None


class NodeUpdate(BaseModel):
    """Model for updating a node."""

    content: str | None = None
    metadata: dict[str, Any] | None = None


class EventUpdate(NodeUpdate):
    """Model for updating an event."""

    status: EventStatus | None = None
    due_date: datetime | None = None
    priority: int | None = None


class NoteUpdate(NodeUpdate):
    """Model for updating a note."""

    title: str | None = None
    tags: list[str] | None = None
    source: str | None = None


class EdgeCreate(BaseModel):
    """Model for creating an edge."""

    source_id: str
    target_id: str
    edge_type: EdgeType


class GraphContext(BaseModel):
    """Context retrieved from the memory graph for a node."""

    main: GraphNode
    dependencies: list[GraphNode] = Field(default_factory=list)
    subtasks: list[GraphNode] = Field(default_factory=list)
    references: list[GraphNode] = Field(default_factory=list)
    produces: list[GraphNode] = Field(default_factory=list)
