# AtomCraft Instrumentation and Controls - Codebase Overview

## Project Description

The AtomCraft Instrumentation and Controls system is a comprehensive Python-based control system designed for managing and monitoring fusion reactor components, specifically focusing on toroidal field (TF) coil current control and temperature monitoring. The system implements a distributed architecture using socket-based communication between PYNQ (Xilinx's Python-based framework) devices and PC-based control interfaces.

## System Architecture

### Communication Protocol
The system uses UDP socket communication across multiple ports for different data streams:
- **Port 1200**: TF Coil current data transmission (PC → PYNQ)
- **Port 1300**: Command reception (PC → PYNQ)
- **Port 1400**: Waveform data reception (PC → PYNQ)
- **Port 1500**: Temperature data transmission (PYNQ → PC)
- **Port 1600**: Pressure data transmission (PYNQ → PC)

### Key Components

#### 1. PC-Side Control (`main/pc_receiver.py`)
- **Primary Function**: Real-time data visualization and control interface
- **Features**:
  - Multi-threaded socket receivers for TF coil current and temperature data
  - Real-time plotting using Matplotlib with Tkinter GUI
  - SQLite database integration for data logging
  - Savitzky-Golay filtering for data smoothing
  - Waveform interpolation and analysis
- **Key Functions**:
  - `receive_from_pynq()`: Handles TF coil current data reception
  - `receive_temp_from_pynq()`: Manages temperature data acquisition
  - Real-time plotting with configurable update rates

#### 2. PYNQ-Side Control (`main/pynq_receiver.py`)
- **Primary Function**: Hardware interface and command execution
- **Features**:
  - Command interpretation and execution
  - Waveform data processing and mapping
  - Hardware abstraction for PMOD interfaces
  - Multi-threaded operation for concurrent data streams
- **Key Functions**:
  - `receive_commands()`: Command listener and dispatcher
  - `receive_waveform()`: Waveform data handler
  - `map_pynq_pmod()`: Hardware signal mapping

#### 3. Simple Controller Interface (`main/controller.py`)
- **Primary Function**: Basic GUI for system interaction
- **Features**:
  - Tkinter-based user interface
  - SQLite database for persistent storage
  - Simple data entry and management
- **Database Schema**: Single table for name storage with auto-incrementing IDs

## Hardware Integration

### PYNQ Board Interfaces
The system extensively uses PYNQ (Python Productivity for Zynq) framework components:

#### 1. PWM Control (`hardware/dutycycle.py`, `examples/pwm_test_notebook.py`)
- **Base Overlay**: Utilizes BaseOverlay("base.bit") for FPGA configuration
- **PWM Generation**: Pmod_PWM for precise duty cycle control
- **Hall Sensor Integration**: Arduino_Analog interface for current measurement
- **Interactive Control**: Button-based duty cycle adjustment (±1% increments)

#### 2. Sensor Interfaces
- **Hall Sensors**: Arduino Grove A1 connector for current sensing
- **Temperature Monitoring**: Integrated sensor data acquisition
- **Real-time Data Collection**: Configurable sampling rates and data buffering

### Arduino Integration (`Control/Prototypes/TF_Coil_PID.ino`)
Complementary Arduino-based PID controller implementation:
- **Hardware**: H-bridge control with dual PWM outputs (pins 5, 11)
- **Sensor Processing**: Hall sensor calibration and current conversion
- **PID Control**: Configurable proportional, integral, and derivative gains
- **Data Logging**: Fixed-size arrays for current and PWM data capture
- **Timer Configuration**: Custom timer settings for precise PWM generation

## Control Algorithms

### PID Implementation
The Arduino code implements a comprehensive PID controller:
```cpp
// PID Parameters
float kp = 5;        // Proportional gain
float ki = 0.00010;  // Integral gain  
float kd = 0;        // Derivative gain
```

### Signal Processing
Python implementation includes advanced signal processing:
- **Savitzky-Golay Filtering**: Noise reduction while preserving signal characteristics
- **Interpolation**: scipy.interpolate.interp1d for waveform reconstruction
- **Real-time Analysis**: Continuous data stream processing

## Data Management

### Database Structure
SQLite databases store operational data:
- **names.db**: User interface data storage
- **commands.db**: Command history and logging

### Data Flow
1. **Sensor Data**: Hardware sensors → PYNQ → UDP sockets → PC visualization
2. **Control Commands**: PC interface → UDP sockets → PYNQ → Hardware actuation
3. **Waveform Data**: PC generation → UDP transmission → PYNQ processing → Hardware output

## Development Environment

### Dependencies (`requirements.txt`)
- **Core Libraries**: numpy (2.1.1), scipy (1.14.1), matplotlib (3.9.2)
- **GUI Framework**: tkinter (built-in)
- **Network**: Standard socket library
- **Data Processing**: pandas-like functionality through numpy

### Platform Support (`Brewfile`)
macOS development environment with:
- Python 3.12 with Tkinter support
- JupyterLab for notebook development
- Node.js 18 LTS for potential web interfaces
- Git for version control

## Testing and Examples

### Prototype Development (`Control/Prototypes/`)
- **hall_sensor_notebook.py**: Basic sensor data acquisition and plotting
- **TF_Coil_test.py**: Comprehensive TF coil control testing with PID implementation
- **TF_Coil_PID.ino**: Arduino-based hardware control validation

### Educational Examples (`examples/`)
- **practice_pynq_notebook.py**: PYNQ board familiarization with LED and button control
- **pwm_test_notebook.py**: PWM signal generation and hall sensor integration testing

## Key Features

### Real-time Monitoring
- Multi-threaded data acquisition from multiple sensor streams
- Live plotting with configurable update rates (default 100ms)
- Data smoothing and filtering for noise reduction

### Distributed Control
- Network-based communication between PC and embedded systems
- Fault-tolerant socket communication with timeout handling
- Modular architecture supporting multiple hardware platforms

### User Interface
- Intuitive Tkinter-based control panels
- Real-time data visualization with matplotlib integration
- Database-backed configuration and data storage

### Hardware Abstraction
- Unified interface for different hardware platforms (PYNQ, Arduino)
- Configurable sensor interfaces and control outputs
- Scalable architecture for additional peripheral integration

## Deployment

### Execution
The system provides a dedicated runner script (`run_pc_receiver.py`) that:
- Manages virtual environment activation
- Ensures dependency availability
- Provides error handling and user feedback
- Supports both development and production deployments

### Configuration
- Centralized configuration through constants in each module
- Flexible port assignments for network communication
- Configurable PID parameters and sensor calibration values

## Future Development Considerations

The architecture supports extension for:
- Additional sensor types and measurement capabilities
- Enhanced control algorithms and feedback systems
- Web-based interfaces for remote monitoring
- Integration with larger fusion reactor control systems
- Advanced data analysis and machine learning capabilities

## Technical Specifications

- **Programming Languages**: Python 3.12, C++ (Arduino), VHDL/Verilog (FPGA)
- **Communication Protocol**: UDP over Ethernet/WiFi
- **Real-time Performance**: Sub-100ms response times
- **Data Acquisition**: Up to 10 kHz sampling rates
- **Control Resolution**: 16-bit PWM resolution, ±1% duty cycle precision
- **Platform Support**: macOS, Linux (PYNQ), Arduino ecosystem

This codebase represents a sophisticated embedded control system suitable for research and educational applications in fusion energy and plasma physics.

## Solenoid Control Integration

### New Solenoid System (`hardware/Solenoid.ino`)
Arduino-based solenoid valve control with integrated pressure monitoring and PID control:

#### Hardware Components:
- **WiFi Communication**: Arduino R4 WiFi for network connectivity
- **Pressure Sensor**: Connected to analog pin A1 for system pressure monitoring
- **Solenoid Valve**: Digital pin 4 controls valve open/close operations
- **PID Controller**: Automated pressure regulation with configurable parameters

#### Key Features:
- **Network Commands**: UDP socket communication on port 2390
- **Manual Control**: Direct valve operation with configurable timing
- **Automatic Control**: PID-based pressure regulation (setpoint: 110 units)
- **Data Streaming**: Real-time pressure and status feedback to PC
- **Safety Interlocks**: Timeout protection and error handling

#### Communication Protocol:
- **Command Port**: 2390 (receives commands from PC)
- **Data Port**: 2391 (sends pressure/status to PC)
- **Commands**:
  - `"o"` - Open valve with preset duration
  - `"pressure"` - Request current pressure reading  
  - `"<milliseconds>"` - Set valve open duration (e.g., "3000")

#### PID Parameters:
```cpp
double Kp = 2.0;   // Proportional gain
double Ki = 5.0;   // Integral gain  
double Kd = 1.9;   // Derivative gain
```

### PC Integration (`main/pc_receiver.py`)
The solenoid system follows the established integration pattern:

#### New Functions:
- `send_solenoid_command(command)` - Send control commands to Arduino
- `receive_solenoid_pressure()` - Monitor pressure and status data
- `handle_solenoid_commands()` - Process GUI commands
- `update_solenoid_display()` - Update GUI elements

#### GUI Integration:
- **Pressure Display**: Real-time pressure monitoring (third measurement panel)
- **Status Display**: Valve position indicator (fourth measurement panel)
- **Command Interface**: Text-based command entry with acknowledgment

#### Available Commands:
- `"solenoid test"` - Initialize solenoid command interface
- `"solenoid open"` - Trigger valve opening sequence
- `"solenoid time <ms>"` - Configure valve open duration
- `"solenoid pressure"` - Request current pressure reading

### Network Configuration
Update the following IP addresses for your network setup:

**In pc_receiver.py:**
```python
SOLENOID_HOST = '192.168.1.100'  # Arduino IP address
```

**In Solenoid.ino:**
```cpp
char ssid[] = "YourNetworkName";
char pass[] = "YourPassword";
Udp.beginPacket("192.168.1.100", 2391); // PC IP for data transmission
```

### Testing and Validation
Use `examples/solenoid_test.py` for integration testing:
- **Hardware Test Mode**: Direct communication with Arduino
- **Simulation Mode**: Generate test data for PC receiver validation
- **Network Diagnostics**: Connection and command response verification

This integration maintains the distributed architecture while adding pressure control capabilities essential for fusion reactor safety systems.

## Library Dependencies and Technology Stack

### Core Python Libraries

#### **Standard Library Components**
- **`socket`** - UDP/TCP network communication for distributed system architecture
  - *Why used*: Essential for real-time communication between PC controller and PYNQ/Arduino devices across network
- **`threading`** - Multi-threaded operation for concurrent data acquisition and GUI responsiveness
  - *Why used*: Prevents GUI freezing while receiving continuous sensor data streams; enables parallel processing of multiple data sources
- **`time`** - Timing operations, delays, and timestamp management
  - *Why used*: Critical for control loop timing, data sampling rates, and coordinated system operations
- **`sqlite3`** - Lightweight database for command history and configuration storage
  - *Why used*: Provides persistent storage without external database dependencies; perfect for logging commands and system state
- **`struct`** - Binary data packing/unpacking for efficient network protocols
  - *Why used*: Enables compact, fast transmission of numerical data (floats) over UDP for real-time performance
- **`contextlib`** - Context management for resource handling and exception suppression
  - *Why used*: Elegant handling of socket timeouts and resource cleanup in network operations
- **`sys`** - System-specific parameters and functions
  - *Why used*: Platform detection and system-level operations for cross-platform compatibility
- **`os`** - Operating system interface for file path operations
  - *Why used*: File system navigation and path handling for configuration files and virtual environments
- **`subprocess`** - Process spawning for virtual environment management
  - *Why used*: Automated activation of Python virtual environments in deployment scripts
- **`re`** - Regular expressions for command parsing and validation
  - *Why used*: Robust parsing of user commands and waveform data validation

#### **Scientific Computing Stack**
- **`numpy` (2.1.1)** - Numerical computing foundation
  - Array operations for sensor data processing
  - Linear algebra operations for signal analysis
  - Data type management for efficient memory usage
  - Mathematical functions for control algorithms
  - *Why used*: Essential for efficient processing of continuous sensor data streams; provides C-speed array operations for real-time performance

- **`scipy` (1.14.1)** - Advanced scientific computing
  - `scipy.signal.savgol_filter` - Savitzky-Golay filtering for noise reduction
  - `scipy.interpolate.interp1d` - Linear interpolation for waveform generation
  - Signal processing algorithms for data conditioning
  - Mathematical optimization for control parameter tuning
  - *Why used*: Sophisticated signal processing needed for noisy sensor data; interpolation creates smooth control waveforms from discrete points

- **`matplotlib` (3.9.2)** - Comprehensive plotting and visualization
  - `matplotlib.pyplot` - High-level plotting interface
  - `matplotlib.figure.Figure` - Object-oriented plotting for GUI integration
  - `matplotlib.backends.backend_tkagg.FigureCanvasTkAgg` - Tkinter integration
  - `matplotlib.backends._backend_tk.NavigationToolbar2Tk` - Interactive plot navigation
  - Real-time data visualization with custom styling and themes
  - *Why used*: Critical for real-time monitoring of fusion reactor parameters; researchers need visual feedback for system behavior analysis

#### **GUI Framework**
- **`tkinter`** - Built-in GUI toolkit (Python standard library)
  - Main application window and layout management
  - Widget creation (Entry, Button, Label, Listbox, OptionMenu)
  - Event handling and user interaction
  - Custom styling with color schemes and fonts
  - Frame-based layout organization
  - *Why used*: No external dependencies needed; perfect for research environment where installation complexity must be minimized; adequate performance for control interface needs

#### **Data Processing and Analysis**
- **`collections.defaultdict`** - Specialized dictionary for data organization
  - *Why used*: Simplifies handling of grouped sensor data without KeyError exceptions
- **`heapq`** - Heap queue algorithm for priority data handling
  - *Why used*: Efficient priority-based processing of time-critical control commands
- **`random`** - Random number generation for testing and simulation
  - *Why used*: Essential for generating realistic test data when hardware isn't available; enables development without physical reactor components

### Hardware Integration Libraries

#### **PYNQ Framework (Xilinx Python Productivity for Zynq)**
- **`pynq`** - Core PYNQ library for FPGA interaction
  - `pynq.GPIO` - General Purpose I/O control
  - `pynq.overlays.base.BaseOverlay` - Base FPGA overlay management
  - Hardware abstraction layer for Zynq SoC devices
  - *Why used*: Enables Python control of FPGA hardware without low-level VHDL/Verilog programming; critical for rapid prototyping of control algorithms

- **`pynq.lib`** - PYNQ peripheral libraries
  - `pynq.lib.Pmod_PWM` - Pulse Width Modulation control
  - `pynq.lib.arduino.Arduino_Analog` - Analog sensor interfaces
  - `pynq.lib.arduino.ARDUINO_GROVE_A1` - Grove connector definitions
  - Standardized hardware interfaces for rapid prototyping
  - *Why used*: Provides high-level abstraction for complex hardware interfaces; eliminates need for custom driver development

#### **Arduino Libraries (C++)**
- **`WiFiS3.h`** - WiFi connectivity for Arduino R4 WiFi
  - *Why used*: Enables wireless communication for distributed solenoid control without physical cable constraints
- **`WiFiUdp.h`** - UDP protocol implementation
  - *Why used*: Low-latency communication protocol essential for real-time control responses
- **`PID_v1.h`** - PID controller library for automatic control loops
  - *Why used*: Proven, tested PID implementation for precise pressure control; avoids reinventing complex control algorithms

### Development and Deployment Tools

#### **Package Management**
- **`pip`** - Python package installer and dependency management
  - *Why used*: Standard Python package management; ensures consistent library versions across development environments
- **`requirements.txt`** - Dependency specification and version control
  - *Why used*: Reproducible environment setup critical for research collaboration and deployment
- **Homebrew (`Brewfile`)** - macOS package management for system dependencies
  - *Why used*: Manages system-level dependencies that pip cannot install; ensures complete development environment setup

#### **Development Environment**
- **Python 3.12** - Latest stable Python interpreter
  - *Why used*: Latest performance improvements and language features; maintains compatibility with scientific libraries
- **JupyterLab** - Interactive development and notebook support
  - *Why used*: Essential for research environment; enables interactive development and documentation of experiments
- **Node.js 18 LTS** - JavaScript runtime for potential web interfaces
  - *Why used*: Future-proofing for web-based monitoring interfaces; enables modern web development if needed
- **Git** - Version control and collaboration
  - *Why used*: Essential for collaborative research development; tracks changes in complex multi-file system
- **SQLite3** - Embedded database engine
  - *Why used*: Zero-configuration database for persistent storage without server complexity

#### **System Libraries (macOS via Homebrew)**
- **`python-networkx`** - Network analysis and graph theory
  - *Why used*: Potential future use for analyzing complex system interconnections and data flow optimization
- **`tcl-tk`** - Tkinter GUI toolkit dependencies
  - *Why used*: Required system-level libraries for Tkinter GUI functionality
- **`python-tk@3.12`** - Python-specific Tkinter bindings
  - *Why used*: Ensures Tkinter compatibility with specific Python version

### Network Communication Stack

#### **Protocol Implementation**
- **UDP (User Datagram Protocol)** - Low-latency, connectionless communication
  - *Why used*: Minimal overhead essential for real-time control; acceptable packet loss in exchange for speed
- **TCP (Transmission Control Protocol)** - Reliable connection-based communication (potential future use)
  - *Why used*: Future reliability option for critical command transmission where packet loss is unacceptable
- **WiFi (IEEE 802.11)** - Wireless network connectivity for Arduino devices
  - *Why used*: Eliminates physical cable constraints for distributed sensor/actuator placement

#### **Data Serialization**
- **`struct` module** - Binary data packing for efficient network transmission
  - *Why used*: Compact binary format reduces network bandwidth; faster than text-based protocols for numerical data
- **String encoding/decoding** - UTF-8 text-based command protocols
  - *Why used*: Human-readable commands for debugging and development; easier troubleshooting than binary protocols
- **JSON** (via config files) - Human-readable configuration format
  - *Why used*: Easy manual editing of configuration files; standard format for structured data

### Testing and Simulation Libraries

#### **Built-in Testing Components**
- **`random`** - Synthetic data generation for system testing
  - *Why used*: Enables development and testing without physical hardware; simulates realistic sensor variations
- **`time.sleep()`** - Timing control for simulation loops
  - *Why used*: Realistic timing simulation for testing system behavior under various conditions
- **Custom simulation functions** - Hardware-in-the-loop testing capabilities
  - *Why used*: Validates system behavior before deploying to actual fusion reactor hardware

### Performance and Optimization

#### **Efficiency Considerations**
- **NumPy vectorization** - Optimized array operations in C
  - *Why used*: Achieves near-C performance for array operations while maintaining Python's ease of use
- **Threading** - Concurrent I/O operations without GIL blocking
  - *Why used*: I/O-bound operations (network, file) release GIL, enabling true parallelism for data acquisition
- **Socket timeouts** - Non-blocking network operations
  - *Why used*: Prevents system freezing when hardware becomes unresponsive; maintains system stability
- **Data structure optimization** - Fixed-size arrays and efficient collections
  - *Why used*: Predictable memory usage critical for long-running reactor monitoring systems

### Cross-Platform Compatibility

#### **Platform-Specific Elements**
- **macOS optimization** - Homebrew package management and system integration
  - *Why used*: Streamlined development environment setup for macOS-based research workstations
- **Linux compatibility** - PYNQ framework requires Linux-based systems
  - *Why used*: PYNQ boards run embedded Linux; essential for FPGA-based control systems
- **Arduino ecosystem** - Cross-platform embedded development support
  - *Why used*: Hardware abstraction enables deployment across different microcontroller platforms
- **Network protocols** - Platform-agnostic UDP/TCP communication
  - *Why used*: Enables heterogeneous system integration regardless of underlying operating systems

### Library Integration Architecture

The system demonstrates sophisticated library integration:
1. **Scientific Stack** - NumPy → SciPy → Matplotlib pipeline for data processing
2. **GUI Integration** - Matplotlib backends embedded in Tkinter interface
3. **Hardware Abstraction** - PYNQ libraries providing unified embedded system interface
4. **Network Layer** - Standard socket libraries enabling distributed architecture
5. **Database Integration** - SQLite providing persistent storage without external dependencies

This technology stack provides a robust foundation for research-oriented fusion reactor instrumentation, balancing development velocity with performance requirements while maintaining platform compatibility and extensibility for future enhancements.

## Future Development Considerations
