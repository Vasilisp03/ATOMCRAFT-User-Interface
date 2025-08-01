"""Signal processing utilities for the AtomCraft system.

This module provides signal processing functions including filtering,
interpolation, and waveform generation.
"""

import numpy as np
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d
from typing import List, Tuple, Union

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import SIGNAL_PROCESSING
from utils.exceptions import DataProcessingException
from utils.logging_config import logger


class WaveformProcessor:
    """Handles waveform processing and interpolation operations."""
    
    def __init__(self):
        """Initialize the waveform processor."""
        self.config = SIGNAL_PROCESSING
        logger.info("WaveformProcessor initialized")
    
    def validate_waveform_input(self, waveform_str: str) -> bool:
        """Validate waveform input format.
        
        Args:
            waveform_str: Comma-separated waveform string
            
        Returns:
            True if valid, False otherwise
        """
        try:
            parts = waveform_str.split(',')
            
            # Should have exactly 8 values (4 time points + 4 amplitude points)
            if len(parts) != 8:
                return False
            
            # All parts should be numeric
            for part in parts:
                float(part.strip())
            
            return True
            
        except (ValueError, AttributeError):
            return False
    
    def parse_waveform(self, waveform_str: str) -> Tuple[np.ndarray, np.ndarray]:
        """Parse waveform string into time and amplitude arrays.
        
        Args:
            waveform_str: Comma-separated waveform string (t1,t2,t3,t4,a1,a2,a3,a4)
            
        Returns:
            Tuple of (time_points, amplitude_points)
            
        Raises:
            DataProcessingException: If waveform format is invalid
        """
        if not self.validate_waveform_input(waveform_str):
            raise DataProcessingException(f"Invalid waveform format: {waveform_str}")
        
        try:
            values = [float(x.strip()) for x in waveform_str.split(',')]
            time_points = np.array(values[:4])
            amplitude_points = np.array(values[4:8])
            
            logger.debug(f"Parsed waveform: time={time_points}, amplitude={amplitude_points}")
            return time_points, amplitude_points
            
        except Exception as e:
            raise DataProcessingException(f"Failed to parse waveform: {e}")
    
    def interpolate_waveform(
        self,
        time_points: np.ndarray,
        amplitude_points: np.ndarray,
        num_points: int = None
    ) -> np.ndarray:
        """Interpolate waveform to create smooth curve.
        
        Args:
            time_points: Time coordinate points
            amplitude_points: Amplitude values at time points
            num_points: Number of interpolated points (default from config)
            
        Returns:
            Interpolated amplitude values
            
        Raises:
            DataProcessingException: If interpolation fails
        """
        if num_points is None:
            num_points = self.config.WAVEFORM_POINTS
        
        try:
            # Create interpolation function
            interpolator = interp1d(
                time_points,
                amplitude_points,
                kind='linear',
                bounds_error=False,
                fill_value='extrapolate'
            )
            
            # Generate new time points
            time_new = np.linspace(
                time_points[0],
                time_points[-1],
                num=num_points,
                endpoint=True
            )
            
            # Interpolate values
            interpolated_values = interpolator(time_new)
            
            logger.debug(f"Interpolated waveform to {num_points} points")
            return interpolated_values
            
        except Exception as e:
            raise DataProcessingException(f"Waveform interpolation failed: {e}")
    
    def process_waveform_command(self, waveform_str: str) -> List[str]:
        """Process complete waveform command from string to interpolated values.
        
        Args:
            waveform_str: Input waveform string
            
        Returns:
            List of interpolated values as strings
            
        Raises:
            DataProcessingException: If processing fails
        """
        try:
            # Parse input
            time_points, amplitude_points = self.parse_waveform(waveform_str)
            
            # Interpolate
            interpolated = self.interpolate_waveform(time_points, amplitude_points)
            
            # Convert to strings for transmission
            result = [str(float(val)) for val in interpolated]
            
            logger.info(f"Processed waveform command: {len(result)} points generated")
            return result
            
        except Exception as e:
            raise DataProcessingException(f"Waveform processing failed: {e}")


class SignalFilter:
    """Handles signal filtering operations."""
    
    def __init__(self):
        """Initialize the signal filter."""
        self.config = SIGNAL_PROCESSING
        logger.info("SignalFilter initialized")
    
    def apply_savgol_filter(
        self,
        data: Union[List[float], np.ndarray],
        window_length: int = None,
        polynomial_order: int = None
    ) -> np.ndarray:
        """Apply Savitzky-Golay filter to smooth data.
        
        Args:
            data: Input data to filter
            window_length: Filter window length (default from config)
            polynomial_order: Polynomial order (default from config)
            
        Returns:
            Filtered data
            
        Raises:
            DataProcessingException: If filtering fails
        """
        if window_length is None:
            window_length = self.config.FILTER_WINDOW_LENGTH
        if polynomial_order is None:
            polynomial_order = self.config.FILTER_POLYNOMIAL_ORDER
        
        try:
            # Convert to numpy array if needed
            if isinstance(data, list):
                data = np.array(data)
            
            # Ensure minimum data length
            if len(data) < window_length:
                logger.warning(f"Data length ({len(data)}) less than window length ({window_length})")
                return data
            
            # Apply filter
            filtered_data = savgol_filter(data, window_length, polynomial_order)
            
            logger.debug(f"Applied Savitzky-Golay filter: window={window_length}, order={polynomial_order}")
            return filtered_data
            
        except Exception as e:
            raise DataProcessingException(f"Signal filtering failed: {e}")
    
    def validate_data_range(
        self,
        data: Union[List[float], np.ndarray],
        data_type: str
    ) -> np.ndarray:
        """Validate and clamp data to expected ranges.
        
        Args:
            data: Input data to validate
            data_type: Type of data ('current', 'temperature', 'pressure')
            
        Returns:
            Validated and clamped data
        """
        # Convert to numpy array
        if isinstance(data, list):
            data = np.array(data)
        
        # Define ranges
        ranges = {
            'current': (self.config.MIN_CURRENT, self.config.MAX_CURRENT),
            'temperature': (self.config.MIN_TEMPERATURE, self.config.MAX_TEMPERATURE),
            'pressure': (0.0, 1000.0)  # Reasonable pressure range
        }
        
        if data_type in ranges:
            min_val, max_val = ranges[data_type]
            data = np.clip(data, min_val, max_val)
            logger.debug(f"Validated {data_type} data range: [{min_val}, {max_val}]")
        
        return data


class DataAnalyzer:
    """Provides data analysis utilities."""
    
    def __init__(self):
        """Initialize the data analyzer."""
        logger.info("DataAnalyzer initialized")
    
    def calculate_statistics(self, data: Union[List[float], np.ndarray]) -> dict:
        """Calculate basic statistics for data.
        
        Args:
            data: Input data
            
        Returns:
            Dictionary with statistics (mean, std, min, max, etc.)
        """
        if isinstance(data, list):
            data = np.array(data)
        
        if len(data) == 0:
            return {'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'count': 0}
        
        stats = {
            'mean': float(np.mean(data)),
            'std': float(np.std(data)),
            'min': float(np.min(data)),
            'max': float(np.max(data)),
            'count': len(data)
        }
        
        # Add median and percentiles if enough data
        if len(data) > 1:
            stats.update({
                'median': float(np.median(data)),
                'p25': float(np.percentile(data, 25)),
                'p75': float(np.percentile(data, 75))
            })
        
        return stats
    
    def detect_anomalies(
        self,
        data: Union[List[float], np.ndarray],
        threshold_std: float = 3.0
    ) -> List[int]:
        """Detect anomalies in data using standard deviation threshold.
        
        Args:
            data: Input data
            threshold_std: Number of standard deviations for anomaly threshold
            
        Returns:
            List of indices where anomalies were detected
        """
        if isinstance(data, list):
            data = np.array(data)
        
        if len(data) < 3:
            return []
        
        mean = np.mean(data)
        std = np.std(data)
        
        if std == 0:
            return []
        
        # Find points beyond threshold
        z_scores = np.abs((data - mean) / std)
        anomaly_indices = np.where(z_scores > threshold_std)[0].tolist()
        
        if anomaly_indices:
            logger.warning(f"Detected {len(anomaly_indices)} anomalies in data")
        
        return anomaly_indices
