"""Chat API endpoints with optional memory augmentation."""

import json

from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.agents.base import ChatAgent, MemoryAugmentedAgent
from app.models.chat import ChatRequest, ChatResponse
from app.services import get_memory_graph

router = APIRouter(prefix="/chat", tags=["chat"])


class MemoryChatRequest(ChatRequest):
    """Chat request with memory augmentation options."""

    use_memory: bool = False
    memory_limit: int = 5


@router.post("", response_model=ChatResponse)
async def chat(request: MemoryChatRequest):
    """Send a chat message and get a response.

    If use_memory is True, relevant context from the memory graph
    will be injected into the conversation.
    """
    if request.use_memory:
        # Get the last user message for context search
        last_user_msg = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                last_user_msg = msg.content
                break

        memory_context = []
        if last_user_msg:
            graph = get_memory_graph()
            memory_context = await graph.search(
                last_user_msg,
                limit=request.memory_limit,
                rerank=True,
            )

        agent = MemoryAugmentedAgent(model=request.model, memory_context=memory_context)
    else:
        agent = ChatAgent(model=request.model)

    response = await agent.chat(request.messages)
    return ChatResponse(message=response)


@router.post("/stream")
async def chat_stream(request: MemoryChatRequest):
    """Stream a chat response using Server-Sent Events.

    If use_memory is True, relevant context from the memory graph
    will be injected into the conversation.
    """
    # Prepare memory context if needed
    memory_context = []
    if request.use_memory:
        last_user_msg = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                last_user_msg = msg.content
                break

        if last_user_msg:
            graph = get_memory_graph()
            memory_context = await graph.search(
                last_user_msg,
                limit=request.memory_limit,
                rerank=True,
            )

    if request.use_memory:
        agent = MemoryAugmentedAgent(model=request.model, memory_context=memory_context)
    else:
        agent = ChatAgent(model=request.model)

    async def generate():
        async for token in agent.stream(request.messages):
            yield {"data": json.dumps({"content": token})}
        yield {"data": "[DONE]"}

    return EventSourceResponse(generate())


class SaveToMemoryRequest(BaseModel):
    """Request to save chat content to memory."""

    content: str
    title: str = ""
    tags: list[str] = []


@router.post("/save-to-memory")
async def save_chat_to_memory(request: SaveToMemoryRequest):
    """Save chat content as a note in the memory graph."""
    from app.models.graph import NoteCreate

    graph = get_memory_graph()
    note = await graph.create_note(
        NoteCreate(
            content=request.content,
            title=request.title,
            tags=request.tags,
        )
    )
    return {
        "message": "Saved to memory",
        "note_id": note.id,
    }
