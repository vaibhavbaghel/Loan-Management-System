"""
Event schemas for inter-service communication.
Events are published to RabbitMQ/Redis and consumed by subscribers.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json


class EventType(str, Enum):
    """Event types for different microservices."""
    # User service events
    USER_CREATED = "user.created"
    USER_APPROVED = "user.approved"
    AGENT_APPROVED = "agent.approved"
    AGENT_REJECTED = "agent.rejected"
    
    # Loan service events
    LOAN_CREATED = "loan.created"
    LOAN_APPROVED = "loan.approved"
    LOAN_REJECTED = "loan.rejected"
    LOAN_EDITED = "loan.edited"


@dataclass
class Event:
    """Base event class."""
    event_type: EventType
    service: str  # e.g., "user-service", "loan-service"
    timestamp: str = None
    data: Dict[str, Any] = None
    correlation_id: Optional[str] = None  # For tracing across services
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
        if self.data is None:
            self.data = {}
    
    def to_json(self) -> str:
        """Serialize event to JSON."""
        return json.dumps({
            'event_type': self.event_type,
            'service': self.service,
            'timestamp': self.timestamp,
            'data': self.data,
            'correlation_id': self.correlation_id
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Event':
        """Deserialize event from JSON."""
        data = json.loads(json_str)
        return cls(
            event_type=data['event_type'],
            service=data['service'],
            timestamp=data.get('timestamp'),
            data=data.get('data'),
            correlation_id=data.get('correlation_id')
        )


# User Service Events
@dataclass
class UserCreatedEvent(Event):
    """Published when a new user is created."""
    def __init__(self, user_id: str, email: str, is_customer: bool, is_agent: bool, **kwargs):
        super().__init__(
            event_type=EventType.USER_CREATED,
            service="user-service",
            data={
                'user_id': user_id,
                'email': email,
                'is_customer': is_customer,
                'is_agent': is_agent
            },
            **kwargs
        )


@dataclass
class AgentApprovedEvent(Event):
    """Published when an agent is approved."""
    def __init__(self, user_id: str, email: str, **kwargs):
        super().__init__(
            event_type=EventType.AGENT_APPROVED,
            service="user-service",
            data={
                'user_id': user_id,
                'email': email
            },
            **kwargs
        )


# Loan Service Events
@dataclass
class LoanCreatedEvent(Event):
    """Published when a new loan is created."""
    def __init__(self, loan_id: str, customer_id: str, agent_id: str, principal: float, **kwargs):
        super().__init__(
            event_type=EventType.LOAN_CREATED,
            service="loan-service",
            data={
                'loan_id': loan_id,
                'customer_id': customer_id,
                'agent_id': agent_id,
                'principal': principal
            },
            **kwargs
        )


@dataclass
class LoanApprovedEvent(Event):
    """Published when a loan is approved."""
    def __init__(self, loan_id: str, customer_id: str, **kwargs):
        super().__init__(
            event_type=EventType.LOAN_APPROVED,
            service="loan-service",
            data={
                'loan_id': loan_id,
                'customer_id': customer_id
            },
            **kwargs
        )
