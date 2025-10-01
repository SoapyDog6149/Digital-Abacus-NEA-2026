import network
import espnow
import time


def b_str_conv(byte_data):
    string_data = byte_data.decode("utf-8")
    return string_data

##ESPNOW BOOT##

def boot_program():
    global e, CYD_mac
    # Initialize ESP-NOW
    
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    sta.config(channel=1)  # Set channel explicitly if packets are not delivered, uncomment if nessesary
    sta.disconnect()

    e = espnow.ESPNow()
    try:
        e.active(True)
    except OSError as err:
        print("Failed to initialize ESP-NOW:", err)
        raise


    # CYD MAC address
    CYD_mac = b'\x30\xae\xa4\xf6\x7d\x4c' #CYD's MAC address
    #CYD_mac = b'\xff\xff\xff\xff\xff\xff' #broadcast

    # Add peer ESP
    try:
        e.add_peer(CYD_mac) #receiver CYD
    except OSError as err:
        print("Failed to add peer:", err)
        raise

    def ping_pong_init():
        received_pong = False
        
        def send_ping(m_msg): # Send the message and print
            try:
                if e.send(CYD_mac, m_msg, True):
                    print(f"Pinged CYD with: {m_msg}")
                else:
                    print("Failed to ping (send returned False)")
            except OSError as err:
                print(f"Failed to ping (OSError: {err})")
        
        while not received_pong: #ping pong procedure
            try:
                main_message = "main ping"
                send_ping(main_message) #send ping message
                 
                # Receive message (host MAC, message, timeout of 10 seconds)
                host, cyd_msg = e.recv(10000) #listen
                
                try:
                    print(f"recieved from {b_str_conv(host)}: {b_str_conv(cyd_msg)}") #print CYD pong message
                    
                    n_cyd_msg = b_str_conv(cyd_msg)
                    
                    if n_cyd_msg == "cyd pong": #if received pong
                        received_pong = True
                        break
                except:
                    pass
            
                time.sleep(1)  # Ping every 1 second
                
            except OSError as err: #OS error handling
                print("Error:", err)
                time.sleep(5)
    
    ping_pong_init()
    print("Boot complete!")


from dcmotor import DCMotor
from machine import Pin, PWM

def motor_init():
    global dc_motor
    frequency = 15000 #init the PWM frequency
    
    #init GPIO and motor object
    pin1 = Pin(12, Pin.OUT) #GPIO 12
    pin2 = Pin(14, Pin.OUT) #GPIO 14
    enable = PWM(Pin(13), frequency) #GPIO 13

    dc_motor = DCMotor(pin1, pin2, enable)
    #dc_motor = DCMotor(pin1, pin2, enable, 350, 1023) #use if need to use min/max duty values

def listen_msg():
    host, cyd_msg = e.recv(10000) #listen
    try:
        print(f"recieved from {b_str_conv(host)}: {b_str_conv(cyd_msg)}") #print CYD message
        receiving_cyd_msg = b_str_conv(cyd_msg) #convert the b string
                    
        if receiving_cyd_msg == "spin arrow": #if received pong
            return True
    except:
        pass

def send_message(msg): # Send the message and print
    try:
        if e.send(CYD_mac, msg, True):
            print(f"Pinged CYD with: {msg}")
        else:
            print("Failed to ping (send returned False)")
    except OSError as err:
        print(f"Failed to ping (OSError: {err})")


import random
def main_program():
    spin_status = listen_msg()
    if spin_status == True:
        spin_duration = random.random(2,5) #random float from 2 to 5 in seconds
        spin_power = random.randint(40,90) #spin power one off rand int 40% - 90%
        
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

boot_program()
motor_init()

while True: #whilst it is on...
    main_program()









        
