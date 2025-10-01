import time
import ujson
import machine
import network
import espnow
import random
import lvgl as lv
import gc

### boot ###

espnow_est = False #espnow establishment status

timer_duration = 60 #timer duration in seconds

random_int_min = 1 #minimum integer generated for the abacus
random_int_max = 99999 #maximum integer generated for the abacus

timer_complete = False

def b_str_conv(byte_data): #b string converter
    string_data = byte_data.decode("utf-8")
    return string_data

def save_settings():
    global timer_duration, random_int_min, random_int_max
    with open('settings.txt', 'w') as f:
        ujson.dump({'timer_duration': timer_duration, 'int_min': random_int_min, 'int_max': random_int_max}, f)
    gc.collect()


def ping_pong_program():
    global espnow_est, timer_duration, random_int_min, random_int_max, e, main_mac
    # Initialize ESPNOW
    
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    sta.config(channel=1)  # Set channel explicitly if packets are not delivered, uncomment if nessesary
    sta.disconnect()

    e = espnow.ESPNow()
    try:
        e.active(True)
    except OSError as err:
        print("Failed to initialize ESPNOW:", err)
        raise


    # CYD MAC address
    main_mac = b'\x30\xae\xa4\xf6\x7d\x4c' #ESP32's MAC address
    #main_mac = b'\xff\xff\xff\xff\xff\xff' #broadcast

    # Add peer ESP
    try:
        e.add_peer(main_mac) #receiver ESP
    except OSError as err:
        print("Failed to add peer:", err)
        raise

    def ping_pong_init():
        received_ping = False
        
        def send_ping(m_msg): # Send the message and print
            try:
                if e.send(main_mac, m_msg, True):
                    print(f"Pinged CYD with: {m_msg}")
                else:
                    print("Failed to ping (send returned False)")
            except OSError as err:
                print(f"Failed to ping (OSError: {err})")
        
        while not received_ping: #ping pong procedure
            try:
                # Receive message (host MAC, message, timeout of 10 seconds)
                host, main_msg = e.recv(10000) #listen
                
                try:
                    print(f"recieved from {b_str_conv(host)}: {b_str_conv(main_msg)}") #print CYD pong message
                    
                    n_main_msg = b_str_conv(main_msg)
                    
                    if n_main_msg == "main ping": #if received pong
                        send_ping("cyd pong") #start nominal boot
                        espnow_est = True
                        
                        received_ping = True
                        break
                except:
                    pass
            
                time.sleep(1)  # Ping every 1 second
                
            except OSError as err: #OS error handling
                print("Error:", err)
                time.sleep(5)
    
    ping_pong_init()
    print("Boot complete!")



def boot_program():
    global espnow_est, timer_duration, random_int_min, random_int_max, stylebg, fs_drive_letter, fs_font_driver, main_screen, style_btn, style_btn_pressed
    
    main_screen = lv.scr_act()

    # fonts and splash initialise
    import fs_driver
    fs_drive_letter = 'D'
    fs_font_driver = lv.fs_drv_t()
    fs_driver.fs_register(fs_font_driver, fs_drive_letter)

    # bg styles init
    stylebg = lv.style_t()
    stylebg.init()
    stylebg.set_bg_opa(lv.OPA.COVER)
    stylebg.set_bg_color(lv.color_hex(0xE0F2F7))
    stylebg.set_border_color(lv.color_hex(0xE0F2F7))
    stylebg.set_border_width(10)
    stylebg.set_radius(0)

    # background itself
    newbg = lv.obj(main_screen)
    newbg.add_style(stylebg, 0)
    newbg.set_size(320, 240)
    newbg.align(lv.ALIGN.CENTER, 0, 0)

    # version text below logo
    versiontext = lv.label(main_screen)
    versiontext.set_recolor(True)
    versiontext.set_text(f"#5c5c5c VERSION 0.5.0 #")
    versiontext.align(lv.ALIGN.CENTER, 0, 15)
    
    #main logo
    andika_30 = lv.font_load(f"{fs_drive_letter}:fonts/andika_30.bin")
    gc.collect()

    andika_30_style = lv.style_t()
    andika_30_style.init()
    andika_30_style.set_text_font(andika_30)
    andika_30_style.set_text_color(lv.color_hex(0x5c5c5c))
    gc.collect()
    
    # logo text font init
    logo_font = lv.style_t()
    logo_font.init()
    logo_font.set_text_font(andika_30)
    logo_font.set_text_color(lv.color_hex(0x5c5c5c))
    gc.collect()

    # main logo
    main_logo = lv.label(main_screen)
    main_logo.set_recolor(True)
    main_logo.set_text(f"#5c5c5c Digital Abacus Program#")
    main_logo.align(lv.ALIGN.CENTER, -50, -12)
    main_logo.add_style(andika_30_style, 0)

    # boot status
    stat_espnow = lv.label(main_screen)
    stat_espnow.set_recolor(True)
    stat_espnow.align(lv.ALIGN.BOTTOM_LEFT, 0, 0)
    
    # the button style
    style_btn = lv.style_t()
    style_btn.init()
    style_btn.set_radius(0)
    style_btn.set_bg_opa(lv.OPA.COVER)
    style_btn.set_bg_color(lv.color_hex(0x636263))
    style_btn.set_border_color(lv.color_hex(0x636263))
    style_btn.set_border_opa(lv.OPA._70)
    style_btn.set_border_width(2)
    style_btn.set_text_color(lv.color_white())
    gc.collect()

    style_btn_pressed = lv.style_t()
    style_btn_pressed.init()
    style_btn_pressed.set_bg_color(lv.color_hex(0x53a03c))
    style_btn_pressed.set_bg_grad_color(lv.palette_darken(lv.PALETTE.RED, 3))
    gc.collect()
    
    #ESPNOW init
    stat_espnow.set_text("#5c5c5c ESPNOW INITIALIZATION... #")
    ping_pong_program() #ESPNOW boot and pingpong

    while not espnow_est: #keep active
        lv.task_handler()
        time.sleep_ms(10)

    # update status text
    if espnow_est:
        stat_espnow.set_text("#5c5c5c PONG RECEIVED... #")
        lv.task_handler()
    
    # load the settings if exist
    try:
        with open('settings.txt', 'r') as f:
            data = ujson.load(f)
            timer_duration = data.get('timer_duration', 60)
            
            random_int_min = data.get('int_min', 1)
            random_int_max = data.get('int_max', 99999)
    except:
        save_settings()

    # cleanup boot
    versiontext.delete()
    main_logo.delete()
    stat_espnow.delete()
    andika_30 = None
    andika_30_style = None
    gc.collect()

####### main content ########

def main_items_initialization():
    global andika_20, andika_20_style, segment_40, segment_40_style, tab_ident, tab_settings, ta_style
    # common fonts init
    # load fonts from file
    andika_20 = lv.font_load(f"{fs_drive_letter}:fonts/andika_20.bin")
    gc.collect()

    # andika 20 Style init
    andika_20_style = lv.style_t()
    andika_20_style.init()
    andika_20_style.set_text_font(andika_20)
    andika_20_style.set_text_color(lv.color_hex(0x5c5c5c))
    gc.collect()

    ###
    segment_40 = lv.font_load(f"{fs_drive_letter}:fonts/segment_40.bin")
    gc.collect()

    segment_40_style = lv.style_t()
    segment_40_style.init()
    segment_40_style.set_text_font(segment_40)
    segment_40_style.set_text_color(lv.color_hex(0x5c5c5c))
    gc.collect()

    # input area styling
    ta_style = lv.style_t()
    ta_style.init()
    ta_style.set_bg_color(lv.color_hex(0xE0F2F7))
    ta_style.set_text_color(lv.color_hex(0x000000))
    ta_style.set_border_color(lv.color_hex(0xE0F2F7))
    ta_style.set_border_width(2)
    ta_style.set_radius(5)
    ta_style.set_pad_all(5)
    gc.collect()

    # tabs init
    tabview = lv.tabview(main_screen, lv.DIR.TOP, 50)
    tabview.set_size(320, 240)
    tabview.center()
    tabview.set_style_bg_opa(0, 0)
    gc.collect()

    # tab style init
    tab_hdr = tabview.get_tab_btns()
    tab_hdr.add_style(style_btn, 0)
    tab_hdr.add_style(style_btn_pressed, lv.STATE.PRESSED)
    tab_hdr.add_style(style_btn_pressed, lv.STATE.CHECKED)
    gc.collect()

    # two tabs
    tab_ident = tabview.add_tab("HOME")
    gc.collect()
    tab_settings = tabview.add_tab("SETTINGS")
    gc.collect()

    # disable scrolling text on tab label (on by default lvgl)
    for i in range(tab_hdr.get_child_cnt()):
        btn = tab_hdr.get_child(i)
        lbl = btn.get_child(0)
        lbl.scroll_to_view_recursive(lv.ANIM.OFF)
    gc.collect()

    tab_settings.set_scroll_dir(lv.DIR.VER)
    gc.collect()


def main_loop():
    # loop
    loop_counter = 0
    while True:
        try:
            lv.task_handler()
            loop_counter += 1
            if loop_counter % 10 == 0:
                gc.collect()
            time.sleep_ms(10)
        except MemoryError:
            machine.reset()




###ESPNOW listen and sending functions###
def listen_msg():
    host, main_msg = e.recv(10000) #listen
    try:
        print(f"recieved from {b_str_conv(host)}: {b_str_conv(main_msg)}") #print ESP message
        receiving_main_msg = b_str_conv(main_msg) #convert the b string
                    
        if receiving_main_msg == "spin program complete": #if received confirmation of completion
            return True
    except:
        pass

def send_message(msg): # Send the message and print
    try:
        if e.send(main_mac, msg, True):
            print(f"Pinged ESP with: {msg}")
        else:
            print("Failed to ping (send returned False)")
    except OSError as err:
        print(f"Failed to ping (OSError: {err})")



#timer object
timer_label = None

def timer_callback(timer):
    global timer_duration
    global timer_complete
    
    if timer_duration > 0:
        timer_duration -= 1
        minutes = timer_duration // 60
        seconds = timer_duration % 60
        timer_label.set_text(f"{minutes:02d}:{seconds:02d}")
    else: #when timer is complete
        timer_label.set_text("--:--") #when timer done
        timer_complete = True
        lv.timer_del(timer) # Delete the timer when done
        
        # stop timer button
        menu_btn = lv.btn(play_screen)
        menu_btn.set_size(120, 60)
        menu_btn.align(lv.ALIGN.CENTER, 0, 20)
        menu_label = lv.label(menu_btn)
        menu_label.set_text("MENU")
        menu_label.center()
        menu_btn.add_style(style_btn, 0)
        gc.collect()

    def menu_btn_cb(e):
        lv.scr_load(main_screen)
        play_screen.delete()
        gc.collect()

    menu_btn.add_event_cb(menu_btn_cb, lv.EVENT.CLICKED, None) #make an event when clicked

def main_timer():
    global timer_label, timer_object

    # Create the LVGL timer
    timer_object = lv.timer_create(timer_callback, 1000, None) # Call every 1000ms (1 second)


def game_start():
    global play_screen, spin_btn, timer_label
    
    # Play overlay onto the screen
    play_screen = lv.obj()
    play_screen.set_size(320, 240)
    play_screen.add_style(stylebg, 0)
    play_screen.set_scroll_dir(lv.DIR.VER)
    gc.collect()
    
    #Create timer label
    timer_label = lv.label(play_screen)
    timer_label.set_text("--:--") # Initial display
    timer_label.align(lv.ALIGN.CENTER, -100, 0)
    timer_label.add_style(segment_40_style, 0)
    
    
    
    #create spin button
    spin_btn = lv.btn(play_screen)
    spin_btn.set_size(100, 50)
    spin_btn.align(lv.ALIGN.CENTER, 100, 0)
    spin_label = lv.label(spin_btn)
    spin_label.set_text("SPIN")
    spin_btn.center()
    spin_btn.add_style(style_btn, 0)
    gc.collect()
    
    def spin_btn_cb(e):
        global spin_stopped
        spin_stopped = False
        send_message("spin arrow") #command esp32 to spin motor
        print("command 'spin' has been sent")
        
        while not spin_stopped:
            complete_status = listen_msg() #constantly listen to messages for completion
            lv.timer_handler()
            time.sleep_ms(5)
            if complete_status:
                game_play()
                spin_stopped = True
    
    spin_btn.add_event_cb(spin_btn_cb, lv.EVENT.CLICKED, None) #make spin event when clicked
    
def game_play():
    spin_btn.hide() #hide the spin button
    
    random_number = random.randint(random_int_min, random_int_max)
    label_random = lv.label(play_screen) #random number
    label_random.set_recolor(True)
    label_random.set_text(f"#5c5c5c {random_number} #") #child will make the random number from the abacus
    
    label_random.add_style(andika_20_style, 0) #7 segment style
    label_random.align(lv.ALIGN.CENTER, 0, 80)
    gc.collect()
    
    # stop timer button
    finish_btn = lv.btn(play_screen)
    finish_btn.set_size(120, 60)
    finish_btn.align(lv.ALIGN.CENTER, 0, 20)
    finish_label = lv.label(finish_btn)
    finish_label.set_text("I FINISHED!")
    finish_label.center()
    finish_btn.add_style(style_btn, 0)
    gc.collect()

    def finish_btn_cb(e):
        global timer_complete
        lv.timer_pause(timer_object)
        timer_complete = True
        finish_btn.delete() #delete the button
    
    finish_btn.add_event_cb(finish_btn_cb, lv.EVENT.CLICKED, None) #make an event when clicked
    
    main_timer() #start the timer


def main_page():
    # main page
    label_home = lv.label(tab_ident)
    label_home.set_recolor(True)
    label_home.set_text(f"#5c5c5c PLAY #")
    label_home.add_style(andika_20_style, 0)
    label_home.align(lv.ALIGN.CENTER, 0, -80)
    gc.collect()

    
    # play button
    play_btn = lv.btn(tab_ident)
    play_btn.set_size(120, 60)
    play_btn.align(lv.ALIGN.CENTER, 0, 0)
    play_label = lv.label(play_btn)
    play_label.set_text("PLAY")
    play_label.center()
    play_btn.add_style(style_btn, 0)
    gc.collect()

    def play_btn_cb(e):
        game_start()
    
    play_btn.add_event_cb(play_btn_cb, lv.EVENT.CLICKED, None) #make an event when clicked


def settings_page():

    # settings page
    label_settings = lv.label(tab_settings)
    label_settings.set_recolor(True)
    label_settings.set_text(f"#5c5c5c SETTINGS#")
    label_settings.add_style(andika_20_style, 0)
    label_settings.align(lv.ALIGN.CENTER, 0, -80)
    gc.collect()

    ##########
    

    # modify timer duration button
    mod_timer_btn = lv.btn(tab_settings)
    mod_timer_btn.set_size(100, 50)
    mod_timer_btn.align(lv.ALIGN.CENTER, 0, -60)
    mod_timer_label = lv.label(mod_timer_btn)
    mod_timer_label.set_text("TIMER DURATION")
    mod_timer_label.center()
    mod_timer_btn.add_style(style_btn, 0)
    gc.collect()
    
    def mod_timer_btn_cb(e):
        global timer_duration
        # text area show
        
        # input init
        input_screen = lv.obj()
        input_screen.set_size(320, 240)
        input_screen.add_style(stylebg, 0)
        input_screen.set_scroll_dir(lv.DIR.VER)
        gc.collect()
        
        ta = lv.textarea(input_screen)
        ta.set_size(300, 60)
        ta.align(lv.ALIGN.TOP_MID, 0, 40)
        ta.set_placeholder_text("TIME IN SECONDS")
        ta.add_style(ta_style, 0)
        gc.collect()

        # keyboard from lvgl (no styles)
        kb = lv.keyboard(input_screen)
        kb.set_size(320, 120)
        kb.align(lv.ALIGN.BOTTOM_MID, 0, 0)
        kb.set_textarea(ta)
        gc.collect()
        
        # submit button
        send_btn = lv.btn(input_screen)
        send_btn.set_size(60, 30)
        send_btn.align(lv.ALIGN.BOTTOM_RIGHT, -10, -130)
        send_label = lv.label(send_btn)
        send_label.set_text("SUBMIT")
        send_label.center()
        send_btn.add_style(style_btn, 0)
        gc.collect()
        
        def send_btn_cb(e):
            global timer_duration
            curr_time_dur = int(ta.get_text())
            if not curr_time_dur:
                return
            
            timer_duration = curr_time_dur
            save_settings()
            ta.set_text("")
            #close
            lv.scr_load(main_screen)
            input_screen.delete()
            gc.collect()
    
        send_btn.add_event_cb(send_btn_cb, lv.EVENT.CLICKED, None) #make an event when clicked
    mod_timer_btn.add_event_cb(mod_timer_btn_cb, lv.EVENT.CLICKED, None) #make an event when clicked
    
    # modify min int button
    mod_min_int_btn = lv.btn(tab_settings)
    mod_min_int_btn.set_size(100, 50)
    mod_min_int_btn.align(lv.ALIGN.CENTER, 0, -120)
    mod_min_int_label = lv.label(mod_min_int_btn)
    mod_min_int_label.set_text("MIN INTEGER")
    mod_min_int_label.center()
    mod_min_int_btn.add_style(style_btn, 0)
    gc.collect()
    
    def mod_min_int_btn_cb(e):
        global random_int_min
        
        # input init
        input_screen2 = lv.obj()
        input_screen2.set_size(320, 240)
        input_screen2.add_style(stylebg, 0)
        input_screen2.set_scroll_dir(lv.DIR.VER)
        gc.collect()
        
        # text area show 
        ta2 = lv.textarea(input_screen2)
        ta2.set_size(300, 60)
        ta2.align(lv.ALIGN.TOP_MID, 0, 40)
        ta2.set_placeholder_text("MINIMUM INTEGER...")
        ta2.add_style(ta_style, 0)
        gc.collect()

        # keyboard from lvgl (no styles)
        kb2 = lv.keyboard(input_screen2)
        kb2.set_size(320, 120)
        kb2.align(lv.ALIGN.BOTTOM_MID, 0, 0)
        kb2.set_textarea(ta2)
        gc.collect()
        
        # submit button
        send_btn2 = lv.btn(input_screen2)
        send_btn2.set_size(60, 30)
        send_btn2.align(lv.ALIGN.BOTTOM_RIGHT, -10, -130)
        send_label2 = lv.label(send_btn2)
        send_label2.set_text("SUBMIT")
        send_label2.center()
        send_btn2.add_style(style_btn, 0)
        gc.collect()
        
        def send2_btn_cb(e):
            global random_int_min
            curr_min_int = int(ta2.get_text())
            if not curr_min_int:
                return
            
            random_int_min = curr_min_int
            save_settings()
            ta2.set_text("")
            #close
            lv.scr_load(main_screen)
            input_screen2.delete()
            gc.collect()
    
        send_btn2.add_event_cb(send2_btn_cb, lv.EVENT.CLICKED, None) #make an event when clicked
    mod_min_int_btn.add_event_cb(mod_min_int_btn_cb, lv.EVENT.CLICKED, None) #make an event when clicked
    
    # modify max int button
    mod_max_int_btn = lv.btn(tab_settings)
    mod_max_int_btn.set_size(100, 50)
    mod_max_int_btn.align(lv.ALIGN.CENTER, 0, -120)
    mod_max_int_label = lv.label(mod_max_int_btn)
    mod_max_int_label.set_text("MAX INTEGER")
    mod_max_int_label.center()
    mod_max_int_btn.add_style(style_btn, 0)
    gc.collect()
    
    def mod_max_int_btn_cb(e):
        global random_int_max
        
        # input init
        input_screen3 = lv.obj()
        input_screen3.set_size(320, 240)
        input_screen3.add_style(stylebg, 0)
        input_screen3.set_scroll_dir(lv.DIR.VER)
        gc.collect()
        
        # text area show 
        ta3 = lv.textarea(input_screen3)
        ta3.set_size(300, 60)
        ta3.align(lv.ALIGN.TOP_MID, 0, 40)
        ta3.set_placeholder_text("MAXIMUM INTEGER...")
        ta3.add_style(ta_style, 0)
        gc.collect()

        # keyboard from lvgl (no styles)
        kb3 = lv.keyboard(input_screen3)
        kb3.set_size(320, 120)
        kb3.align(lv.ALIGN.BOTTOM_MID, 0, 0)
        kb3.set_textarea(ta3)
        gc.collect()
        
        # submit button
        send_btn3 = lv.btn(input_screen3)
        send_btn3.set_size(60, 30)
        send_btn3.align(lv.ALIGN.BOTTOM_RIGHT, -10, -130)
        send_label3 = lv.label(send_btn3)
        send_label3.set_text("SUBMIT")
        send_label3.center()
        send_btn3.add_style(style_btn, 0)
        gc.collect()
        
        def send3_btn_cb(e):
            global random_int_max
            curr_max_int = int(ta3.get_text())
            if not curr_max_int:
                return
            
            random_int_max = curr_max_int
            save_settings()
            ta3.set_text("")
            #close
            lv.scr_load(main_screen)
            input_screen3.delete()
            gc.collect()
    
        send_btn3.add_event_cb(send3_btn_cb, lv.EVENT.CLICKED, None) #make an event when clicked
    mod_max_int_btn.add_event_cb(mod_max_int_btn_cb, lv.EVENT.CLICKED, None) #make an event when clicked
    

#### Main execution code ####

boot_program() #start up and connect to ESPNOW

# After boot...

main_items_initialization()
main_page() #main page init
settings_page() #settings page init
main_loop() #main loop finally....