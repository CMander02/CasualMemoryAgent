from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from openai import OpenAI

from app.core.config import get_settings
from app.models.chat import Message
from app.models.graph import GraphNode, Note


class BaseAgent(ABC):
    """Base class for all agents using DeepSeek API."""

    def __init__(self, model: str | None = None):
        settings = get_settings()
        self.client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
        self.model = model or settings.deepseek_model
        self.max_tokens = settings.max_tokens

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass

    def _format_messages(self, messages: list[Message]) -> list[dict[str, str]]:
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    async def chat(self, messages: list[Message]) -> Message:
        """Send messages and get a response."""
        formatted_messages = [
            {"role": "system", "content": self.system_prompt},
            *self._format_messages(messages),
        ]
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=formatted_messages,
        )
        return Message(
            role="assistant",
            content=response.choices[0].message.content or "",
        )

    async def stream(self, messages: list[Message]) -> AsyncGenerator[str, None]:
        """Stream responses token by token."""
        formatted_messages = [
            {"role": "system", "content": self.system_prompt},
            *self._format_messages(messages),
        ]
        stream = self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=formatted_messages,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class ChatAgent(BaseAgent):
    """A simple chat agent."""

    @property
    def system_prompt(self) -> str:
        return "You are a helpful assistant. Be concise and clear in your responses."


class MemoryAugmentedAgent(BaseAgent):
    """An agent that uses the memory graph for context-aware responses."""

    def __init__(self, model: str | None = None, memory_context: list[GraphNode] | None = None):
        super().__init__(model)
        self.memory_context = memory_context or []

    @property
    def system_prompt(self) -> str:
        base_prompt = """You are a helpful assistant with access to a memory system.
You can recall relevant information from past conversations and notes.
Be concise, clear, and reference relevant context when available."""

        if not self.memory_context:
            return base_prompt

        # Build context from memory nodes
        context_parts = [base_prompt, "\n\n## Relevant Context from Memory:\n"]

        for node in self.memory_context:
            if isinstance(node, Note):
                context_parts.append(f"### {node.title or 'Note'}\n{node.content}\n")
            else:
                context_parts.append(f"### Memory\n{node.content}\n")

        return "".join(context_parts)

    def set_memory_context(self, nodes: list[GraphNode]) -> None:
        """Update the memory context."""
        self.memory_context = nodes

    async def chat_with_memory(
        self,
        messages: list[Message],
        memory_nodes: list[GraphNode],
    ) -> Message:
        """Chat with memory context injected."""
        self.set_memory_context(memory_nodes)
        return await self.chat(messages)

    async def stream_with_memory(
        self,
        messages: list[Message],
        memory_nodes: list[GraphNode],
    ) -> AsyncGenerator[str, None]:
        """Stream response with memory context injected."""
        self.set_memory_context(memory_nodes)
        async for token in self.stream(messages):
            yield token
