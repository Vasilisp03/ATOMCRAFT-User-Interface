"""Configuration constants for the AtomCraft control system.

This module centralizes all configuration parameters to make them easy to find
and modify without changing code throughout the application.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class NetworkConfig:
    """Network configuration for socket communication."""
    
    # Host addresses
    LOCAL_HOST: str = '127.0.0.1'
    ARDUINO_HOST: str = '192.168.1.100'
    
    # Port assignments
    TF_CURRENT_RX_PORT: int = 1200      # PC receives TF coil current
    COMMAND_TX_PORT: int = 1300         # PC sends commands to PYNQ
    WAVEFORM_TX_PORT: int = 1400        # PC sends waveform data
    TEMPERATURE_RX_PORT: int = 1500     # PC receives temperature data
    PRESSURE_RX_PORT: int = 1600        # PC receives pressure data
    SOLENOID_PORT: int = 2390           # Arduino solenoid control
    
    # Timeouts and connection settings
    SOCKET_TIMEOUT: float = 1.0
    MAX_PACKET_SIZE: int = 1024


@dataclass
class UIConfig:
    """User interface configuration."""
    
    # Window settings
    WINDOW_TITLE: str = "AtomCraft Controller"
    WINDOW_SIZE: Tuple[int, int] = (1440, 900)
    
    # Colors (using a professional dark theme)
    BACKGROUND_COLOR: str = "#1D1D1D"
    ACCENT_COLOR: str = "#C65D3B"
    PANEL_COLOR: str = "#005B5C"
    TEXT_COLOR: str = "#FFFFFF"
    
    # Update rates (milliseconds)
    PLOT_UPDATE_RATE: int = 100
    DISPLAY_UPDATE_RATE: int = 1000
    
    # Plot settings
    PLOT_SIZE: Tuple[int, int] = (4, 3)
    PLOT_DPI: int = 100
    DATA_BUFFER_SIZE: int = 100


@dataclass
class SignalProcessingConfig:
    """Signal processing parameters."""
    
    # Savitzky-Golay filter parameters
    FILTER_WINDOW_LENGTH: int = 7
    FILTER_POLYNOMIAL_ORDER: int = 2
    
    # Waveform parameters
    WAVEFORM_POINTS: int = 100
    WAVEFORM_TIMESCALE: int = 3000  # milliseconds
    
    # Data ranges
    MIN_CURRENT: float = 0.0
    MAX_CURRENT: float = 100.0
    MIN_TEMPERATURE: float = 0.0
    MAX_TEMPERATURE: float = 150.0


@dataclass
class DatabaseConfig:
    """Database configuration."""
    
    NAMES_DB_PATH: str = "data/names.db"
    COMMANDS_DB_PATH: str = "data/commands.db"
    
    # Table schemas
    NAMES_TABLE: str = """
        CREATE TABLE IF NOT EXISTS names (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    """


# Global configuration instances
NETWORK = NetworkConfig()
UI = UIConfig()
SIGNAL_PROCESSING = SignalProcessingConfig()
DATABASE = DatabaseConfig()


# Available plot data types
PLOT_DATA_TYPES = ["Current", "Temperature", "Pressure"]

# Available commands for the system
SYSTEM_COMMANDS = {
    "clear": "Clear command history",
    "start control loop": "Begin current control with waveform input",
    "temperature test": "Start temperature monitoring test",
    "pressure test": "Start pressure monitoring test",
    "solenoid test": "Initialize solenoid system",
    "solenoid open": "Open solenoid valve",
    "solenoid pressure": "Get solenoid pressure reading",
    "exit": "Exit the application gracefully"
}
