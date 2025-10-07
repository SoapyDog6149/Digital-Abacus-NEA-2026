import espnow
import time


def b_str_conv(byte_data):
    string_data = byte_data.decode("utf-8")
    return string_data

##ESPNOW BOOT##

# Initialize ESP-NOW
import network
# Initialize WLAN
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.disconnect()
#sta.config(channel=1)  # Set explicit channel
#sta.config(pm=network.PM_NONE)  # Disable power saving

# Initialize ESP-NOW
e = espnow.ESPNow()
try:
    e.active(True)
except OSError as err:
    print("Failed to initialize ESP-NOW:", err)
    raise

# CYD MAC address
CYD_mac = b'\xec\xe3\x34\x1f\xb0\xc0'  # CYD's MAC
# CYD_mac = b'\xff\xff\xff\xff\xff\xff'  # Broadcast for testing

# Add peer
try:
    e.add_peer(CYD_mac)
except OSError as err:
    print("Failed to add peer:", err)
    raise

received_pong = False

def send_ping(m_msg):  # Send and print
    if e.send(CYD_mac, m_msg, True):
        print(f"Sent to CYD: {m_msg}")
    else:
        print("Failed to send (returned False)")

while not received_pong:
    try:
        main_message = "main ping"
        send_ping(main_message)

        # Listen with timeout (wait up to 2 seconds for response)
        host, cyd_msg = e.recv(2000)

        if cyd_msg is not None:
            print(f"Received from {host}: {b_str_conv(cyd_msg)}")
            n_cyd_msg = b_str_conv(cyd_msg)
            if n_cyd_msg == "cyd pong":
                received_pong = True
                break
        else:
            print("No response in timeout")

        time.sleep(1)  # Retry every 1 second if needed

    except OSError as err:
        print("Error:", err)
        time.sleep(5)

print("Boot complete!")


from dcmotor import DCMotor
from machine import Pin, PWM

global dc_motor
frequency = 15000 #init the PWM frequency

#init GPIO and motor object
pin1 = Pin(12, Pin.OUT) #GPIO 12
pin2 = Pin(14, Pin.OUT) #GPIO 14
enable = PWM(Pin(13), frequency) #GPIO 13

dc_motor = DCMotor(pin1, pin2, enable)
#dc_motor = DCMotor(pin1, pin2, enable, 350, 1023) #use if need to use min/max duty values

### ESPNOW listen and sending functions for ESP32 (Main) ###

def listen_msg():
    try:
        print("Constantly Listening for Spin...")
        host, cyd_msg = e.recv(2000)  # Listen with a 2-second timeout
        if cyd_msg is not None:
            host_str = ':'.join(f'{b:02x}' for b in host) if host else 'Unknown'
            msg_str = cyd_msg.decode('utf-8') if cyd_msg else ''
            print(f"Received from {host_str}: {msg_str}")
            
            if msg_str == "spin arrow":  # If received matching message
                return True
        return False  # No message or not matching
    except OSError as err:
        print(f"Listen error: {err}")
        return False

def send_message(msg):
    try:
        success = e.send(CYD_mac, msg.encode('utf-8'), True)
        if success:
            print(f"Sent to CYD: {msg}")
            return True
        else:
            print("Failed to send (returned False)")
            return False
    except OSError as err:
        print(f"Send error (OSError: {err})")
        return False

import random
def main_program():
    global dc_motor
    spin_status = listen_msg()
    if spin_status == True:
        spin_duration = random.uniform(5,10) #random float from 2 to 5 in seconds
        print(f"Spin Duration is {spin_duration:.2f}s")
        spin_power = random.randint(40,90) #spin power one off rand int 40% - 90%
        print(f"Spin Power is {spin_power}%")
        
        start_time = time.time()
        time_met = False
        while not time_met: #spin motor until time met
            dc_motor.forward(spin_power)
            current_time = time.time()
            if (current_time - start_time) >= spin_duration:
                time_met = True
                break
        if time_met:
            dc_motor.stop() #stop spinning
            send_message("spin program complete") #confirm to CYD to perform next action
            print("spin program complete")

#run the program

while True: #whilst it is on...
    main_program()



