"""Network communication protocols for the AtomCraft system.

This module defines the communication protocols and message formats
used between different components of the system.
"""

import struct
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Union

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.exceptions import NetworkException
from utils.logging_config import logger


class MessageType(Enum):
    """Enumeration of message types in the system."""
    COMMAND = "command"
    WAVEFORM = "waveform"
    SENSOR_DATA = "sensor_data"
    STATUS = "status"
    ACK = "acknowledgment"
    ERROR = "error"


@dataclass
class Message:
    """Standard message format for system communication."""
    
    message_type: MessageType
    payload: Any
    timestamp: Optional[float] = None
    sender: Optional[str] = None
    sequence_id: Optional[int] = None
    
    def to_bytes(self) -> bytes:
        """Convert message to bytes for transmission."""
        try:
            if isinstance(self.payload, str):
                return self.payload.encode('utf-8')
            elif isinstance(self.payload, (int, float)):
                return struct.pack('!f', float(self.payload))
            elif isinstance(self.payload, list):
                # For waveform data - join as space-separated string
                payload_str = ' '.join(str(x) for x in self.payload)
                return payload_str.encode('utf-8')
            else:
                # Default to string representation
                return str(self.payload).encode('utf-8')
                
        except Exception as e:
            raise NetworkException(f"Failed to serialize message: {e}")
    
    @classmethod
    def from_bytes(cls, data: bytes, message_type: MessageType) -> 'Message':
        """Create message from received bytes."""
        try:
            if message_type == MessageType.SENSOR_DATA:
                # Try to unpack as float first
                try:
                    payload = struct.unpack('!f', data)[0]
                except struct.error:
                    # Fall back to string decoding
                    payload = data.decode('utf-8')
            else:
                payload = data.decode('utf-8')
            
            return cls(message_type=message_type, payload=payload)
            
        except Exception as e:
            raise NetworkException(f"Failed to deserialize message: {e}")


class ProtocolHandler(ABC):
    """Abstract base class for protocol handlers."""
    
    @abstractmethod
    def send_message(self, message: Message, address: tuple) -> bool:
        """Send a message to the specified address."""
        pass
    
    @abstractmethod
    def receive_message(self) -> Optional[Message]:
        """Receive a message if available."""
        pass


class UDPProtocolHandler(ProtocolHandler):
    """UDP protocol handler for socket communication."""
    
    def __init__(self, socket_instance):
        """Initialize with a socket instance.
        
        Args:
            socket_instance: Configured UDP socket
        """
        self.socket = socket_instance
        self._sequence_counter = 0
        logger.debug("UDPProtocolHandler initialized")
    
    def send_message(self, message: Message, address: tuple) -> bool:
        """Send a message via UDP.
        
        Args:
            message: Message to send
            address: Target address (host, port)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add sequence ID if not present
            if message.sequence_id is None:
                message.sequence_id = self._sequence_counter
                self._sequence_counter += 1
            
            # Convert to bytes and send
            data = message.to_bytes()
            bytes_sent = self.socket.sendto(data, address)
            
            logger.debug(f"Sent {bytes_sent} bytes to {address}: {message.message_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to {address}: {e}")
            return False
    
    def receive_message(self, message_type: MessageType = None) -> Optional[Message]:
        """Receive a message via UDP.
        
        Args:
            message_type: Expected message type (for proper parsing)
            
        Returns:
            Received message or None if no data available
        """
        try:
            data, address = self.socket.recvfrom(1024)
            
            # If message type not specified, try to infer from context
            if message_type is None:
                message_type = MessageType.COMMAND  # Default assumption
            
            message = Message.from_bytes(data, message_type)
            message.sender = f"{address[0]}:{address[1]}"
            
            logger.debug(f"Received message from {address}: {message.message_type.value}")
            return message
            
        except Exception as e:
            logger.debug(f"No message received or parsing failed: {e}")
            return None


class CommandProtocol:
    """Handles command-specific protocol operations."""
    
    # Command categories
    SYSTEM_COMMANDS = {
        'clear', 'exit', 'status'
    }
    
    TEST_COMMANDS = {
        'temperature test', 'pressure test', 'solenoid test'
    }
    
    CONTROL_COMMANDS = {
        'start control loop', 'stop control loop'
    }
    
    SOLENOID_COMMANDS = {
        'solenoid open', 'solenoid close', 'solenoid pressure'
    }
    
    def __init__(self):
        """Initialize the command protocol."""
        self.all_commands = (
            self.SYSTEM_COMMANDS |
            self.TEST_COMMANDS |
            self.CONTROL_COMMANDS |
            self.SOLENOID_COMMANDS
        )
        logger.info("CommandProtocol initialized")
    
    def validate_command(self, command: str) -> bool:
        """Validate if a command is recognized.
        
        Args:
            command: Command string to validate
            
        Returns:
            True if command is valid
        """
        # Handle solenoid time commands specially
        if command.startswith('solenoid time '):
            try:
                time_value = command.split('solenoid time ')[1]
                float(time_value)  # Validate it's a number
                return True
            except (IndexError, ValueError):
                return False
        
        return command.lower() in self.all_commands
    
    def get_command_type(self, command: str) -> str:
        """Determine the category of a command.
        
        Args:
            command: Command string
            
        Returns:
            Command category string
        """
        command_lower = command.lower()
        
        if command_lower in self.SYSTEM_COMMANDS:
            return 'system'
        elif command_lower in self.TEST_COMMANDS:
            return 'test'
        elif command_lower in self.CONTROL_COMMANDS:
            return 'control'
        elif command_lower in self.SOLENOID_COMMANDS or command.startswith('solenoid'):
            return 'solenoid'
        else:
            return 'unknown'
    
    def get_help_text(self) -> str:
        """Get help text for available commands.
        
        Returns:
            Formatted help text
        """
        help_lines = [
            "Available Commands:",
            "",
            "System Commands:",
            "  clear - Clear command history",
            "  exit - Exit application gracefully",
            "  status - Show system status",
            "",
            "Test Commands:",
            "  temperature test - Start temperature monitoring",
            "  pressure test - Start pressure monitoring",
            "  solenoid test - Initialize solenoid system",
            "",
            "Control Commands:",
            "  start control loop - Begin current control with waveform",
            "  stop control loop - Stop current control",
            "",
            "Solenoid Commands:",
            "  solenoid open - Open solenoid valve",
            "  solenoid close - Close solenoid valve",
            "  solenoid pressure - Get pressure reading",
            "  solenoid time <ms> - Set valve open duration",
        ]
        
        return "\n".join(help_lines)


class DataPacket:
    """Represents a data packet for sensor readings."""
    
    def __init__(self, sensor_type: str, value: float, unit: str = "", status: str = "OK"):
        """Initialize a data packet.
        
        Args:
            sensor_type: Type of sensor data
            value: Sensor reading value
            unit: Unit of measurement
            status: Sensor status
        """
        self.sensor_type = sensor_type
        self.value = value
        self.unit = unit
        self.status = status
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert packet to dictionary."""
        return {
            'sensor_type': self.sensor_type,
            'value': self.value,
            'unit': self.unit,
            'status': self.status
        }
    
    def __str__(self) -> str:
        """String representation of the packet."""
        return f"{self.sensor_type}: {self.value} {self.unit} ({self.status})"
