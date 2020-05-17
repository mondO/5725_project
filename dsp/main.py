import time
import atexit
import os
import pygame
import pdb
import copy
from pygame.locals import * # for event MOUSE variables
from enum import Enum, auto

class St(Enum):
    MAIN       = auto()
    BROWSE     = auto()
    RECORD     = auto()
    DSP        = auto()
MY_STATE = St.MAIN


MAIN_BUTTONS = {
    (160, 90) : 'BROWSE',
    (160, 130) : 'QUIT',
}




BROWSE_FILE_BUTTONS = {
    (160, 80) : 'file0',
    (160, 100) : 'file1',
    (160, 120) : 'file2',
    (160, 140) : 'file3',
}
BROWSE_UI_BUTTONS = {
    (80, 200) : 'BACK',
    (160, 200) : 'PREV',
    (240, 200) : 'NEXT',
}
file_list = ['a', 'b', 'c', 'd', 'e']
file_page_num = 0
file_page_size = 4



DSP_BUTTONS = {
    (190, 90) : 'FOO',
    (160, 90) : 'BAR',
}

# k,v = coordinate tuple, reference to pygame rectangle for button
# contents of this gets cleared every time we transition states
BUTTON_RECTS = {}


#Pygame globals
WHITE = 255, 255, 255
BLACK = 0,0,0
SCREEN = None
FONT = None
SMALL_FONT = None

def detect_touch(current_state):
    global BUTTON_RECTS, MY_STATE, file_page_num
    label_dict = None
    
    if current_state == St.MAIN:
        label_dict = MAIN_BUTTONS
    elif current_state == St.BROWSE:
        label_dict = copy.copy(BROWSE_UI_BUTTONS)
        label_dict.update(BROWSE_FILE_BUTTONS)
    # elif current_state = St.RECORD:
        # pass
    elif current_state == St.DSP:
        label_dict = DSP_BUTTONS
    else:
        assert False, "Invalid state"

    touched = None
    for event in pygame.event.get():
        if(event.type is MOUSEBUTTONDOWN):
            pos = pygame.mouse.get_pos()
        elif(event.type is MOUSEBUTTONUP):
            pos=pygame.mouse.get_pos()
            x,y = pos
        
            for coor, rect in BUTTON_RECTS.items():
                if rect.collidepoint((x, y)):
                    # get the name of the button that was touched
                    touched = label_dict[coor]
                    break
    if touched:
        print(touched)
        if current_state == St.MAIN:
            if touched == 'BROWSE':
                MY_STATE = St.BROWSE
            elif touched == 'QUIT':
                system.exit(0)
        elif current_state == St.BROWSE:
            if touched == 'BACK':
                MY_STATE = St.MAIN
            elif touched == 'PREV':
                if file_page_num > 0:
                    file_page_num -= 1
            elif touched == 'NEXT':
                if len(file_list) - (file_page_num + 1) * 4 > 0:
                    file_page_num += 1

    # TODO: do stuff after detecting a touch (depending on state)


# Draw all the UI elements
def draw_screen(current_state):
 
    global BUTTON_RECTS
    BUTTON_RECTS = {}
    label_dict = None
    
    if current_state == St.MAIN:
        label_dict = MAIN_BUTTONS
    elif current_state == St.BROWSE:
        label_dict = BROWSE_UI_BUTTONS
    # elif current_state = St.RECORD:
        # pass
    elif current_state == St.DSP:
        label_dict = DSP_BUTTONS
    else:
        assert False, "Invalid state"

    SCREEN.fill(BLACK)
    for coor, label in label_dict.items():
        text_surface = FONT.render(label, True, WHITE)
        rect = text_surface.get_rect(center=coor)
        BUTTON_RECTS[coor] = rect
        SCREEN.blit(text_surface, rect)

    #TODO: do extra stuff for browse and dsp states
    if current_state == St.BROWSE:
        shown_files = file_list[ 
            file_page_num * file_page_size : 
            min( (file_page_num + 1) * file_page_size, len(file_list))
        ]
        file_i = 0
        for coor, label in BROWSE_FILE_BUTTONS.items():
            if file_i < len(shown_files):
                text_surface = FONT.render(shown_files[file_i], True, WHITE)
                rect = text_surface.get_rect(center=coor)
                BUTTON_RECTS[coor] = rect
                SCREEN.blit(text_surface, rect)
                file_i += 1
        
    
    pygame.display.flip()


def setup_pygame(pitft = False):
    if pitft:
        os.putenv('SDL_VIDEODRIVER', 'fbcon') # Display on piTFT
        os.putenv('SDL_FBDEV', '/dev/fb1')
        os.putenv('SDL_MOUSEDRV', 'TSLIB') # Track mouse clicks on piTFT
        os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

    pygame.init()
    if pitft: pygame.mouse.set_visble(False)
    
    global SCREEN 
    SCREEN = pygame.display.set_mode((320, 240))
    global FONT, SMALL_FONT
    FONT = pygame.font.Font(None, 30)
    SMALL_FONT = pygame.font.Font(None, 16)

def get_wavs():
    wav_list = []
    for file in os.listdir("../wavs"):
        if file.endswith(".wav"):
            wav_list.append(str(file))
    return wav_list


def main():
    global MY_STATE, file_list
    setup_pygame()

    MY_STATE = St.MAIN
    file_list = get_wavs()
    
    while True:
        draw_screen(MY_STATE)
        detect_touch(MY_STATE)
        pass

if __name__ == '__main__':
    main()
        
