import time
from datetime import datetime
import atexit
import os
import pygame
import pdb
import copy
from pygame.locals import * # for event MOUSE variables
from enum import Enum, auto

import numpy as np
import scipy.io.wavfile
import scipy.signal
import matplotlib.pyplot as plt
import wavio
from playsound import playsound

class St(Enum):
    MAIN       = auto()
    BROWSE     = auto()
    RECORD     = auto()
    DSP        = auto()
MY_STATE = St.MAIN


MAIN_BUTTONS = {
    (160, 50) : 'RECORD',
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
    (80, 200) : 'BACK',
    (160, 200) : 'PLAY',
    (240, 200) : 'UNCLIP',
}
image = None
wav_filename = None


# k,v = coordinate tuple, reference to pygame rectangle for button
# contents of this gets cleared every time we transition states
BUTTON_RECTS = {}


#Pygame globals
WHITE = 255, 255, 255
BLACK = 0,0,0
SCREEN = None
FONT = None
SMALL_FONT = None


def get_image(path):
        global _image_library
        image = _image_library.get(path)
        if image == None:
                canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
                image = pygame.image.load(canonicalized_path)
                _image_library[path] = image
        return image



def enter_dsp(filename):
    my_wavio = wavio.read(f'../wavs/{filename}')

    samples = np.array(my_wavio.data)
    samples = samples + (-1 * np.min(samples))
    num_samples = len(samples)

    clipped = np.copy(samples)
    clipped = clipped/np.max(clipped)
    clipped[clipped < 5e-19] = 0
    plt.clf()
    plt.axis('off')
    plt.plot(clipped)
    plt.savefig('foo.png', bbox_inches='tight', transparent=True)
    global image
    image = pygame.image.load('foo.png')
    image = pygame.transform.scale(image, (280, int(480/5)))
    # to_wav = scipy.signal.resample(clipped, int(num_samples * (441000/my_wavio.rate)))
    wavio.write("foo.wav", clipped, my_wavio.rate, sampwidth=3)

def unclip (filename):
    my_wavio = wavio.read(f'../wavs/{filename}')

    samples = np.array(my_wavio.data)
    samples = samples + (-1 * np.min(samples))
    num_samples = len(samples)

    clipped = np.copy(samples)
    clipped = clipped/np.max(clipped)
    clipped[clipped < 5e-19] = 0

    unclipped = np.zeros(clipped.shape)
    start = False
    i = 0
    while i < len(clipped):
        if i < len(clipped) and clipped[i] > 0 or not start:
            unclipped[i] = clipped[i]
            i += 1
            if(i < len(clipped) and clipped[i] > 0):
                start = True
            continue
        else:
            mirror_begin = i
            mirror_i = 0
            mirror = -clipped[mirror_begin - mirror_i]
            unclipped[i] = mirror
            mirror_i +=1
            mirror = -clipped[mirror_begin - mirror_i]
            i+=1
            while i < len(clipped) and mirror < 0 and clipped[i] <= 0:
                unclipped[i] = mirror
                mirror_i +=1
                mirror = -clipped[mirror_begin - mirror_i]
                i+=1

    plt.clf()
    plt.axis('off')
    plt.plot(unclipped)
    plt.savefig('foo.png', bbox_inches='tight', transparent=True)
    
    global image
    image = pygame.image.load('foo.png')
    image = pygame.transform.scale(image, (280, int(480/5)))

    # to_wav = scipy.signal.resample(unclipped, int(num_samples * (441000/my_wavio.rate)))
    wavio.write("foo.wav", unclipped, my_wavio.rate, sampwidth=3)

def detect_touch(current_state):
    global BUTTON_RECTS, MY_STATE, file_page_num, MAIN_BUTTONS, file_list
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
            elif touched == 'RECORD':
                MAIN_BUTTONS[(160, 50)] = 'RECORDING...'
                draw_screen(MY_STATE)
                
                now = datetime.now()
                date_time = now.strftime("%Y-%m-%d_%H-%M-%S")
                os.system(f'sudo ../build/record ../wavs/{date_time}_rec.wav')
                file_list = get_wavs()

                
                MAIN_BUTTONS[(160, 50)] = 'RECORD'
                draw_screen(MY_STATE)

            elif touched == 'QUIT':
                exit(0)
        elif current_state == St.BROWSE:
            if touched == 'BACK':
                MY_STATE = St.MAIN
            elif touched == 'PREV':
                if file_page_num > 0:
                    file_page_num -= 1
            elif touched == 'NEXT':
                if len(file_list) - (file_page_num + 1) * 4 > 0:
                    file_page_num += 1
            else:
                # here, touched is a filename
                enter_dsp(touched)
                global wav_filename
                wav_filename = touched
                MY_STATE = St.DSP
        elif current_state == St.DSP:
            if touched == 'BACK':
                MY_STATE = St.BROWSE
            elif touched == 'UNCLIP':
                unclip(wav_filename)
            elif touched == 'PLAY':
                os.system('aplay ./foo.wav')
                # pygame.mixer.init()
                # pygame.mixer.music.load("./foo.wav")
                # pygame.mixer.music.play()

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
                BROWSE_FILE_BUTTONS[coor] = shown_files[file_i]
                BUTTON_RECTS[coor] = rect
                SCREEN.blit(text_surface, rect)
                file_i += 1

    if current_state == St.DSP:
        SCREEN.blit(image, (20, 20))
        
    
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
        
