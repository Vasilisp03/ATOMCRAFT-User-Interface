"""Plot widgets for the AtomCraft GUI.

This module provides plotting components with real-time data visualization
capabilities using matplotlib and tkinter integration.
"""

import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
import numpy as np
from typing import Dict, List, Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import UI, SIGNAL_PROCESSING, PLOT_DATA_TYPES
from core.data_manager import SensorDataBuffer
from core.signal_processor import SignalFilter
from utils.logging_config import logger


class PlotWidget:
    """Individual plot widget for displaying sensor data.
    
    This class manages a single plot with configurable data source
    and automatic updating capabilities.
    """
    
    def __init__(self, parent: tk.Widget, title: str, position: tuple):
        """Initialize a plot widget.
        
        Args:
            parent: Parent tkinter widget
            title: Plot title
            position: (x, y) relative position for placement
        """
        self.parent = parent
        self.title = title
        self.position = position
        self.data_type = "Current"  # Default data type
        
        # Signal processing
        self.signal_filter = SignalFilter()
        
        # Create matplotlib figure
        self.figure = Figure(
            figsize=UI.PLOT_SIZE,
            dpi=UI.PLOT_DPI,
            facecolor=UI.BACKGROUND_COLOR
        )
        
        self.axes = self.figure.add_subplot(111)
        self._configure_plot_appearance()
        
        # Create tkinter canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.canvas.draw()
        
        # Position the widget
        self.canvas.get_tk_widget().place(relx=position[0], rely=position[1])
        
        # Create toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, parent)
        self.toolbar.update()
        
        logger.debug(f"PlotWidget '{title}' created at position {position}")
    
    def _configure_plot_appearance(self) -> None:
        """Configure the visual appearance of the plot."""
        # Set colors
        self.axes.set_facecolor('black')
        self.axes.spines['bottom'].set_color(UI.ACCENT_COLOR)
        self.axes.spines['top'].set_color(UI.ACCENT_COLOR)
        self.axes.spines['right'].set_color(UI.ACCENT_COLOR)
        self.axes.spines['left'].set_color(UI.ACCENT_COLOR)
        
        # Set text colors
        self.axes.xaxis.label.set_color(UI.ACCENT_COLOR)
        self.axes.yaxis.label.set_color(UI.ACCENT_COLOR)
        self.axes.tick_params(axis='x', colors='white')
        self.axes.tick_params(axis='y', colors='white')
        
        # Set title
        self.axes.set_title(self.title, color=UI.TEXT_COLOR)
        
        # Set default limits
        self.axes.set_xlim(0, UI.DATA_BUFFER_SIZE)
        self._set_y_limits_for_data_type(self.data_type)
    
    def _set_y_limits_for_data_type(self, data_type: str) -> None:
        """Set appropriate Y-axis limits based on data type.
        
        Args:
            data_type: Type of data being plotted
        """
        limits = {
            "Current": (SIGNAL_PROCESSING.MIN_CURRENT, SIGNAL_PROCESSING.MAX_CURRENT),
            "Temperature": (SIGNAL_PROCESSING.MIN_TEMPERATURE, SIGNAL_PROCESSING.MAX_TEMPERATURE),
            "Pressure": (0, 100)  # Reasonable pressure range
        }
        
        if data_type in limits:
            self.axes.set_ylim(limits[data_type])
            self.axes.set_ylabel(f"{data_type} ({self._get_unit(data_type)})", color=UI.ACCENT_COLOR)
    
    def _get_unit(self, data_type: str) -> str:
        """Get the unit string for a data type.
        
        Args:
            data_type: Type of data
            
        Returns:
            Unit string
        """
        units = {
            "Current": "A",
            "Temperature": "°C",
            "Pressure": "kPa"
        }
        return units.get(data_type, "")
    
    def set_data_type(self, data_type: str) -> None:
        """Set the data type for this plot.
        
        Args:
            data_type: New data type to plot
        """
        if data_type in PLOT_DATA_TYPES:
            self.data_type = data_type
            self._set_y_limits_for_data_type(data_type)
            logger.debug(f"Plot '{self.title}' data type changed to {data_type}")
    
    def update_plot(self, data: List[float]) -> None:
        """Update the plot with new data.
        
        Args:
            data: New data points to plot
        """
        if not data:
            return
        
        try:
            # Convert to numpy array
            y_data = np.array(data)
            
            # Validate data range
            y_data = self.signal_filter.validate_data_range(y_data, self.data_type.lower())
            
            # Create smoothed version
            smoothed_data = self.signal_filter.apply_savgol_filter(y_data)
            
            # Clear previous plots
            self.axes.clear()
            self._configure_plot_appearance()
            
            # Plot raw and smoothed data
            x_data = np.arange(len(y_data))
            self.axes.plot(x_data, y_data, label='Raw Signal', color='blue', alpha=0.7)
            self.axes.plot(x_data, smoothed_data, label='Smoothed Signal', color='red', linewidth=2)
            
            # Add legend
            self.axes.legend(facecolor='black', edgecolor=UI.ACCENT_COLOR, 
                           labelcolor='white', fontsize=8)
            
            # Update canvas
            self.canvas.draw_idle()
            
        except Exception as e:
            logger.error(f"Error updating plot '{self.title}': {e}")
    
    def clear_plot(self) -> None:
        """Clear the plot data."""
        self.axes.clear()
        self._configure_plot_appearance()
        self.canvas.draw_idle()


class PlotManager:
    """Manages multiple plot widgets and their data sources.
    
    This class coordinates multiple plots and handles data type switching
    through dropdown menus.
    """
    
    def __init__(self, parent: tk.Widget, data_buffer: SensorDataBuffer):
        """Initialize the plot manager.
        
        Args:
            parent: Parent tkinter widget
            data_buffer: Data buffer for sensor readings
        """
        self.parent = parent
        self.data_buffer = data_buffer
        self.plots: Dict[str, PlotWidget] = {}
        self.dropdowns: Dict[str, tk.StringVar] = {}
        
        self._create_plots()
        self._create_dropdown_menus()
        
        logger.info("PlotManager initialized with multiple plots")
    
    def _create_plots(self) -> None:
        """Create the plot widgets."""
        # Alpha plot (left)
        self.plots['alpha'] = PlotWidget(
            self.parent,
            "Alpha Plot",
            (0.05, 0.2)
        )
        
        # Beta plot (right)
        self.plots['beta'] = PlotWidget(
            self.parent,
            "Beta Plot",
            (0.55, 0.2)
        )
    
    def _create_dropdown_menus(self) -> None:
        """Create dropdown menus for data type selection."""
        # Alpha plot dropdown
        self.dropdowns['alpha'] = tk.StringVar()
        self.dropdowns['alpha'].set("Select Variable To Plot")
        self.dropdowns['alpha'].trace_add("write", lambda *args: self._on_alpha_selection_changed())
        
        alpha_dropdown = tk.OptionMenu(
            self.parent,
            self.dropdowns['alpha'],
            *PLOT_DATA_TYPES
        )
        self._configure_dropdown(alpha_dropdown)
        alpha_dropdown.place(relx=0.05, rely=0.1)
        
        # Beta plot dropdown
        self.dropdowns['beta'] = tk.StringVar()
        self.dropdowns['beta'].set("Select Variable To Plot")
        self.dropdowns['beta'].trace_add("write", lambda *args: self._on_beta_selection_changed())
        
        beta_dropdown = tk.OptionMenu(
            self.parent,
            self.dropdowns['beta'],
            *PLOT_DATA_TYPES
        )
        self._configure_dropdown(beta_dropdown)
        beta_dropdown.place(relx=0.55, rely=0.1)
    
    def _configure_dropdown(self, dropdown: tk.OptionMenu) -> None:
        """Configure dropdown appearance.
        
        Args:
            dropdown: Dropdown widget to configure
        """
        dropdown.config(
            activebackground="lightgrey",
            bg=UI.BACKGROUND_COLOR,
            activeforeground="black",
            fg="white",
            highlightthickness=0
        )
    
    def _on_alpha_selection_changed(self) -> None:
        """Handle alpha plot data type selection change."""
        data_type = self.dropdowns['alpha'].get()
        if data_type in PLOT_DATA_TYPES:
            self.plots['alpha'].set_data_type(data_type)
            logger.debug(f"Alpha plot data type changed to {data_type}")
    
    def _on_beta_selection_changed(self) -> None:
        """Handle beta plot data type selection change."""
        data_type = self.dropdowns['beta'].get()
        if data_type in PLOT_DATA_TYPES:
            self.plots['beta'].set_data_type(data_type)
            logger.debug(f"Beta plot data type changed to {data_type}")
    
    def update_plots(self) -> None:
        """Update all plots with current data."""
        try:
            # Get data based on plot selections
            for plot_name, plot_widget in self.plots.items():
                data_type = plot_widget.data_type
                data = self._get_data_for_type(data_type)
                
                if data:
                    plot_widget.update_plot(data)
                    
        except Exception as e:
            logger.error(f"Error updating plots: {e}")
    
    def _get_data_for_type(self, data_type: str) -> Optional[List[float]]:
        """Get data from buffer based on type.
        
        Args:
            data_type: Type of data to retrieve
            
        Returns:
            Data list or None if not available
        """
        data_getters = {
            "Current": self.data_buffer.get_tf_current_data,
            "Temperature": self.data_buffer.get_temperature_data,
            "Pressure": self.data_buffer.get_pressure_data
        }
        
        getter = data_getters.get(data_type)
        if getter:
            return getter()
        
        return None
    
    def clear_all_plots(self) -> None:
        """Clear all plots."""
        for plot in self.plots.values():
            plot.clear_plot()
        logger.info("All plots cleared")
