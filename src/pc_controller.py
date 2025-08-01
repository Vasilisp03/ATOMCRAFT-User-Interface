"""Main PC controller application for the AtomCraft system.

This is the main entry point for the PC-side control application.
It initializes all components and starts the GUI.
"""

#!/usr/bin/env python3

import sys
import signal
from pathlib import Path

import sys
import signal
from pathlib import Path

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from gui.main_window import MainWindow
from networking.pc_server import NetworkServer
from utils.logging_config import logger


class AtomCraftPCController:
    """Main controller class for the PC-side application.
    
    This class coordinates all the major components of the system
    including the GUI, networking, and data management.
    """
    
    def __init__(self):
        """Initialize the controller."""
        self.main_window = None
        self.network_server = None
        self._setup_signal_handlers()
        
        logger.info("AtomCraftPCController initializing...")
    
    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def initialize(self) -> bool:
        """Initialize all system components.
        
        Returns:
            True if initialization successful
        """
        try:
            # Create main window
            self.main_window = MainWindow()
            
            # Create network server
            self.network_server = NetworkServer(self.main_window.data_buffer)
            
            # Set up callbacks between components
            self._setup_component_callbacks()
            
            logger.info("System initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize system: {e}")
            return False
    
    def _setup_component_callbacks(self) -> None:
        """Set up callbacks between different components."""
        # Register network callbacks for real-time updates
        if self.network_server and self.main_window:
            # TF Current callback
            def on_tf_current_received(value):
                logger.debug(f"TF Current received: {value}")
            
            # Temperature callback
            def on_temperature_received(value):
                logger.debug(f"Temperature received: {value}")
            
            # Pressure callback
            def on_pressure_received(value):
                logger.debug(f"Pressure received: {value}")
            
            # Solenoid callback
            def on_solenoid_received(pressure, status):
                logger.debug(f"Solenoid data received: {pressure}, {status}")
            
            # Register callbacks
            self.network_server.register_callback('tf_current', on_tf_current_received)
            self.network_server.register_callback('temperature', on_temperature_received)
            self.network_server.register_callback('pressure', on_pressure_received)
            self.network_server.register_callback('solenoid', on_solenoid_received)
            
            # Give main window reference to network server for cleanup
            self.main_window.set_network_server(self.network_server)
    
    def run(self) -> int:
        """Run the main application.
        
        Returns:
            Exit code (0 for success)
        """
        if not self.initialize():
            logger.error("Failed to initialize application")
            return 1
        
        try:
            # Start network services
            logger.info("Starting network services...")
            self.network_server.start()
            
            # Create and show main window
            logger.info("Creating main window...")
            self.main_window.create_window()
            
            # Start the GUI main loop
            logger.info("Starting GUI main loop...")
            self.main_window.run()
            
            logger.info("Application finished normally")
            return 0
            
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
            return 0
            
        except Exception as e:
            logger.error(f"Unexpected error in main application: {e}")
            return 1
            
        finally:
            self.shutdown()
    
    def shutdown(self) -> None:
        """Shutdown the application gracefully."""
        logger.info("Shutting down application...")
        
        try:
            # Stop network server
            if self.network_server:
                self.network_server.stop()
                logger.info("Network server stopped")
            
            # The main window cleanup is handled by the window itself
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        logger.info("Application shutdown completed")


def main():
    """Main entry point for the application."""
    print("=" * 60)
    print("AtomCraft Instrumentation and Controls System (Refactored)")
    print("PC Controller Application")
    print("=" * 60)
    
    try:
        controller = AtomCraftPCController()
        exit_code = controller.run()
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
