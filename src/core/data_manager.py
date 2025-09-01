"""Data management and storage for the AtomCraft system.

This module handles all data storage operations, including database management,
data caching, and persistence operations.
"""

import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import DATABASE
from utils.exceptions import DatabaseException
from utils.logging_config import logger


class DataManager:
    """Manages data storage and retrieval operations.
    
    This class provides a clean interface for all data operations,
    including database management, command history, and sensor data storage.
    """
    
    def __init__(self, db_path: str = DATABASE.NAMES_DB_PATH):
        """Initialize the data manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self._db_lock = threading.Lock()
        self._initialize_database()
        
        logger.info(f"DataManager initialized with database: {self.db_path}")
    
    def _initialize_database(self) -> None:
        """Create database tables if they don't exist."""
        try:
            # Ensure database directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(DATABASE.NAMES_TABLE)
                conn.commit()
                
            logger.info("Database initialized successfully")
            
        except sqlite3.Error as e:
            raise DatabaseException(f"Failed to initialize database: {e}")
    
    def add_command(self, command: str) -> None:
        """Add a command to the command history.
        
        Args:
            command: The command string to store
            
        Raises:
            DatabaseException: If the database operation fails
        """
        try:
            with self._db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "INSERT INTO names (name) VALUES (?)",
                        (command,)
                    )
                    conn.commit()
                    
            logger.debug(f"Added command to history: {command}")
            
        except sqlite3.Error as e:
            raise DatabaseException(f"Failed to add command: {e}")
    
    def get_command_history(self, limit: Optional[int] = None) -> List[Tuple[int, str]]:
        """Retrieve command history from the database.
        
        Args:
            limit: Maximum number of commands to retrieve (optional)
            
        Returns:
            List of tuples containing (id, command)
            
        Raises:
            DatabaseException: If the database operation fails
        """
        try:
            with self._db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    query = "SELECT id, name FROM names ORDER BY id"
                    if limit:
                        query += f" LIMIT {limit}"
                    
                    cursor = conn.execute(query)
                    return cursor.fetchall()
                    
        except sqlite3.Error as e:
            raise DatabaseException(f"Failed to retrieve command history: {e}")
    
    def clear_command_history(self) -> None:
        """Clear all commands from the history.
        
        Raises:
            DatabaseException: If the database operation fails
        """
        try:
            with self._db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM names")
                    conn.commit()
                    
            logger.info("Command history cleared")
            
        except sqlite3.Error as e:
            raise DatabaseException(f"Failed to clear command history: {e}")
    
    def get_latest_commands(self, count: int = 10) -> List[str]:
        """Get the most recent commands.
        
        Args:
            count: Number of recent commands to retrieve
            
        Returns:
            List of command strings
        """
        try:
            history = self.get_command_history()
            return [cmd[1] for cmd in history[-count:]]
            
        except DatabaseException:
            logger.warning("Failed to retrieve latest commands")
            return []


class SensorDataBuffer:
    """Thread-safe buffer for sensor data.
    
    This class manages rolling buffers for different types of sensor data,
    providing thread-safe access and automatic size management.
    """
    
    def __init__(self, buffer_size: int = 100):
        """Initialize the sensor data buffer.
        
        Args:
            buffer_size: Maximum number of data points to store
        """
        self.buffer_size = buffer_size
        self._lock = threading.Lock()
        
        # Initialize data buffers
        self.tf_current_data: List[float] = [0.0] * buffer_size
        self.temperature_data: List[float] = [25.0] * buffer_size
        self.pressure_data: List[float] = [0.0] * buffer_size
        self.solenoid_pressure_data: List[float] = [0.0] * buffer_size
        
        # Status variables
        self.solenoid_status: str = "CLOSED"
        
        logger.info(f"SensorDataBuffer initialized with size: {buffer_size}")
    
    def add_tf_current(self, value: float) -> None:
        """Add a TF coil current measurement.
        
        Args:
            value: Current measurement value
        """
        with self._lock:
            self.tf_current_data.append(value)
            if len(self.tf_current_data) > self.buffer_size:
                self.tf_current_data.pop(0)
    
    def add_temperature(self, value: float) -> None:
        """Add a temperature measurement.
        
        Args:
            value: Temperature measurement value
        """
        with self._lock:
            self.temperature_data.append(value)
            if len(self.temperature_data) > self.buffer_size:
                self.temperature_data.pop(0)
    
    def add_pressure(self, value: float) -> None:
        """Add a pressure measurement.
        
        Args:
            value: Pressure measurement value
        """
        with self._lock:
            self.pressure_data.append(value)
            if len(self.pressure_data) > self.buffer_size:
                self.pressure_data.pop(0)
    
    def add_solenoid_pressure(self, value: float, status: str) -> None:
        """Add solenoid pressure and status data.
        
        Args:
            value: Pressure measurement value
            status: Solenoid status string
        """
        with self._lock:
            self.solenoid_pressure_data.append(value)
            if len(self.solenoid_pressure_data) > self.buffer_size:
                self.solenoid_pressure_data.pop(0)
            self.solenoid_status = status
    
    def get_tf_current_data(self) -> List[float]:
        """Get a copy of the TF current data."""
        with self._lock:
            return self.tf_current_data.copy()
    
    def get_temperature_data(self) -> List[float]:
        """Get a copy of the temperature data."""
        with self._lock:
            return self.temperature_data.copy()
    
    def get_pressure_data(self) -> List[float]:
        """Get a copy of the pressure data."""
        with self._lock:
            return self.pressure_data.copy()
    
    def get_solenoid_data(self) -> Tuple[List[float], str]:
        """Get solenoid pressure data and status.
        
        Returns:
            Tuple of (pressure_data_copy, current_status)
        """
        with self._lock:
            return self.solenoid_pressure_data.copy(), self.solenoid_status
    
    def get_latest_value(self, data_type: str) -> Optional[float]:
        """Get the latest value for a specific data type.
        
        Args:
            data_type: Type of data ('current', 'temperature', 'pressure', 'solenoid_pressure')
            
        Returns:
            Latest value or None if no data available
        """
        with self._lock:
            data_map = {
                'current': self.tf_current_data,
                'temperature': self.temperature_data,
                'pressure': self.pressure_data,
                'solenoid_pressure': self.solenoid_pressure_data
            }
            
            data = data_map.get(data_type)
            return data[-1] if data else None
