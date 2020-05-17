import RPi.GPIO as GPIO
import time
import atexit
import os
import pygame
from pygame.locals import * # for event MOUSE variables

START_TIME = int(time.time())

IN_CHANNELS = {
            17: ('left', 100),
            22: ('left', -100),
            23: ('right', 100),
            27: ('right', -100),
        }

PWM_OUT_CHANNELS = {
    #   Pin       Default Freq      Default Duty Cycle
        13:       (46.51,              6.98),
        12:       (46.51,              6.98),
        }

PWM_DICT = {12: 'right', 13: 'left'}
PWM_SPEEDS = {12: 0, 13: 0}
# PWM_DICT = {}

# Key: Motor Pin, Value: queue of commands (up to 3 long)
HIST_DICT = {12: ['', '', ''], 13: ['', '', '']}

# Pygame Globals
WHITE = 255, 255, 255
BLACK = 0,0,0
SCREEN = None
FONT = None
SMALL_FONT = None
BUTTONS = { 'Display Recordings':(160,90)}
BUTTON_RECTS = {}
HISTORY_Y_COORDINATES = [60, 100, 140, 180]
FILES={}
FILES_RECTS ={}
TRANSITION ={'Fix Audio':(160,90),'Go Back':(160,120),'Home Screen':(160,140)}
TRANSITION_RECTS ={}

PANIC = False
state =1

def gpio_callback(channel):
    print("edge detected on {}, command {}".format(channel, IN_CHANNELS[channel]))
    servoname, speed = IN_CHANNELS[channel]

    servo = None
    if servoname == 'left':
        servo = PWM_DICT[13]
    elif servoname == 'right':
        servo = PWM_DICT[12]

    if not PANIC:
        set_motor_speed(servo, speed)
    
    if IN_CHANNELS[channel]=='quit':
        my_exit()

def calc_pwm(speed):
    assert abs(speed) <= 100
    pulsewidth = 0.0015 + speed * 0.0002/100 
    period = 0.020 + pulsewidth
    freq = 1.0/period
    dut = pulsewidth/period * 100
    print(f"Pulsewidth:{pulsewidth:.5f}, Frequency: {freq:.5f}, Dutycycle: {dut:.5f}")
    return (freq, dut)

def get_elapsed_time():
    return int(time.time()) - START_TIME

def set_motor_speed(pwm, speed, save_speed=True):
    print(f"setting speed to {speed}")
    freq, dut = calc_pwm(speed)
    
    hist_text = ''
    side = ''
    if    speed > 0: hist_text = 'clockwise'
    else: hist_text = 'counterclockwise'
    
    if    pwm == PWM_DICT[13]: side = 'left'
    elif  pwm == PWM_DICT[12]: side = 'right'
    else: assert False, f"{pwm}"
    
    if speed == 0:
        push_pop_queue(side, 'stop')
        dut = 0
    else:
        push_pop_queue(side, hist_text)
    if save_speed:
        if side == 'left':
            PWM_SPEEDS[13] = speed
        elif side == 'right':
            PWM_SPEEDS[12] = speed

    pwm.ChangeFrequency(freq)
    pwm.ChangeDutyCycle(dut)

def setup_pygame():
    # os.putenv('SDL_VIDEODRIVER', 'fbcon') # Display on piTFT
    # os.putenv('SDL_FBDEV', '/dev/fb1')
    # os.putenv('SDL_MOUSEDRV', 'TSLIB') # Track mouse clicks on piTFT
    # os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

    pygame.init()
    # pygame.mouse.set_visble(False)
    global SCREEN 
    SCREEN = pygame.display.set_mode((320, 240))
    global FONT, SMALL_FONT
    FONT = pygame.font.Font(None, 30)
    SMALL_FONT = pygame.font.Font(None, 20)
    

# called at the beginning to set up all the GPIO pin pull up resistors
def setup_pins():
    GPIO.setmode(GPIO.BCM)
    for pin in IN_CHANNELS.keys():
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(pin,GPIO.FALLING,callback=gpio_callback,bouncetime=300)
    
    for pin in PWM_OUT_CHANNELS.keys():
        GPIO.setup(pin, GPIO.OUT)
        freq = PWM_OUT_CHANNELS[pin][0]
        dut = PWM_OUT_CHANNELS[pin][1]
        PWM_DICT[pin] = GPIO.PWM(pin, freq)
        PWM_DICT[pin].start(dut)

# pushes and pops the history queue
def push_pop_queue(side, push_me):
    pin = 0
    x = 0

    if side == 'left':
        pin = 13
    elif side == 'right':
        pin = 12
    else:
        assert False, f"gave {side}, only left and right are valid sides"
    queue = HIST_DICT[pin]
    queue.pop(len(queue) - 1)
    queue.insert(0, f"{get_elapsed_time()}: {push_me}")

# Draws history on the screen. Does not blank the screen
def draw_history(side):
   # pin = 0
   # x = 0
   # global foo
   # if side == 'left':
       # pin = 13
       # x = 60
    #elif side == 'right':
       # pin = 12
       # x = 260
    #else:
        #assert False, f"gave {side}, only left and right are valid sides"

    texts = [side]
    y=50
    for text in texts:
        text_surface = SMALL_FONT.render(text, True, WHITE)
        rect = text_surface.get_rect(center=(160,y))
        SCREEN.blit(text_surface, rect)


def refresh_screen():
    global state
    SCREEN.fill(BLACK)
    #print(f"{state}")
    # draw history
    #draw_history('Press to Record')

    # draw buttons
    if (state==1):
        for my_text, text_pos in BUTTONS.items():
        #if PANIC and my_text == "STOP":
           # my_text = "RESUME"
            text_surface = FONT.render(my_text, True, WHITE)
            rect = text_surface.get_rect(center=text_pos)
            BUTTON_RECTS[my_text] = rect
            #print(rect)
            SCREEN.blit(text_surface, rect)
        pygame.display.flip()
        
    if (state==2):
        #print("Instate 2")
        position = 1
        with  os.scandir('wavs/') as entries:
            for entry in entries:
                #print(entry.name)
                data = {entry.name:(120,90+10*position)}
                # FILES[entry.name] = (120, 90+10*position)
                position+=5
                FILES.update(data)
            #for key in FILES:
                #print(key)
            for my_text, text_pos in FILES.items():
                text_surface = FONT.render(my_text, True, WHITE)
                #import pdb
                #pdb.set_trace()
                rect1 = text_surface.get_rect(center=text_pos)
                FILES_RECTS[my_text] = rect1
                SCREEN.blit(text_surface, rect1)
            pygame.display.flip()

    if state ==3:
        #display plot --------- HOW????????
        for my_text, text_pos in TRANSITION.items():
                text_surface = FONT.render(my_text, True, WHITE)
                #import pdb
                #pdb.set_trace()
                rect1 = text_surface.get_rect(center=text_pos)
                TRANSITION_RECTS[my_text] = rect1
                SCREEN.blit(text_surface, rect1)
        pygame.display.flip()

    if state ==4:
        #display fixed audio
        text_surface= FONT.render('Home Screen',True,WHITE)
        rect = text_surface.get_rect(center = (120,90))
        SCREEN.blit(text_surface,rect)
        pygame.display.flip()


def detect_touch():
    global state
    if state==1 :
        for event in pygame.event.get():
            if(event.type is MOUSEBUTTONDOWN):
                pos = pygame.mouse.get_pos()
                # print("mousebottomdown")
            elif(event.type is MOUSEBUTTONUP):
                pos=pygame.mouse.get_pos()
                # print("mousebottomup")
                x,y = pos
                for btn in BUTTON_RECTS:
                    #print(f"{btn}")
                    rect = BUTTON_RECTS[btn]
                    temp = rect.collidepoint(x,y)
                    #print(f"{temp}")
                    if rect.collidepoint(x, y): 
                        if btn == "Display Recordings":
                            state =2
                            #print("recordings on the screen")
                            #print(f"{state}")
                        if btn == "QUIT":
                            print("QUITTING")
                            exit()
    elif state ==2:
        for event in pygame.event.get():
            if(event.type is MOUSEBUTTONDOWN):
                pos = pygame.mouse.get_pos()
                # print("mousebottomdown")
            elif(event.type is MOUSEBUTTONUP):
                pos=pygame.mouse.get_pos()
                # print("mousebottomup")
                x,y = pos

            
                for btn in FILES_RECTS:
                    #print(f"{btn}")
                    rect = FILES_RECTS[btn]
                    #temp = rect.collidepoint(x,y)
                    #print(f"{temp}")
                    if rect.collidepoint(x, y): 
                        state =3
                        print(f"Displaying {btn} file ")
                        #print(f"{state}")
    elif state ==3:
         for event in pygame.event.get():
            if(event.type is MOUSEBUTTONDOWN):
                pos = pygame.mouse.get_pos()
                # print("mousebottomdown")
            elif(event.type is MOUSEBUTTONUP):
                pos=pygame.mouse.get_pos()
                # print("mousebottomup")
                x,y = pos
                for btn in TRANSITION_RECTS:
                    #print(f"{btn}")
                    rect = TRANSITION_RECTS[btn]
                    #temp = rect.collidepoint(x,y)
                    #print(f"{temp}")
                    if rect.collidepoint(x, y): 
                        if btn =="Go Back":
                            state =2
                        if btn == "Home Screen":
                            state =1
                            #print("recordings on the screen")
                            #print(f"{state}")
                        if btn == "Fix Audio":
                            #print("Fix Audio")
                            state =4
                            #call audio fixing function here


    elif state ==4:
         for event in pygame.event.get():
            if(event.type is MOUSEBUTTONDOWN):
                pos = pygame.mouse.get_pos()
                # print("mousebottomdown")
            elif(event.type is MOUSEBUTTONUP):
                pos=pygame.mouse.get_pos()
                # print("mousebottomup")
                x,y = pos
                for btn in TRANSITION_RECTS:
                    #print(f"{btn}")
                    rect = TRANSITION_RECTS[btn]
                    #temp = rect.collidepoint(x,y)
                    #print(f"{temp}")
                    if rect.collidepoint(x, y): 
                        if btn == "Home Screen":
                            state =1
                            #print("recordings on the screen")
                            #print(f"{state}")
                        


def my_exit():
    #TODO: stop PWM?
    GPIO.cleanup()
    print("exit handler!")
    exit()

def main():
   # setup_pins()
    atexit.register(my_exit)
    setup_pygame()
    #global state  #Home screen "Display recordings"
    #state =1
   # for _ , pwm in PWM_DICT.items():
      #  set_motor_speed(pwm, 0)
    while True:
        refresh_screen()

        detect_touch()
        pass

if __name__ == '__main__':
    main()
