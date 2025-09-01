"""PYNQ-side client for the AtomCraft system (refactored).

This module provides the refactored PYNQ-side implementation with
improved structure and error handling.
"""

#!/usr/bin/env python3

import sys
import signal
import threading
import time
from pathlib import Path

import sys
import signal
import threading
import time
from pathlib import Path

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from networking.protocols import Message, MessageType, UDPProtocolHandler
from core.config import NETWORK, SIGNAL_PROCESSING
from core.signal_processor import WaveformProcessor
from utils.logging_config import logger
import socket
import contextlib
import random
import struct


class AtomCraftPYNQClient:
    """PYNQ-side client for the AtomCraft system.
    
    This class handles receiving commands from the PC and sending
    sensor data back to the PC.
    """
    
    def __init__(self):
        """Initialize the PYNQ client."""
        self.config = NETWORK
        self.waveform_processor = WaveformProcessor()
        self._running = False
        self._threads = []
        self._sockets = {}
        
        # Data storage
        self.current_waveform = []
        self.mapped_waveform = []
        
        self._setup_signal_handlers()
        logger.info("AtomCraftPYNQClient initialized")
    
    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def start(self) -> None:
        """Start all PYNQ client services."""
        if self._running:
            logger.warning("PYNQ client already running")
            return
        
        self._running = True
        
        # Start receiver threads
        self._start_command_receiver()
        self._start_waveform_receiver()
        
        logger.info("PYNQ client started - all services active")
    
    def stop(self) -> None:
        """Stop all PYNQ client services."""
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
        
        logger.info("PYNQ client stopped")
    
    def _create_receiver_socket(self, port: int, name: str) -> socket.socket:
        """Create and configure a UDP receiver socket.
        
        Args:
            port: Port number to bind to
            name: Socket name for logging
            
        Returns:
            Configured socket
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((self.config.LOCAL_HOST, port))
            sock.settimeout(self.config.SOCKET_TIMEOUT)
            
            self._sockets[name] = sock
            logger.debug(f"Created receiver socket '{name}' on port {port}")
            return sock
            
        except Exception as e:
            logger.error(f"Failed to create socket '{name}' on port {port}: {e}")
            raise
    
    def _start_command_receiver(self) -> None:
        """Start the command receiver thread."""
        def receiver_thread():
            sock = self._create_receiver_socket(
                self.config.COMMAND_TX_PORT,
                "command_receiver"
            )
            protocol = UDPProtocolHandler(sock)
            
            logger.info(f"Command receiver listening on port {self.config.COMMAND_TX_PORT}")
            
            while self._running:
                try:
                    with contextlib.suppress(socket.timeout):
                        message = protocol.receive_message(MessageType.COMMAND)
                        if message and isinstance(message.payload, str):
                            self._handle_command(message.payload)
                            
                except Exception as e:
                    logger.error(f"Error in command receiver: {e}")
        
        thread = threading.Thread(target=receiver_thread, name="CommandReceiver")
        thread.daemon = True
        thread.start()
        self._threads.append(thread)
    
    def _start_waveform_receiver(self) -> None:
        """Start the waveform receiver thread."""
        def receiver_thread():
            sock = self._create_receiver_socket(
                self.config.WAVEFORM_TX_PORT,
                "waveform_receiver"
            )
            protocol = UDPProtocolHandler(sock)
            
            logger.info(f"Waveform receiver listening on port {self.config.WAVEFORM_TX_PORT}")
            
            while self._running:
                try:
                    with contextlib.suppress(socket.timeout):
                        message = protocol.receive_message(MessageType.WAVEFORM)
                        if message and isinstance(message.payload, str):
                            self._handle_waveform_data(message.payload)
                            
                except Exception as e:
                    logger.error(f"Error in waveform receiver: {e}")
        
        thread = threading.Thread(target=receiver_thread, name="WaveformReceiver")
        thread.daemon = True
        thread.start()
        self._threads.append(thread)
    
    def _handle_command(self, command: str) -> None:
        """Handle received commands.
        
        Args:
            command: Command string to process
        """
        logger.info(f"Received command: {command}")
        
        command_lower = command.lower()
        
        if command_lower == "temperature test":
            self._start_temperature_test()
        elif command_lower == "pressure test":
            self._start_pressure_test()
        elif command_lower == "start control loop":
            logger.info("Control loop started - waiting for waveform data")
        else:
            logger.warning(f"Unknown command: {command}")
    
    def _handle_waveform_data(self, waveform_str: str) -> None:
        """Handle received waveform data.
        
        Args:
            waveform_str: Waveform data string
        """
        try:
            # Parse waveform data
            waveform_values = waveform_str.split()
            waveform_floats = [float(x) for x in waveform_values]
            
            logger.info(f"Received waveform data: {len(waveform_floats)} points")
            
            # Map waveform for hardware
            self.mapped_waveform = self._map_pynq_pmod(waveform_floats)
            
            # Drive the TF coil current
            self._drive_tf_current()
            
        except Exception as e:
            logger.error(f"Error processing waveform data: {e}")
    
    def _map_pynq_pmod(self, reference_current: list) -> list:
        """Map reference current to PMOD port values.
        
        Args:
            reference_current: Reference current values
            
        Returns:
            Mapped values for PMOD interface
        """
        try:
            min_value = 1
            max_value = 99
            min_x = min(reference_current)
            max_x = max(reference_current)
            
            if min_x == max_x:
                return [min_value] * len(reference_current)
            
            mapped = [
                min_value + (max_value - min_value) * (x - min_x) / (max_x - min_x)
                for x in reference_current
            ]
            
            logger.debug(f"Mapped waveform: {len(mapped)} points")
            return mapped
            
        except Exception as e:
            logger.error(f"Error mapping waveform: {e}")
            return reference_current  # Return original on error
    
    def _drive_tf_current(self) -> None:
        """Drive the TF coil current using mapped waveform."""
        if not self.mapped_waveform:
            logger.warning("No mapped waveform data available")
            return
        
        logger.info("Starting TF current control")
        
        # Start a thread to send the waveform data back to PC
        thread = threading.Thread(target=self._send_tf_current_data, name="TFCurrentSender")
        thread.daemon = True
        thread.start()
    
    def _send_tf_current_data(self) -> None:
        """Send TF current data back to PC."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            address = (self.config.LOCAL_HOST, self.config.TF_CURRENT_RX_PORT)
            
            logger.info(f"Sending TF current data to {address}")
            
            for value in self.mapped_waveform:
                if not self._running:
                    break
                
                try:
                    # Pack as binary float
                    packet = struct.pack('!f', float(value))
                    sock.sendto(packet, address)
                    
                    time.sleep(0.01)  # 10ms delay between points
                    
                except Exception as e:
                    logger.error(f"Error sending TF current data point: {e}")
            
            sock.close()
            logger.info("Finished sending TF current data")
            
        except Exception as e:
            logger.error(f"Error in TF current data sender: {e}")
    
    def _start_temperature_test(self) -> None:
        """Start temperature test data generation."""
        def temperature_sender():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                address = (self.config.LOCAL_HOST, self.config.TEMPERATURE_RX_PORT)
                
                logger.info(f"Starting temperature test - sending to {address}")
                
                while self._running:
                    # Generate random temperature data (50-100°C)
                    temperature = random.randint(50, 100)
                    packet = str(temperature).encode()
                    
                    sock.sendto(packet, address)
                    logger.debug(f"Sent temperature: {temperature}")
                    
                    time.sleep(0.5)  # Send every 500ms
                
                sock.close()
                logger.info("Temperature test stopped")
                
            except Exception as e:
                logger.error(f"Error in temperature sender: {e}")
        
        thread = threading.Thread(target=temperature_sender, name="TemperatureSender")
        thread.daemon = True
        thread.start()
        self._threads.append(thread)
    
    def _start_pressure_test(self) -> None:
        """Start pressure test data generation."""
        def pressure_sender():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                address = (self.config.LOCAL_HOST, self.config.PRESSURE_RX_PORT)
                
                logger.info(f"Starting pressure test - sending to {address}")
                
                while self._running:
                    # Generate random pressure data (50-100 kPa)
                    pressure = random.uniform(50, 100)
                    packet = f"{pressure:.2f}".encode()
                    
                    sock.sendto(packet, address)
                    logger.debug(f"Sent pressure: {pressure:.2f}")
                    
                    time.sleep(0.5)  # Send every 500ms
                
                sock.close()
                logger.info("Pressure test stopped")
                
            except Exception as e:
                logger.error(f"Error in pressure sender: {e}")
        
        thread = threading.Thread(target=pressure_sender, name="PressureSender")
        thread.daemon = True
        thread.start()
        self._threads.append(thread)
    
    def run(self) -> int:
        """Run the PYNQ client.
        
        Returns:
            Exit code (0 for success)
        """
        try:
            logger.info("Starting PYNQ client...")
            self.start()
            
            # Keep the main thread alive
            while self._running:
                time.sleep(1)
            
            logger.info("PYNQ client finished normally")
            return 0
            
        except KeyboardInterrupt:
            logger.info("PYNQ client interrupted by user")
            return 0
            
        except Exception as e:
            logger.error(f"Unexpected error in PYNQ client: {e}")
            return 1
            
        finally:
            self.stop()


def main():
    """Main entry point for the PYNQ client."""
    print("=" * 60)
    print("AtomCraft Instrumentation and Controls System (Refactored)")
    print("PYNQ Client Application")
    print("=" * 60)
    
    try:
        client = AtomCraftPYNQClient()
        exit_code = client.run()
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
