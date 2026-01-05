"""LanceDB storage service for the unified graph memory system.

Stores both graph structure and vector embeddings in LanceDB tables.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import lancedb
import pyarrow as pa
from lancedb.pydantic import LanceModel, Vector

from app.core.config import get_settings
from app.models.graph import (
    VALID_EDGE_TYPES,
    Edge,
    EdgeType,
    Event,
    EventStatus,
    GraphNode,
    NodeType,
    Note,
)


# LanceDB schema models
class NodeRecord(LanceModel):
    """LanceDB record for graph nodes with vector embeddings."""

    id: str
    type: str  # NodeType as string
    content: str
    created_at: str  # datetime as ISO string
    updated_at: str
    metadata_json: str  # JSON serialized metadata

    # Event-specific fields (nullable for notes)
    status: Optional[str] = None  # EventStatus as string
    due_date: Optional[str] = None
    priority: Optional[int] = None

    # Note-specific fields (nullable for events)
    title: Optional[str] = None
    tags_json: Optional[str] = None  # JSON serialized list
    source: Optional[str] = None

    # Vector embedding - use list[float] for compatibility
    vector: Optional[list[float]] = None


class EdgeRecord(LanceModel):
    """LanceDB record for graph edges."""

    source_id: str
    target_id: str
    edge_type: str  # EdgeType as string
    created_at: str


class CyclicDependencyError(Exception):
    """Raised when adding an edge would create a cycle in the event graph."""

    pass


class InvalidEdgeTypeError(Exception):
    """Raised when edge type is invalid for the given node types."""

    pass


class DatabaseService:
    """Service for managing the LanceDB graph storage."""

    def __init__(self):
        settings = get_settings()
        self.db_path = settings.lancedb_path
        self._db: lancedb.DBConnection | None = None
        self._nodes_table: lancedb.table.Table | None = None
        self._edges_table: lancedb.table.Table | None = None

    def _ensure_directory(self) -> None:
        """Ensure the database directory exists."""
        Path(self.db_path).mkdir(parents=True, exist_ok=True)

    @property
    def db(self) -> lancedb.DBConnection:
        """Get or create the database connection."""
        if self._db is None:
            self._ensure_directory()
            self._db = lancedb.connect(str(self.db_path))
        return self._db

    @property
    def nodes_table(self) -> lancedb.table.Table:
        """Get or create the nodes table."""
        if self._nodes_table is None:
            table_names = self.db.table_names()
            if "nodes" in table_names:
                self._nodes_table = self.db.open_table("nodes")
            else:
                # Create table with schema using pyarrow
                schema = pa.schema([
                    pa.field("id", pa.string()),
                    pa.field("type", pa.string()),
                    pa.field("content", pa.string()),
                    pa.field("created_at", pa.string()),
                    pa.field("updated_at", pa.string()),
                    pa.field("metadata_json", pa.string()),
                    pa.field("status", pa.string()),
                    pa.field("due_date", pa.string()),
                    pa.field("priority", pa.int64()),
                    pa.field("title", pa.string()),
                    pa.field("tags_json", pa.string()),
                    pa.field("source", pa.string()),
                    pa.field("vector", pa.list_(pa.float32(), 1024)),
                ])
                self._nodes_table = self.db.create_table("nodes", schema=schema)
        return self._nodes_table

    @property
    def edges_table(self) -> lancedb.table.Table:
        """Get or create the edges table."""
        if self._edges_table is None:
            table_names = self.db.table_names()
            if "edges" in table_names:
                self._edges_table = self.db.open_table("edges")
            else:
                # Create table with schema using pyarrow
                schema = pa.schema([
                    pa.field("source_id", pa.string()),
                    pa.field("target_id", pa.string()),
                    pa.field("edge_type", pa.string()),
                    pa.field("created_at", pa.string()),
                ])
                self._edges_table = self.db.create_table("edges", schema=schema)
        return self._edges_table

    # ==================== Node Operations ====================

    def _node_to_record(self, node: GraphNode) -> dict:
        """Convert a GraphNode to a LanceDB record dict."""
        import json

        record = {
            "id": node.id,
            "type": node.type.value,
            "content": node.content,
            "created_at": node.created_at.isoformat(),
            "updated_at": node.updated_at.isoformat(),
            "metadata_json": json.dumps(node.metadata),
            "vector": node.embedding,
        }

        if isinstance(node, Event):
            record["status"] = node.status.value
            record["due_date"] = node.due_date.isoformat() if node.due_date else None
            record["priority"] = node.priority
        elif isinstance(node, Note):
            record["title"] = node.title
            record["tags_json"] = json.dumps(node.tags)
            record["source"] = node.source

        return record

    def _record_to_node(self, record: dict) -> GraphNode:
        """Convert a LanceDB record to a GraphNode."""
        import json

        node_type = NodeType(record["type"])
        metadata = json.loads(record["metadata_json"]) if record["metadata_json"] else {}

        if node_type == NodeType.EVENT:
            return Event(
                id=record["id"],
                type=node_type,
                content=record["content"],
                created_at=datetime.fromisoformat(record["created_at"]),
                updated_at=datetime.fromisoformat(record["updated_at"]),
                metadata=metadata,
                embedding=record.get("vector"),
                status=EventStatus(record["status"]) if record.get("status") else EventStatus.PENDING,
                due_date=datetime.fromisoformat(record["due_date"]) if record.get("due_date") else None,
                priority=record.get("priority", 0),
            )
        else:
            tags = json.loads(record["tags_json"]) if record.get("tags_json") else []
            return Note(
                id=record["id"],
                type=node_type,
                content=record["content"],
                created_at=datetime.fromisoformat(record["created_at"]),
                updated_at=datetime.fromisoformat(record["updated_at"]),
                metadata=metadata,
                embedding=record.get("vector"),
                title=record.get("title", ""),
                tags=tags,
                source=record.get("source"),
            )

    def add_node(self, node: GraphNode) -> GraphNode:
        """Add a node to the database."""
        record = self._node_to_record(node)
        self.nodes_table.add([record])
        return node

    def get_node(self, node_id: str) -> GraphNode | None:
        """Get a node by ID."""
        results = self.nodes_table.search().where(f"id = '{node_id}'").limit(1).to_list()
        if not results:
            return None
        return self._record_to_node(results[0])

    def update_node(self, node: GraphNode) -> GraphNode:
        """Update a node in the database."""
        node.updated_at = datetime.now()
        # LanceDB doesn't have native update, so we delete and re-add
        self.delete_node(node.id)
        return self.add_node(node)

    def delete_node(self, node_id: str) -> bool:
        """Delete a node and its related edges."""
        # Delete related edges first
        self.edges_table.delete(f"source_id = '{node_id}' OR target_id = '{node_id}'")
        # Delete the node
        self.nodes_table.delete(f"id = '{node_id}'")
        return True

    def get_all_nodes(self, node_type: NodeType | None = None) -> list[GraphNode]:
        """Get all nodes, optionally filtered by type."""
        try:
            if self.nodes_table.count_rows() == 0:
                return []
            if node_type:
                results = self.nodes_table.search().where(f"type = '{node_type.value}'").to_list()
            else:
                results = self.nodes_table.to_pandas().to_dict("records")
            return [self._record_to_node(r) for r in results]
        except Exception:
            return []

    def get_events(self, status: EventStatus | None = None) -> list[Event]:
        """Get all events, optionally filtered by status."""
        try:
            if self.nodes_table.count_rows() == 0:
                return []
            query = f"type = '{NodeType.EVENT.value}'"
            if status:
                query += f" AND status = '{status.value}'"
            results = self.nodes_table.search().where(query).to_list()
            return [self._record_to_node(r) for r in results]  # type: ignore
        except Exception:
            return []

    def get_notes(self) -> list[Note]:
        """Get all notes."""
        try:
            if self.nodes_table.count_rows() == 0:
                return []
            results = self.nodes_table.search().where(f"type = '{NodeType.NOTE.value}'").to_list()
            return [self._record_to_node(r) for r in results]  # type: ignore
        except Exception:
            return []

    # ==================== Edge Operations ====================

    def _edge_to_record(self, edge: Edge) -> dict:
        """Convert an Edge to a LanceDB record dict."""
        return {
            "source_id": edge.source_id,
            "target_id": edge.target_id,
            "edge_type": edge.edge_type.value,
            "created_at": edge.created_at.isoformat(),
        }

    def _record_to_edge(self, record: dict) -> Edge:
        """Convert a LanceDB record to an Edge."""
        return Edge(
            source_id=record["source_id"],
            target_id=record["target_id"],
            edge_type=EdgeType(record["edge_type"]),
            created_at=datetime.fromisoformat(record["created_at"]),
        )

    def _validate_edge(self, source: GraphNode, target: GraphNode, edge_type: EdgeType) -> None:
        """Validate that an edge type is valid for the given node types."""
        key = (source.type, target.type)
        valid_types = VALID_EDGE_TYPES.get(key, [])
        if edge_type not in valid_types:
            raise InvalidEdgeTypeError(
                f"Edge type {edge_type.value} is not valid for "
                f"{source.type.value} -> {target.type.value}"
            )

    def _has_path(self, from_id: str, to_id: str, edge_type: EdgeType) -> bool:
        """Check if there's a path from from_id to to_id using edges of the given type."""
        try:
            if self.edges_table.count_rows() == 0:
                return False
        except Exception:
            return False

        visited = set()
        stack = [from_id]

        while stack:
            current = stack.pop()
            if current == to_id:
                return True
            if current in visited:
                continue
            visited.add(current)

            # Get outgoing edges of the specified type
            try:
                edges = self.edges_table.search().where(
                    f"source_id = '{current}' AND edge_type = '{edge_type.value}'"
                ).to_list()
                for edge in edges:
                    stack.append(edge["target_id"])
            except Exception:
                pass

        return False

    def add_edge(self, edge: Edge) -> Edge:
        """Add an edge to the database with validation."""
        source = self.get_node(edge.source_id)
        target = self.get_node(edge.target_id)

        if not source:
            raise ValueError(f"Source node {edge.source_id} not found")
        if not target:
            raise ValueError(f"Target node {edge.target_id} not found")

        # Validate edge type
        self._validate_edge(source, target, edge.edge_type)

        # Check for cycles in DEPENDS_ON edges
        if edge.edge_type == EdgeType.DEPENDS_ON:
            if self._has_path(edge.target_id, edge.source_id, EdgeType.DEPENDS_ON):
                raise CyclicDependencyError(
                    f"Adding edge would create a cycle: {edge.source_id} -> {edge.target_id}"
                )

        record = self._edge_to_record(edge)
        self.edges_table.add([record])
        return edge

    def get_edges(
        self,
        source_id: str | None = None,
        target_id: str | None = None,
        edge_type: EdgeType | None = None,
    ) -> list[Edge]:
        """Get edges with optional filters."""
        try:
            if self.edges_table.count_rows() == 0:
                return []
            conditions = []
            if source_id:
                conditions.append(f"source_id = '{source_id}'")
            if target_id:
                conditions.append(f"target_id = '{target_id}'")
            if edge_type:
                conditions.append(f"edge_type = '{edge_type.value}'")

            if conditions:
                query = " AND ".join(conditions)
                results = self.edges_table.search().where(query).to_list()
            else:
                results = self.edges_table.to_pandas().to_dict("records")

            return [self._record_to_edge(r) for r in results]
        except Exception:
            return []

    def delete_edge(self, source_id: str, target_id: str, edge_type: EdgeType) -> bool:
        """Delete a specific edge."""
        self.edges_table.delete(
            f"source_id = '{source_id}' AND target_id = '{target_id}' AND edge_type = '{edge_type.value}'"
        )
        return True

    # ==================== Graph Traversal ====================

    def get_neighbors(
        self,
        node_id: str,
        edge_type: EdgeType | None = None,
        direction: str = "both",
    ) -> list[GraphNode]:
        """Get neighboring nodes connected by edges.

        Args:
            node_id: The node to find neighbors for
            edge_type: Filter by edge type (optional)
            direction: "outgoing", "incoming", or "both"
        """
        neighbor_ids = set()

        if direction in ("outgoing", "both"):
            edges = self.get_edges(source_id=node_id, edge_type=edge_type)
            for edge in edges:
                neighbor_ids.add(edge.target_id)

        if direction in ("incoming", "both"):
            edges = self.get_edges(target_id=node_id, edge_type=edge_type)
            for edge in edges:
                neighbor_ids.add(edge.source_id)

        neighbors = []
        for nid in neighbor_ids:
            node = self.get_node(nid)
            if node:
                neighbors.append(node)

        return neighbors

    def get_predecessors(self, node_id: str, edge_type: EdgeType | None = None) -> list[GraphNode]:
        """Get nodes that point to this node (incoming edges)."""
        return self.get_neighbors(node_id, edge_type, direction="incoming")

    def get_successors(self, node_id: str, edge_type: EdgeType | None = None) -> list[GraphNode]:
        """Get nodes this node points to (outgoing edges)."""
        return self.get_neighbors(node_id, edge_type, direction="outgoing")

    # ==================== Vector Search ====================

    def search_by_vector(
        self,
        query_vector: list[float],
        limit: int = 10,
        node_type: NodeType | None = None,
    ) -> list[tuple[GraphNode, float]]:
        """Search nodes by vector similarity.

        Returns list of (node, distance) tuples sorted by distance.
        """
        search = self.nodes_table.search(query_vector)
        if node_type:
            search = search.where(f"type = '{node_type.value}'")
        results = search.limit(limit).to_list()

        return [
            (self._record_to_node(r), r.get("_distance", 0.0))
            for r in results
        ]

    def search_by_content(
        self,
        query: str,
        limit: int = 10,
        node_type: NodeType | None = None,
    ) -> list[GraphNode]:
        """Search nodes by content using full-text search."""
        # LanceDB supports full-text search, but for now we use simple filtering
        query_lower = query.lower()
        all_nodes = self.get_all_nodes(node_type)
        matches = [
            node for node in all_nodes
            if query_lower in node.content.lower()
            or (isinstance(node, Note) and query_lower in node.title.lower())
        ]
        return matches[:limit]


# Singleton instance
_db_service: DatabaseService | None = None


def get_database_service() -> DatabaseService:
    """Get the singleton database service instance."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service
