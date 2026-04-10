"""
V6 Agent Communication System

This module implements advanced communication protocols for V6 specialized agents,
enabling seamless coordination, context sharing, and collaborative task execution.

Author: Claude AI Assistant
Date: 2025-09-23
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime
import hashlib
import uuid

class MessageType(Enum):
    TASK_REQUEST = "task_request"
    TASK_STATUS = "task_status"
    CONTEXT_SHARE = "context_share"
    RESOURCE_REQUEST = "resource_request"
    COLLABORATION_INVITE = "collaboration_invite"
    KNOWLEDGE_SHARE = "knowledge_share"
    ERROR_REPORT = "error_report"
    PERFORMANCE_UPDATE = "performance_update"

class Priority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class AgentMessage:
    message_id: str
    sender_id: str
    recipient_id: str
    message_type: MessageType
    content: Dict[str, Any]
    priority: Priority
    timestamp: datetime
    correlation_id: Optional[str] = None
    requires_response: bool = False
    ttl: int = 300  # Time to live in seconds

@dataclass
class SharedContext:
    context_id: str
    owner_id: str
    data: Dict[str, Any]
    access_list: Set[str] = field(default_factory=set)
    created_at: datetime
    expires_at: datetime
    tags: List[str] = field(default_factory=list)

class AgentCommunicationBus:
    """Central communication bus for agent inter-communication"""

    def __init__(self):
        self.message_queue = asyncio.Queue()
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.shared_contexts: Dict[str, SharedContext] = {}
        self.active_agents: Set[str] = set()
        self.message_history: List[AgentMessage] = []
        self.delivery_confirmations: Dict[str, Set[str]] = {}

        # Performance metrics
        self.metrics = {
            "messages_sent": 0,
            "messages_delivered": 0,
            "average_delivery_time": 0.0,
            "context_shares": 0,
            "collaboration_requests": 0
        }

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def start(self):
        """Start the communication bus"""
        asyncio.create_task(self._message_processor())
        asyncio.create_task(self._context_cleaner())
        self.logger.info("Agent Communication Bus started")

    async def send_message(self, message: AgentMessage) -> bool:
        """Send a message to another agent"""
        try:
            # Validate message
            if not self._validate_message(message):
                return False

            # Add to queue
            await self.message_queue.put(message)
            self.metrics["messages_sent"] += 1

            # Add to history
            self.message_history.append(message)

            self.logger.debug(f"Message sent from {message.sender_id} to {message.recipient_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False

    async def broadcast_message(self, sender_id: str, message_type: MessageType,
                              content: Dict[str, Any], exclude_agents: List[str] = None) -> int:
        """Broadcast message to all active agents"""
        exclude_agents = exclude_agents or []
        recipients = [agent_id for agent_id in self.active_agents
                     if agent_id != sender_id and agent_id not in exclude_agents]

        sent_count = 0
        for recipient_id in recipients:
            message = AgentMessage(
                message_id=str(uuid.uuid4()),
                sender_id=sender_id,
                recipient_id=recipient_id,
                message_type=message_type,
                content=content,
                priority=Priority.NORMAL,
                timestamp=datetime.now()
            )

            if await self.send_message(message):
                sent_count += 1

        return sent_count

    async def share_context(self, owner_id: str, data: Dict[str, Any],
                          access_list: List[str] = None,
                          tags: List[str] = None,
                          ttl: int = 3600) -> str:
        """Share context with other agents"""
        context_id = hashlib.sha256(
            f"{owner_id}_{datetime.now().isoformat()}_{json.dumps(data, sort_keys=True)}".encode()
        ).hexdigest()[:16]

        context = SharedContext(
            context_id=context_id,
            owner_id=owner_id,
            data=data,
            access_list=set(access_list or []),
            created_at=datetime.now(),
            expires_at=datetime.now().plus(seconds=ttl),
            tags=tags or []
        )

        self.shared_contexts[context_id] = context
        self.metrics["context_shares"] += 1

        # Notify agents with access
        await self.broadcast_message(
            sender_id=owner_id,
            message_type=MessageType.CONTEXT_SHARE,
            content={
                "context_id": context_id,
                "owner_id": owner_id,
                "tags": tags or [],
                "expires_at": context.expires_at.isoformat()
            },
            exclude_agents=[owner_id]
        )

        self.logger.info(f"Context {context_id} shared by {owner_id}")
        return context_id

    async def request_collaboration(self, requester_id: str, target_agents: List[str],
                                  task_id: str, task_description: str,
                                  required_skills: List[str]) -> str:
        """Request collaboration from other agents"""
        correlation_id = str(uuid.uuid4())

        for target_id in target_agents:
            message = AgentMessage(
                message_id=str(uuid.uuid4()),
                sender_id=requester_id,
                recipient_id=target_id,
                message_type=MessageType.COLLABORATION_INVITE,
                content={
                    "task_id": task_id,
                    "task_description": task_description,
                    "required_skills": required_skills,
                    "correlation_id": correlation_id
                },
                priority=Priority.HIGH,
                timestamp=datetime.now(),
                requires_response=True,
                correlation_id=correlation_id
            )

            await self.send_message(message)

        self.metrics["collaboration_requests"] += 1
        return correlation_id

    async def register_agent(self, agent_id: str, message_handler: Callable):
        """Register an agent with the communication system"""
        self.active_agents.add(agent_id)
        if agent_id not in self.message_handlers:
            self.message_handlers[agent_id] = []
        self.message_handlers[agent_id].append(message_handler)

        self.logger.info(f"Agent {agent_id} registered")

    async def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        self.active_agents.discard(agent_id)
        self.message_handlers.pop(agent_id, None)

        self.logger.info(f"Agent {agent_id} unregistered")

    async def get_shared_context(self, context_id: str, requester_id: str) -> Optional[Dict[str, Any]]:
        """Get shared context if agent has access"""
        context = self.shared_contexts.get(context_id)
        if context and (requester_id in context.access_list or requester_id == context.owner_id):
            return context.data
        return None

    async def request_context_access(self, requester_id: str, context_id: str,
                                   reason: str) -> bool:
        """Request access to a shared context"""
        context = self.shared_contexts.get(context_id)
        if not context:
            return False

        # Send request to context owner
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            sender_id=requester_id,
            recipient_id=context.owner_id,
            message_type=MessageType.RESOURCE_REQUEST,
            content={
                "resource_type": "context_access",
                "context_id": context_id,
                "reason": reason
            },
            priority=Priority.NORMAL,
            timestamp=datetime.now(),
            requires_response=True
        )

        return await self.send_message(message)

    async def _message_processor(self):
        """Process messages from the queue"""
        while True:
            try:
                message = await self.message_queue.get()

                # Check TTL
                if (datetime.now() - message.timestamp).total_seconds() > message.ttl:
                    self.logger.warning(f"Message {message.message_id} expired")
                    continue

                # Deliver message
                await self._deliver_message(message)

                self.message_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Message processor error: {e}")

    async def _deliver_message(self, message: AgentMessage):
        """Deliver message to recipient"""
        recipient_id = message.recipient_id

        if recipient_id not in self.active_agents:
            self.logger.warning(f"Agent {recipient_id} not active")
            return

        # Get handlers for recipient
        handlers = self.message_handlers.get(recipient_id, [])

        # Deliver to all handlers
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                self.logger.error(f"Error in message handler for {recipient_id}: {e}")

        # Record delivery
        self.metrics["messages_delivered"] += 1
        delivery_time = (datetime.now() - message.timestamp).total_seconds()
        self.metrics["average_delivery_time"] = (
            (self.metrics["average_delivery_time"] * (self.metrics["messages_delivered"] - 1) + delivery_time) /
            self.metrics["messages_delivered"]
        )

    async def _context_cleaner(self):
        """Clean up expired contexts"""
        while True:
            try:
                current_time = datetime.now()
                expired_contexts = [
                    context_id for context_id, context in self.shared_contexts.items()
                    if current_time > context.expires_at
                ]

                for context_id in expired_contexts:
                    del self.shared_contexts[context_id]
                    self.logger.debug(f"Expired context {context_id} cleaned up")

                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Context cleaner error: {e}")

    def _validate_message(self, message: AgentMessage) -> bool:
        """Validate message structure and content"""
        if not message.sender_id or not message.recipient_id:
            return False

        if message.sender_id == message.recipient_id:
            return False

        if message.recipient_id not in self.active_agents:
            return False

        return True

    async def get_metrics(self) -> Dict[str, Any]:
        """Get communication system metrics"""
        return {
            **self.metrics,
            "active_agents": len(self.active_agents),
            "shared_contexts": len(self.shared_contexts),
            "message_history_size": len(self.message_history)
        }

class CollaborativeTaskManager:
    """Manages collaborative task execution among agents"""

    def __init__(self, communication_bus: AgentCommunicationBus):
        self.comm_bus = communication_bus
        self.collaborative_tasks: Dict[str, Dict[str, Any]] = {}
        self.agent_skills: Dict[str, Set[str]] = {}

    async def start_collaborative_task(self, task_id: str, task_description: str,
                                     required_skills: List[str],
                                     coordinator_id: str) -> Dict[str, Any]:
        """Start a collaborative task"""
        # Find agents with required skills
        candidate_agents = self._find_agents_with_skills(required_skills)

        if not candidate_agents:
            raise ValueError("No agents available with required skills")

        # Create collaborative task
        collaborative_task = {
            "task_id": task_id,
            "description": task_description,
            "coordinator": coordinator_id,
            "participants": candidate_agents,
            "required_skills": required_skills,
            "status": "initiating",
            "created_at": datetime.now().isoformat(),
            "subtasks": [],
            "results": {}
        }

        self.collaborative_tasks[task_id] = collaborative_task

        # Send collaboration requests
        correlation_id = await self.comm_bus.request_collaboration(
            requester_id=coordinator_id,
            target_agents=candidate_agents,
            task_id=task_id,
            task_description=task_description,
            required_skills=required_skills
        )

        collaborative_task["correlation_id"] = correlation_id

        return collaborative_task

    def _find_agents_with_skills(self, required_skills: List[str]) -> List[str]:
        """Find agents that have the required skills"""
        qualified_agents = []

        for agent_id, skills in self.agent_skills.items():
            if skill in skills for skill in required_skills:
                qualified_agents.append(agent_id)

        return qualified_agents

    async def handle_collaboration_response(self, response_message: AgentMessage):
        """Handle response to collaboration request"""
        correlation_id = response_message.content.get("correlation_id")
        response = response_message.content.get("response")

        # Find the collaborative task
        for task_id, task in self.collaborative_tasks.items():
            if task.get("correlation_id") == correlation_id:
                if response == "accept":
                    task["participants"].append(response_message.sender_id)
                    task["status"] = "in_progress"
                elif response == "decline":
                    if response_message.sender_id in task["participants"]:
                        task["participants"].remove(response_message.sender_id)

                break

    async def update_agent_skills(self, agent_id: str, skills: List[str]):
        """Update agent skills registry"""
        self.agent_skills[agent_id] = set(skills)

    async def get_collaborative_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a collaborative task"""
        return self.collaborative_tasks.get(task_id)