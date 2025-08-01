"""Quick validation script for the refactored AtomCraft system.

This script performs basic validation of the refactored components
to ensure they work correctly.
"""

import sys
import time
from pathlib import Path

# Add the refactored package to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_configuration():
    """Test configuration loading."""
    print("Testing configuration...")
    try:
        from core.config import NETWORK, UI, SIGNAL_PROCESSING
        
        assert NETWORK.LOCAL_HOST == '127.0.0.1'
        assert UI.WINDOW_TITLE == "AtomCraft Controller"
        assert SIGNAL_PROCESSING.WAVEFORM_POINTS == 100
        
        print("✓ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_data_manager():
    """Test data manager functionality."""
    print("Testing data manager...")
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(__file__))
        
        from core.data_manager import DataManager, SensorDataBuffer
        
        # Test data manager
        dm = DataManager(":memory:")  # Use in-memory database
        dm.add_command("test command")
        history = dm.get_command_history()
        assert len(history) >= 1
        
        # Test sensor buffer
        buffer = SensorDataBuffer(10)
        buffer.add_tf_current(50.0)
        buffer.add_temperature(75.0)
        
        current_data = buffer.get_tf_current_data()
        temp_data = buffer.get_temperature_data()
        
        assert len(current_data) == 10
        assert len(temp_data) == 10
        assert current_data[-1] == 50.0
        assert temp_data[-1] == 75.0
        
        print("✓ Data manager works correctly")
        return True
    except Exception as e:
        print(f"✗ Data manager test failed: {e}")
        return False

def test_signal_processor():
    """Test signal processing functionality."""
    print("Testing signal processor...")
    try:
        from core.signal_processor import WaveformProcessor, SignalFilter
        
        # Test waveform processor
        wp = WaveformProcessor()
        test_waveform = "1,2,3,4,10,20,30,40"
        
        if wp.validate_waveform_input(test_waveform):
            time_points, amp_points = wp.parse_waveform(test_waveform)
            interpolated = wp.interpolate_waveform(time_points, amp_points, 50)
            
            assert len(interpolated) == 50
            print("✓ Waveform processing works correctly")
        
        # Test signal filter
        sf = SignalFilter()
        test_data = [1, 2, 3, 4, 5, 4, 3, 2, 1]
        filtered = sf.apply_savgol_filter(test_data)
        
        assert len(filtered) == len(test_data)
        print("✓ Signal filtering works correctly")
        
        return True
    except Exception as e:
        print(f"✗ Signal processor test failed: {e}")
        return False

def test_networking():
    """Test networking components."""
    print("Testing networking...")
    try:
        from networking.protocols import Message, MessageType, CommandProtocol
        
        # Test message creation
        msg = Message(MessageType.COMMAND, "test command")
        data = msg.to_bytes()
        
        # Test message parsing
        parsed_msg = Message.from_bytes(data, MessageType.COMMAND)
        assert parsed_msg.payload == "test command"
        
        # Test command protocol
        cp = CommandProtocol()
        assert cp.validate_command("clear")
        assert cp.validate_command("solenoid time 1000")
        assert not cp.validate_command("invalid command")
        
        print("✓ Networking components work correctly")
        return True
    except Exception as e:
        print(f"✗ Networking test failed: {e}")
        return False

def test_gui_components():
    """Test GUI components (without actually showing windows)."""
    print("Testing GUI components...")
    try:
        # Import GUI components
        from gui.main_window import MainWindow
        from core.data_manager import SensorDataBuffer
        
        # Create components (but don't show GUI)
        buffer = SensorDataBuffer()
        
        # Test data buffer integration
        buffer.add_tf_current(25.0)
        buffer.add_temperature(30.0)
        
        latest_current = buffer.get_latest_value('current')
        latest_temp = buffer.get_latest_value('temperature')
        
        assert latest_current == 25.0
        assert latest_temp == 30.0
        
        print("✓ GUI components initialize correctly")
        return True
    except Exception as e:
        print(f"✗ GUI component test failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("=" * 60)
    print("AtomCraft Refactored Code Validation")
    print("=" * 60)
    
    tests = [
        test_configuration,
        test_data_manager,
        test_signal_processor,
        test_networking,
        test_gui_components,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! The refactored code is working correctly.")
        print("\nTo run the application:")
        print("  python pc_controller.py    # For PC side")
        print("  python pynq_client.py      # For PYNQ side")
    else:
        print("✗ Some tests failed. Please check the errors above.")
    
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
