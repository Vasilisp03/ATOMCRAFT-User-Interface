"""Control panels for the AtomCraft GUI.

This module provides user interface panels for command input,
status display, and system control.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import UI
from core.data_manager import DataManager, SensorDataBuffer
from utils.logging_config import logger


class ControlPanel:
    """Control panel for command input and history display.
    
    This panel provides the main interface for users to input commands
    and view command history.
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        data_manager: DataManager,
        on_command_callback: Callable,
        on_exit_callback: Callable
    ):
        """Initialize the control panel.
        
        Args:
            parent: Parent tkinter widget
            data_manager: Data manager for command history
            on_command_callback: Callback for command submission
            on_exit_callback: Callback for exit requests
        """
        self.parent = parent
        self.data_manager = data_manager
        self.on_command_callback = on_command_callback
        self.on_exit_callback = on_exit_callback
        
        # GUI components
        self.command_entry = None
        self.history_listbox = None
        
        self._create_widgets()
        self._populate_initial_data()
        
        logger.info("ControlPanel initialized")
    
    def _create_widgets(self) -> None:
        """Create the control panel widgets."""
        # Title label
        title_label = tk.Label(
            self.parent,
            text="Command Interface",
            font=("Arial", 14, "bold"),
            bg=UI.PANEL_COLOR,
            fg=UI.TEXT_COLOR
        )
        title_label.pack(pady=(10, 5))
        
        # Command input frame
        input_frame = tk.Frame(self.parent, bg=UI.PANEL_COLOR)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Command entry
        tk.Label(
            input_frame,
            text="Command:",
            bg=UI.PANEL_COLOR,
            fg=UI.TEXT_COLOR
        ).pack(anchor=tk.W)
        
        self.command_entry = tk.Entry(
            input_frame,
            font=("Consolas", 10),
            bg="white",
            fg="black",
            insertbackground="black"
        )
        self.command_entry.pack(fill=tk.X, pady=(2, 0))
        self.command_entry.focus_set()  # Set initial focus
        
        # Buttons frame
        button_frame = tk.Frame(self.parent, bg=UI.PANEL_COLOR)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Submit button
        submit_btn = tk.Button(
            button_frame,
            text="Submit",
            command=self.on_command_callback,
            bg=UI.ACCENT_COLOR,
            fg="black",
            font=("Arial", 10),
            relief="flat",
            cursor="hand2"
        )
        submit_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Clear button
        clear_btn = tk.Button(
            button_frame,
            text="Clear History",
            command=self._clear_history,
            bg="#666666",
            fg="black",
            font=("Arial", 10),
            relief="flat",
            cursor="hand2"
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Help button
        help_btn = tk.Button(
            button_frame,
            text="Help",
            command=self._show_help,
            bg="#0066CC",
            fg="black",
            font=("Arial", 10),
            relief="flat",
            cursor="hand2"
        )
        help_btn.pack(side=tk.RIGHT)
        
        # Command history section
        history_label = tk.Label(
            self.parent,
            text="Command History",
            font=("Arial", 12, "bold"),
            bg=UI.PANEL_COLOR,
            fg=UI.TEXT_COLOR
        )
        history_label.pack(pady=(15, 5))
        
        # History listbox with scrollbar
        history_frame = tk.Frame(self.parent, bg=UI.PANEL_COLOR)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Scrollbar
        scrollbar = tk.Scrollbar(history_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox
        self.history_listbox = tk.Listbox(
            history_frame,
            yscrollcommand=scrollbar.set,
            font=("Consolas", 9),
            bg="#F0F0F0",
            fg="black",
            selectbackground=UI.ACCENT_COLOR,
            activestyle="none"
        )
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.history_listbox.yview)
        
        # Exit button at bottom
        exit_btn = tk.Button(
            self.parent,
            text="Exit Application",
            command=self.on_exit_callback,
            bg="#CC0000",
            fg="black",
            font=("Arial", 10, "bold"),
            relief="flat",
            cursor="hand2"
        )
        exit_btn.pack(side=tk.BOTTOM, pady=10)
    
    def _populate_initial_data(self) -> None:
        """Populate initial data in the widgets."""
        self.update_command_history()
        
        # Add welcome message
        try:
            self.data_manager.add_command("=== AtomCraft Control System Started ===")
            self.data_manager.add_command("Type 'help' for available commands")
            self.update_command_history()
        except Exception as e:
            logger.error(f"Failed to add welcome messages: {e}")
    
    def get_current_command(self) -> str:
        """Get the current command from the entry field.
        
        Returns:
            Command string (stripped of whitespace)
        """
        if self.command_entry:
            return self.command_entry.get().strip()
        return ""
    
    def clear_command_input(self) -> None:
        """Clear the command input field."""
        if self.command_entry:
            self.command_entry.delete(0, tk.END)
    
    def update_command_history(self) -> None:
        """Update the command history display."""
        if not self.history_listbox:
            return
        
        try:
            # Get command history from database
            history = self.data_manager.get_command_history()
            
            # Clear current content
            self.history_listbox.delete(0, tk.END)
            
            # Add commands to listbox
            for _, command, timestamp in history:
                # Format display string
                display_text = f"{command}"
                if len(display_text) > 50:
                    display_text = display_text[:47] + "..."
                
                self.history_listbox.insert(tk.END, display_text)
            
            # Scroll to bottom to show most recent
            if history:
                self.history_listbox.see(tk.END)
                
        except Exception as e:
            logger.error(f"Failed to update command history: {e}")
    
    def _clear_history(self) -> None:
        """Clear the command history."""
        try:
            self.data_manager.clear_command_history()
            self.update_command_history()
            logger.info("Command history cleared from control panel")
        except Exception as e:
            logger.error(f"Failed to clear history: {e}")
    
    def _show_help(self) -> None:
        """Show help by adding help command to history."""
        try:
            self.data_manager.add_command("help")
            self.update_command_history()
            # The main window will handle the actual help display
        except Exception as e:
            logger.error(f"Failed to add help command: {e}")


class StatusPanel:
    """Status panel for displaying system information and sensor readings.
    
    This panel shows real-time status information including sensor values,
    system state, and operational metrics.
    """
    
    def __init__(self, parent: tk.Widget, data_buffer: SensorDataBuffer):
        """Initialize the status panel.
        
        Args:
            parent: Parent tkinter widget
            data_buffer: Data buffer for sensor readings
        """
        self.parent = parent
        self.data_buffer = data_buffer
        
        # Status display widgets
        self.status_labels = {}
        self.value_labels = {}
        
        self._create_widgets()
        
        logger.info("StatusPanel initialized")
    
    def _create_widgets(self) -> None:
        """Create the status panel widgets."""
        # Configure grid layout
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_columnconfigure(1, weight=1)
        self.parent.grid_columnconfigure(2, weight=1)
        self.parent.grid_columnconfigure(3, weight=1)
        
        # Create status sections
        self._create_status_section("Pressure", 0, "pressure")
        self._create_status_section("Temperature", 1, "temperature")
        self._create_status_section("Solenoid Pressure", 2, "solenoid_pressure")
        self._create_status_section("Solenoid Status", 3, "solenoid_status")
        
        # Add divider lines
        self._create_dividers()
    
    def _create_status_section(self, title: str, column: int, data_key: str) -> None:
        """Create a status display section.
        
        Args:
            title: Section title
            column: Grid column position
            data_key: Data key for updates
        """
        # Section frame
        section_frame = tk.Frame(self.parent, bg=UI.PANEL_COLOR)
        section_frame.grid(row=0, column=column, sticky="nsew", padx=5, pady=10)
        
        # Title label
        title_label = tk.Label(
            section_frame,
            text=title,
            font=("Arial", 12, "bold"),
            bg="#060621",  # Dark background for contrast
            fg=UI.TEXT_COLOR,
            relief="solid",
            bd=2
        )
        title_label.pack(fill=tk.X, pady=(0, 5))
        
        # Value label
        value_label = tk.Label(
            section_frame,
            text="0.00" if "status" not in data_key else "UNKNOWN",
            font=("Arial", 24, "bold") if "status" not in data_key else ("Arial", 18, "bold"),
            bg="#060621",
            fg=UI.TEXT_COLOR,
            relief="solid",
            bd=1
        )
        value_label.pack(fill=tk.X)
        
        # Store references
        self.status_labels[data_key] = title_label
        self.value_labels[data_key] = value_label
    
    def _create_dividers(self) -> None:
        """Create visual dividers between sections."""
        for i in range(3):  # 3 dividers for 4 sections
            divider = tk.Frame(
                self.parent,
                width=2,
                bg=UI.ACCENT_COLOR,
                relief="solid",
                bd=1
            )
            divider.grid(row=0, column=i, sticky="nse", padx=(0, 5))
    
    def update_displays(self) -> None:
        """Update all status displays with current data."""
        try:
            # Update pressure
            pressure_data = self.data_buffer.get_pressure_data()
            if pressure_data:
                latest_pressure = pressure_data[-1]
                self.value_labels["pressure"].config(text=f"{latest_pressure:.2f}")
            
            # Update temperature
            temp_data = self.data_buffer.get_temperature_data()
            if temp_data:
                latest_temp = temp_data[-1]
                self.value_labels["temperature"].config(text=f"{latest_temp:.1f}")
            
            # Update solenoid data
            solenoid_data, solenoid_status = self.data_buffer.get_solenoid_data()
            if solenoid_data:
                latest_solenoid_pressure = solenoid_data[-1]
                self.value_labels["solenoid_pressure"].config(text=f"{latest_solenoid_pressure:.2f}")
            
            self.value_labels["solenoid_status"].config(text=solenoid_status)
            
            # Update status colors based on values
            self._update_status_colors()
            
        except Exception as e:
            logger.error(f"Error updating status displays: {e}")
    
    def _update_status_colors(self) -> None:
        """Update display colors based on current values."""
        try:
            # Color solenoid status based on state
            status_text = self.value_labels["solenoid_status"].cget("text")
            if status_text == "OPEN":
                self.value_labels["solenoid_status"].config(fg="#00FF00")  # Green
            elif status_text == "CLOSED":
                self.value_labels["solenoid_status"].config(fg="#FF6666")  # Light red
            else:
                self.value_labels["solenoid_status"].config(fg=UI.TEXT_COLOR)  # Default
            
            # Add temperature warning colors
            temp_text = self.value_labels["temperature"].cget("text")
            try:
                temp_value = float(temp_text)
                if temp_value > 80:  # High temperature warning
                    self.value_labels["temperature"].config(fg="#FF4444")  # Red
                elif temp_value > 60:  # Medium temperature warning
                    self.value_labels["temperature"].config(fg="#FFAA00")  # Orange
                else:
                    self.value_labels["temperature"].config(fg=UI.TEXT_COLOR)  # Default
            except ValueError:
                pass  # Keep default color if not a number
                
        except Exception as e:
            logger.error(f"Error updating status colors: {e}")
    
    def reset_displays(self) -> None:
        """Reset all displays to default values."""
        default_values = {
            "pressure": "0.00",
            "temperature": "0.0",
            "solenoid_pressure": "0.00",
            "solenoid_status": "UNKNOWN"
        }
        
        for key, default_value in default_values.items():
            if key in self.value_labels:
                self.value_labels[key].config(text=default_value, fg=UI.TEXT_COLOR)
        
        logger.info("Status displays reset to defaults")
