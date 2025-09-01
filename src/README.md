# AtomCraft Refactored Code Structure

This directory contains the refactored version of the AtomCraft control system, designed to be more maintainable and understandable for new developers.

## Key Improvements

### 1. **Modular Architecture**
- Separated concerns into distinct modules
- Clear separation between GUI, networking, and business logic
- Easier to test and maintain individual components

### 2. **Improved Code Organization**
```
refactored/
├── core/                 # Core business logic
│   ├── __init__.py
│   ├── data_manager.py   # Data handling and storage
│   ├── signal_processor.py # Signal processing utilities
│   └── config.py         # Configuration constants
├── networking/           # Network communication
│   ├── __init__.py
│   ├── pc_server.py      # PC-side networking
│   ├── pynq_client.py    # PYNQ-side networking
│   └── protocols.py      # Communication protocols
├── gui/                  # User interface
│   ├── __init__.py
│   ├── main_window.py    # Main application window
│   ├── plot_widgets.py   # Plotting components
│   └── control_panels.py # Control interface panels
├── hardware/             # Hardware interfaces
│   ├── __init__.py
│   ├── sensors.py        # Sensor interfaces
│   └── actuators.py      # Actuator controls
└── utils/                # Utilities and helpers
    ├── __init__.py
    ├── logging_config.py # Logging setup
    └── exceptions.py     # Custom exceptions
```

### 3. **Better Error Handling**
- Comprehensive exception handling
- Proper logging throughout the application
- Graceful degradation when components fail

### 4. **Clear Documentation**
- Comprehensive docstrings for all classes and methods
- Type hints for better IDE support
- Clear naming conventions

### 5. **Configuration Management**
- Centralized configuration
- Easy to modify settings without code changes
- Environment-specific configurations

## Getting Started

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the PC Controller**:
   ```bash
   python pc_controller.py
   ```

3. **Run the PYNQ Controller**:
   ```bash
   python pynq_controller.py
   ```

## Architecture Overview

The refactored system follows a clean architecture pattern:

- **Presentation Layer**: GUI components handle user interaction
- **Application Layer**: Core business logic and orchestration
- **Infrastructure Layer**: Networking, database, and hardware interfaces

This separation makes the code easier to understand, test, and maintain.
