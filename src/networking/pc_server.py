"""PC-side network server for the AtomCraft system.

This module handles all network communication from the PC side,
including receiving sensor data and sending commands to remote devices.
"""

import contextlib
import socket
import threading
import time
from typing import Callable, Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import NETWORK
from core.data_manager import SensorDataBuffer
from networking.protocols import Message, MessageType, UDPProtocolHandler
from utils.exceptions import NetworkException
from utils.logging_config import logger


class NetworkServer:
    """Manages network communication for the PC side of the system.
    
    This class handles multiple UDP sockets for different data streams
    and coordinates communication with PYNQ and Arduino devices.
    """
    
    def __init__(self, data_buffer: SensorDataBuffer):
        """Initialize the network server.
        
        Args:
            data_buffer: Shared data buffer for sensor readings
        """
        self.data_buffer = data_buffer
        self.config = NETWORK
        self._running = False
        self._threads = []
        self._sockets = {}
        
        # Callback functions for different data types
        self._callbacks = {}
        
        logger.info("NetworkServer initialized")
    
    def register_callback(self, data_type: str, callback: Callable) -> None:
        """Register a callback function for specific data types.
        
        Args:
            data_type: Type of data ('tf_current', 'temperature', etc.)
            callback: Function to call when data is received
        """
        self._callbacks[data_type] = callback
        logger.debug(f"Registered callback for {data_type}")
    
    def start(self) -> None:
        """Start all network receivers."""
        if self._running:
            logger.warning("NetworkServer already running")
            return
        
        self._running = True
        
        # Start individual receiver threads
        self._start_tf_current_receiver()
        self._start_temperature_receiver()
        self._start_pressure_receiver()
        self._start_solenoid_receiver()
        
        logger.info("NetworkServer started - all receivers active")
    
    def stop(self) -> None:
        """Stop all network receivers and close sockets."""
        if not self._running:
            return
        
        self._running = False
        
        # Close all sockets
        for socket_name, sock in self._sockets.items():
            try:
                sock.close()
                logger.debug(f"Closed socket: {socket_name}")
            except Exception as e:
                logger.error(f"Error closing socket {socket_name}: {e}")
        
        # Wait for threads to finish
        for thread in self._threads:
            if thread.is_alive():
                thread.join(timeout=2.0)
        
        self._sockets.clear()
        self._threads.clear()
        
        logger.info("NetworkServer stopped")
    
    def _create_receiver_socket(self, port: int, name: str) -> socket.socket:
        """Create and configure a UDP receiver socket.
        
        Args:
            port: Port number to bind to
            name: Socket name for logging
            
        Returns:
            Configured socket
            
        Raises:
            NetworkException: If socket creation fails
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((self.config.LOCAL_HOST, port))
            sock.settimeout(self.config.SOCKET_TIMEOUT)
            
            self._sockets[name] = sock
            logger.debug(f"Created receiver socket '{name}' on port {port}")
            return sock
            
        except Exception as e:
            raise NetworkException(f"Failed to create socket '{name}' on port {port}: {e}")
    
    def _start_tf_current_receiver(self) -> None:
        """Start TF coil current data receiver."""
        def receiver_thread():
            sock = self._create_receiver_socket(
                self.config.TF_CURRENT_RX_PORT,
                "tf_current"
            )
            protocol = UDPProtocolHandler(sock)
            
            logger.info(f"TF current receiver listening on port {self.config.TF_CURRENT_RX_PORT}")
            
            while self._running:
                try:
                    with contextlib.suppress(socket.timeout):
                        message = protocol.receive_message(MessageType.SENSOR_DATA)
                        if message and isinstance(message.payload, (int, float)):
                            value = float(message.payload)
                            self.data_buffer.add_tf_current(value)
                            
                            # Call registered callback if available
                            if 'tf_current' in self._callbacks:
                                self._callbacks['tf_current'](value)
                            
                            logger.debug(f"Received TF current: {value}")
                            
                except Exception as e:
                    logger.error(f"Error in TF current receiver: {e}")
        
        thread = threading.Thread(target=receiver_thread, name="TFCurrentReceiver")
        thread.daemon = True
        thread.start()
        self._threads.append(thread)
    
    def _start_temperature_receiver(self) -> None:
        """Start temperature data receiver."""
        def receiver_thread():
            sock = self._create_receiver_socket(
                self.config.TEMPERATURE_RX_PORT,
                "temperature"
            )
            protocol = UDPProtocolHandler(sock)
            
            logger.info(f"Temperature receiver listening on port {self.config.TEMPERATURE_RX_PORT}")
            
            while self._running:
                try:
                    with contextlib.suppress(socket.timeout):
                        message = protocol.receive_message(MessageType.SENSOR_DATA)
                        if message:
                            try:
                                # Handle both string and numeric temperature data
                                if isinstance(message.payload, str):
                                    value = float(message.payload)
                                else:
                                    value = float(message.payload)
                                
                                self.data_buffer.add_temperature(value)
                                
                                # Call registered callback if available
                                if 'temperature' in self._callbacks:
                                    self._callbacks['temperature'](value)
                                
                                logger.debug(f"Received temperature: {value}")
                                
                            except ValueError as e:
                                logger.warning(f"Invalid temperature data: {message.payload}")
                            
                except Exception as e:
                    logger.error(f"Error in temperature receiver: {e}")
        
        thread = threading.Thread(target=receiver_thread, name="TemperatureReceiver")
        thread.daemon = True
        thread.start()
        self._threads.append(thread)
    
    def _start_pressure_receiver(self) -> None:
        """Start pressure data receiver."""
        def receiver_thread():
            sock = self._create_receiver_socket(
                self.config.PRESSURE_RX_PORT,
                "pressure"
            )
            protocol = UDPProtocolHandler(sock)
            
            logger.info(f"Pressure receiver listening on port {self.config.PRESSURE_RX_PORT}")
            
            while self._running:
                try:
                    with contextlib.suppress(socket.timeout):
                        message = protocol.receive_message(MessageType.SENSOR_DATA)
                        if message:
                            try:
                                value = float(message.payload)
                                self.data_buffer.add_pressure(value)
                                
                                # Call registered callback if available
                                if 'pressure' in self._callbacks:
                                    self._callbacks['pressure'](value)
                                
                                logger.debug(f"Received pressure: {value}")
                                
                            except ValueError:
                                logger.warning(f"Invalid pressure data: {message.payload}")
                            
                except Exception as e:
                    logger.error(f"Error in pressure receiver: {e}")
        
        thread = threading.Thread(target=receiver_thread, name="PressureReceiver")
        thread.daemon = True
        thread.start()
        self._threads.append(thread)
    
    def _start_solenoid_receiver(self) -> None:
        """Start solenoid data receiver."""
        def receiver_thread():
            sock = self._create_receiver_socket(
                self.config.SOLENOID_PORT + 1,  # Different port for receiving
                "solenoid"
            )
            protocol = UDPProtocolHandler(sock)
            
            logger.info(f"Solenoid receiver listening on port {self.config.SOLENOID_PORT + 1}")
            
            while self._running:
                try:
                    with contextlib.suppress(socket.timeout):
                        message = protocol.receive_message(MessageType.SENSOR_DATA)
                        if message and isinstance(message.payload, str):
                            # Parse solenoid data: "pressure,status"
                            parts = message.payload.split(',')
                            if len(parts) >= 2:
                                try:
                                    pressure = float(parts[0])
                                    status = parts[1].strip()
                                    
                                    self.data_buffer.add_solenoid_pressure(pressure, status)
                                    
                                    # Call registered callback if available
                                    if 'solenoid' in self._callbacks:
                                        self._callbacks['solenoid'](pressure, status)
                                    
                                    logger.debug(f"Received solenoid data: {pressure}, {status}")
                                    
                                except ValueError:
                                    logger.warning(f"Invalid solenoid pressure: {parts[0]}")
                            
                except Exception as e:
                    logger.error(f"Error in solenoid receiver: {e}")
        
        thread = threading.Thread(target=receiver_thread, name="SolenoidReceiver")
        thread.daemon = True
        thread.start()
        self._threads.append(thread)


class NetworkClient:
    """Handles outgoing network communication from the PC.
    
    This class manages sending commands and data to remote devices.
    """
    
    def __init__(self):
        """Initialize the network client."""
        self.config = NETWORK
        logger.info("NetworkClient initialized")
    
    def send_command(self, command: str, timeout: float = 2.0) -> bool:
        """Send a command to the PYNQ device.
        
        Args:
            command: Command string to send
            timeout: Socket timeout in seconds
            
        Returns:
            True if command sent successfully
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            
            message = Message(MessageType.COMMAND, command)
            protocol = UDPProtocolHandler(sock)
            
            address = (self.config.LOCAL_HOST, self.config.COMMAND_TX_PORT)
            success = protocol.send_message(message, address)
            
            sock.close()
            
            if success:
                logger.info(f"Sent command: {command}")
            else:
                logger.error(f"Failed to send command: {command}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending command '{command}': {e}")
            return False
    
    def send_waveform(self, waveform_data: list, timeout: float = 2.0) -> bool:
        """Send waveform data to the PYNQ device.
        
        Args:
            waveform_data: List of waveform values
            timeout: Socket timeout in seconds
            
        Returns:
            True if waveform sent successfully
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            
            message = Message(MessageType.WAVEFORM, waveform_data)
            protocol = UDPProtocolHandler(sock)
            
            address = (self.config.LOCAL_HOST, self.config.WAVEFORM_TX_PORT)
            success = protocol.send_message(message, address)
            
            sock.close()
            
            if success:
                logger.info(f"Sent waveform data: {len(waveform_data)} points")
            else:
                logger.error("Failed to send waveform data")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending waveform: {e}")
            return False
    
    def send_solenoid_command(self, command: str, timeout: float = 2.0) -> Optional[str]:
        """Send a command to the Arduino solenoid controller.
        
        Args:
            command: Solenoid command to send
            timeout: Socket timeout in seconds
            
        Returns:
            Response from Arduino or None if failed
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            
            message = Message(MessageType.COMMAND, command)
            protocol = UDPProtocolHandler(sock)
            
            # Send command
            address = (self.config.ARDUINO_HOST, self.config.SOLENOID_PORT)
            if not protocol.send_message(message, address):
                sock.close()
                return None
            
            # Wait for acknowledgment
            response_msg = protocol.receive_message(MessageType.ACK)
            sock.close()
            
            if response_msg:
                logger.info(f"Solenoid command '{command}' acknowledged: {response_msg.payload}")
                return str(response_msg.payload)
            else:
                logger.warning(f"No acknowledgment for solenoid command: {command}")
                return None
                
        except Exception as e:
            logger.error(f"Error sending solenoid command '{command}': {e}")
            return None
