"""Main GUI window for the AtomCraft control system.

This module provides the main application window with all user interface
components organized in a clean, maintainable structure.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import UI, SYSTEM_COMMANDS
from core.data_manager import DataManager, SensorDataBuffer
from core.signal_processor import WaveformProcessor
from networking.pc_server import NetworkClient
from utils.logging_config import logger
from gui.plot_widgets import PlotManager
from gui.control_panels import ControlPanel, StatusPanel


class MainWindow:
    """Main application window for the AtomCraft control system.
    
    This class coordinates all GUI components and manages the overall
    user interface layout and interactions.
    """
    
    def __init__(self):
        """Initialize the main window."""
        # Core components
        self.data_manager = DataManager()
        self.data_buffer = SensorDataBuffer()
        self.waveform_processor = WaveformProcessor()
        self.network_client = NetworkClient()
        
        # GUI components
        self.root = None
        self.plot_manager = None
        self.control_panel = None
        self.status_panel = None
        
        # State management
        self._waiting_for_waveform = False
        self._running = True
        
        logger.info("MainWindow initialized")
    
    def create_window(self) -> tk.Tk:
        """Create and configure the main window.
        
        Returns:
            The root Tkinter window
        """
        self.root = tk.Tk()
        self.root.title(UI.WINDOW_TITLE)
        self.root.geometry(f"{UI.WINDOW_SIZE[0]}x{UI.WINDOW_SIZE[1]}")
        self.root.configure(bg=UI.BACKGROUND_COLOR)
        
        # Prevent window from being too small
        self.root.minsize(800, 600)
        
        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        # Create GUI layout
        self._create_layout()
        
        # Bind keyboard shortcuts
        self._setup_keyboard_bindings()
        
        logger.info("Main window created")
        return self.root
    
    def _create_layout(self) -> None:
        """Create the main window layout."""
        # Create main frames using modern grid layout
        self._create_frames()
        
        # Initialize components
        self._initialize_components()
        
        # Start periodic updates
        self._start_updates()
    
    def _create_frames(self) -> None:
        """Create the main layout frames."""
        # Configure grid weights for responsive layout
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        # Left control frame
        self.left_frame = tk.Frame(
            self.root,
            width=300,
            bg=UI.PANEL_COLOR,
            relief="solid",
            bd=1
        )
        self.left_frame.grid(row=0, column=0, sticky="nsw", padx=2, pady=2)
        self.left_frame.grid_propagate(False)
        
        # Main content frame (plots)
        self.main_frame = tk.Frame(
            self.root,
            bg=UI.BACKGROUND_COLOR,
            relief="solid",
            bd=1
        )
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        
        # Bottom status frame
        self.bottom_frame = tk.Frame(
            self.root,
            height=200,
            bg=UI.PANEL_COLOR,
            relief="solid",
            bd=1
        )
        self.bottom_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=2, pady=2)
        self.bottom_frame.grid_propagate(False)
    
    def _initialize_components(self) -> None:
        """Initialize all GUI components."""
        # Control panel (left side)
        self.control_panel = ControlPanel(
            self.left_frame,
            self.data_manager,
            self._on_command_submitted,
            self._on_exit_requested
        )
        
        # Plot manager (main area)
        self.plot_manager = PlotManager(
            self.main_frame,
            self.data_buffer
        )
        
        # Status panel (bottom)
        self.status_panel = StatusPanel(
            self.bottom_frame,
            self.data_buffer
        )
        
        logger.info("GUI components initialized")
    
    def _setup_keyboard_bindings(self) -> None:
        """Set up keyboard shortcuts."""
        # Enter key for command submission
        self.root.bind('<Return>', self._on_command_submitted)
        
        # Escape key to cancel operations
        self.root.bind('<Escape>', self._on_escape_pressed)
        
        # Ctrl+Q for quit
        self.root.bind('<Control-q>', lambda e: self._on_exit_requested())
        
        logger.debug("Keyboard bindings configured")
    
    def _start_updates(self) -> None:
        """Start periodic GUI updates."""
        self._update_displays()
        logger.debug("Periodic updates started")
    
    def _update_displays(self) -> None:
        """Update all displays periodically."""
        if not self._running:
            return
        
        try:
            # Update plots
            if self.plot_manager:
                self.plot_manager.update_plots()
            
            # Update status displays
            if self.status_panel:
                self.status_panel.update_displays()
            
        except Exception as e:
            logger.error(f"Error updating displays: {e}")
        
        # Schedule next update
        if self.root:
            self.root.after(UI.PLOT_UPDATE_RATE, self._update_displays)
    
    def _on_command_submitted(self, event=None) -> None:
        """Handle command submission from the control panel.
        
        Args:
            event: Tkinter event (optional)
        """
        try:
            command = self.control_panel.get_current_command()
            if not command:
                return
            
            # Clear the input field
            self.control_panel.clear_command_input()
            
            # Add to command history
            self.data_manager.add_command(command)
            self.control_panel.update_command_history()
            
            # Handle different command types
            if self._waiting_for_waveform:
                self._handle_waveform_input(command)
            else:
                self._handle_regular_command(command)
                
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            self._show_error("Command Error", f"Failed to process command: {e}")
    
    def _handle_regular_command(self, command: str) -> None:
        """Handle regular system commands.
        
        Args:
            command: Command string to process
        """
        command_lower = command.lower()
        
        # Handle special commands locally
        if command_lower == "clear":
            self._clear_command_history()
        elif command_lower == "exit":
            self._on_exit_requested()
        elif command_lower == "start control loop":
            self._start_waveform_input()
        elif command_lower == "help":
            self._show_help()
        elif command_lower.startswith("solenoid"):
            self._handle_solenoid_command(command)
        else:
            # Send command to network
            success = self.network_client.send_command(command)
            if not success:
                self._show_error("Network Error", f"Failed to send command: {command}")
    
    def _handle_waveform_input(self, waveform_str: str) -> None:
        """Handle waveform input during control loop setup.
        
        Args:
            waveform_str: Waveform input string
        """
        if waveform_str.lower() == "cancel control":
            self._waiting_for_waveform = False
            self.data_manager.add_command("Control loop cancelled")
            self.control_panel.update_command_history()
            return
        
        try:
            # Process waveform
            waveform_data = self.waveform_processor.process_waveform_command(waveform_str)
            
            # Send to network
            success = self.network_client.send_waveform(waveform_data)
            
            if success:
                self.data_manager.add_command("Waveform sent successfully")
                self._waiting_for_waveform = False
            else:
                self.data_manager.add_command("Failed to send waveform")
                self._show_error("Network Error", "Failed to send waveform data")
            
            self.control_panel.update_command_history()
            
        except Exception as e:
            logger.error(f"Waveform processing error: {e}")
            self.data_manager.add_command(f"Waveform error: {str(e)}")
            self.control_panel.update_command_history()
    
    def _start_waveform_input(self) -> None:
        """Start waveform input mode."""
        self._waiting_for_waveform = True
        self.data_manager.add_command("Enter waveform data:")
        self.data_manager.add_command("Format: t1,t2,t3,t4,a1,a2,a3,a4")
        self.data_manager.add_command("Type 'cancel control' to abort")
        self.control_panel.update_command_history()
    
    def _handle_solenoid_command(self, command: str) -> None:
        """Handle solenoid-specific commands.
        
        Args:
            command: Solenoid command string
        """
        try:
            response = self.network_client.send_solenoid_command(command)
            if response:
                self.data_manager.add_command(f"Solenoid response: {response}")
            else:
                self.data_manager.add_command("Solenoid command failed")
            
            self.control_panel.update_command_history()
            
        except Exception as e:
            logger.error(f"Solenoid command error: {e}")
            self._show_error("Solenoid Error", f"Failed to execute solenoid command: {e}")
    
    def _clear_command_history(self) -> None:
        """Clear the command history."""
        try:
            self.data_manager.clear_command_history()
            self.control_panel.update_command_history()
            logger.info("Command history cleared")
        except Exception as e:
            logger.error(f"Failed to clear command history: {e}")
            self._show_error("Database Error", "Failed to clear command history")
    
    def _show_help(self) -> None:
        """Show help information."""
        help_text = """
AtomCraft Control System Help

Available Commands:
• clear - Clear command history
• start control loop - Begin waveform control
• temperature test - Start temperature monitoring
• pressure test - Start pressure monitoring
• solenoid test - Initialize solenoid system
• solenoid open - Open solenoid valve
• solenoid pressure - Get pressure reading
• solenoid time <ms> - Set valve duration
• help - Show this help
• exit - Exit application

Keyboard Shortcuts:
• Enter - Submit command
• Escape - Cancel current operation
• Ctrl+Q - Exit application
        """
        
        messagebox.showinfo("Help", help_text.strip())
    
    def _on_escape_pressed(self, event=None) -> None:
        """Handle Escape key press.
        
        Args:
            event: Tkinter event (optional)
        """
        if self._waiting_for_waveform:
            self._waiting_for_waveform = False
            self.data_manager.add_command("Operation cancelled")
            self.control_panel.update_command_history()
    
    def _on_exit_requested(self) -> None:
        """Handle exit request."""
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            self._cleanup_and_exit()
    
    def _on_window_close(self) -> None:
        """Handle window close event."""
        self._cleanup_and_exit()
    
    def _cleanup_and_exit(self) -> None:
        """Perform cleanup and exit the application."""
        try:
            self._running = False
            
            # Stop network components
            if hasattr(self, 'network_server'):
                self.network_server.stop()
            
            # Close database connections
            # (DataManager handles this automatically)
            
            logger.info("Application shutting down")
            
            # Destroy the window
            if self.root:
                self.root.quit()
                self.root.destroy()
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def _show_error(self, title: str, message: str) -> None:
        """Show an error dialog.
        
        Args:
            title: Dialog title
            message: Error message
        """
        messagebox.showerror(title, message)
        logger.error(f"{title}: {message}")
    
    def set_network_server(self, network_server) -> None:
        """Set the network server instance for cleanup.
        
        Args:
            network_server: NetworkServer instance
        """
        self.network_server = network_server
    
    def run(self) -> None:
        """Start the GUI main loop."""
        if not self.root:
            raise RuntimeError("Window not created. Call create_window() first.")
        
        logger.info("Starting GUI main loop")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            self._cleanup_and_exit()
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            raise
