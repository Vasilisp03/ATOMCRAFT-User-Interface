#!/usr/bin/env python3
"""
Solenoid Test Script
Test script to validate solenoid integration with AtomCraft system
"""

import socket
import time
import threading

# Solenoid Arduino configuration
SOLENOID_HOST = '192.168.1.100'  # Replace with your Arduino's IP
SOLENOID_PORT = 2390

def test_solenoid_communication():
    """Test basic communication with solenoid system"""
    print("Testing Solenoid Communication...")
    
    try:
        # Test basic connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5.0)
        
        # Test pressure reading
        print("Requesting pressure reading...")
        sock.sendto("pressure".encode(), (SOLENOID_HOST, SOLENOID_PORT))
        
        response, addr = sock.recvfrom(1024)
        print(f"Response: {response.decode()}")
        
        # Test solenoid opening
        print("Testing solenoid open command...")
        sock.sendto("o".encode(), (SOLENOID_HOST, SOLENOID_PORT))
        
        response, addr = sock.recvfrom(1024)
        print(f"Response: {response.decode()}")
        
        # Test time setting
        print("Setting solenoid time to 3000ms...")
        sock.sendto("3000".encode(), (SOLENOID_HOST, SOLENOID_PORT))
        
        response, addr = sock.recvfrom(1024)
        print(f"Response: {response.decode()}")
        
        sock.close()
        print("Solenoid communication test completed successfully!")
        
    except Exception as e:
        print(f"Solenoid communication test failed: {e}")

def simulate_solenoid_data():
    """Simulate solenoid data for testing without hardware"""
    print("Starting simulated solenoid data stream...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    pressure = 100.0
    status = "CLOSED"
    
    try:
        while True:
            # Simulate pressure variations
            pressure += (time.time() % 10 - 5) * 0.5
            pressure = max(80, min(120, pressure))  # Keep within realistic range
            
            # Simulate status changes
            if time.time() % 20 < 2:  # Open for 2 seconds every 20 seconds
                status = "OPEN"
            else:
                status = "CLOSED"
            
            # Send data packet
            data_packet = f"{pressure:.2f},{status}"
            sock.sendto(data_packet.encode(), ('127.0.0.1', 2391))
            
            print(f"Sent: Pressure={pressure:.2f}, Status={status}")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nSimulation stopped")
        sock.close()

if __name__ == "__main__":
    print("AtomCraft Solenoid Integration Test")
    print("===================================")
    print()
    print("Choose test mode:")
    print("1. Test real hardware communication")
    print("2. Simulate solenoid data for PC receiver testing")
    
    choice = input("Enter choice (1 or 2): ")
    
    if choice == "1":
        test_solenoid_communication()
    elif choice == "2":
        simulate_solenoid_data()
    else:
        print("Invalid choice")
