"""
Event bus interface for publishing and consuming events.
Implementations can use RabbitMQ, Redis, or other brokers.
"""
import os
import json
from abc import ABC, abstractmethod
from typing import Callable, Dict
from .event_schemas import Event, EventType


class EventBus(ABC):
    """Abstract base class for event bus implementations."""
    
    @abstractmethod
    def publish(self, event: Event) -> None:
        """Publish an event to the bus."""
        pass
    
    @abstractmethod
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Subscribe to an event type."""
        pass
    
    @abstractmethod
    def consume(self) -> None:
        """Start consuming events (blocking call)."""
        pass


class InMemoryEventBus(EventBus):
    """
    Simple in-memory event bus for development and testing.
    Not suitable for production as events are lost on service restart.
    """
    
    def __init__(self):
        self.subscribers: Dict[EventType, list] = {}
    
    def publish(self, event: Event) -> None:
        """Publish event to in-memory subscribers."""
        if event.event_type in self.subscribers:
            for handler in self.subscribers[event.event_type]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"Error processing event {event.event_type}: {str(e)}")
    
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Register handler for an event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
    
    def consume(self) -> None:
        """In-memory bus doesn't need explicit consume."""
        pass


class RabbitMQEventBus(EventBus):
    """
    Event bus implementation using RabbitMQ.
    Recommended for production environments.
    """
    
    def __init__(self, broker_url: str = None):
        try:
            import pika
        except ImportError:
            raise ImportError("pika not installed. Run: pip install pika")
        
        self.broker_url = broker_url or os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
        self.connection = None
        self.channel = None
        self._connect()
    
    def _connect(self):
        """Establish connection to RabbitMQ."""
        try:
            import pika
            self.connection = pika.BlockingConnection(pika.URLParameters(self.broker_url))
            self.channel = self.connection.channel()
        except Exception as e:
            print(f"Failed to connect to RabbitMQ: {str(e)}")
            raise
    
    def publish(self, event: Event) -> None:
        """Publish event to RabbitMQ exchange."""
        try:
            self.channel.exchange_declare(exchange='microservices', exchange_type='topic', durable=True)
            routing_key = f"service.{event.event_type}"
            self.channel.basic_publish(
                exchange='microservices',
                routing_key=routing_key,
                body=event.to_json(),
                properties=__import__('pika').BasicProperties(delivery_mode=2)
            )
            print(f"Event published: {event.event_type}")
        except Exception as e:
            print(f"Failed to publish event: {str(e)}")
            raise
    
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Subscribe to events of a specific type."""
        self.channel.exchange_declare(exchange='microservices', exchange_type='topic', durable=True)
        result = self.channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        routing_key = f"service.{event_type}"
        self.channel.queue_bind(exchange='microservices', queue=queue_name, routing_key=routing_key)
        
        def on_message(ch, method, properties, body):
            try:
                event = Event.from_json(body.decode())
                handler(event)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f"Error processing event: {str(e)}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        self.channel.basic_consume(queue=queue_name, on_message_callback=on_message)
    
    def consume(self) -> None:
        """Start consuming from RabbitMQ."""
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
            self.connection.close()


def get_event_bus() -> EventBus:
    """
    Factory function to get appropriate event bus based on environment.
    """
    bus_type = os.getenv("EVENT_BUS_TYPE", "memory")  # "memory", "rabbitmq", "redis"
    
    if bus_type == "rabbitmq":
        return RabbitMQEventBus()
    elif bus_type == "redis":
        # TODO: Implement Redis event bus
        raise NotImplementedError("Redis event bus not yet implemented")
    else:
        return InMemoryEventBus()
