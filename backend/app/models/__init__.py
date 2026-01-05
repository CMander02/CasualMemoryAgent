"""Data models for the Casual Memory Agent."""

from app.models.chat import ChatRequest, ChatResponse, Message
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
    NodeCreate,
    NodeType,
    NodeUpdate,
    Note,
    NoteCreate,
    NoteUpdate,
    VALID_EDGE_TYPES,
)

__all__ = [
    # Chat models
    "Message",
    "ChatRequest",
    "ChatResponse",
    # Graph models
    "NodeType",
    "EventStatus",
    "EdgeType",
    "GraphNode",
    "Event",
    "Note",
    "Edge",
    "VALID_EDGE_TYPES",
    # Request/Response models
    "NodeCreate",
    "EventCreate",
    "NoteCreate",
    "NodeUpdate",
    "EventUpdate",
    "NoteUpdate",
    "EdgeCreate",
    "GraphContext",
]
