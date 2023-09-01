import mido
import keyboard
import threading
import PySimpleGUI as sg
import time
from pynput.keyboard import Key, Controller
keyboard1 = Controller()
table = str.maketrans("!@#$%^&*()", "1234567890")
mid=None
pitch_shift=0
i=0
ds=0
jumpflag=None
jump_to=0
def update_ui():
    while True:
        window['-PROG-'].update(ds)
        window['-TIME-'].update(f'{ds:.2f} / {mid.length:.2f}')
        time.sleep(5)
ui_thread = threading.Thread(target=update_ui)
def note_to_key(note):
    midi_to_vk = (
        [None]*24 +
        list('1!2@34$5%6^71!2@34$5%6^78*9(0qQwWeErtTyYuiIoOpPasSdDfgGhHjJklLzZxcCvVbBnmLzZxcCvVbBn') +
        [None]*36
    )
    return midi_to_vk[note]


def play_midi():
    global cond
    global i
    global msg
    global mid
    global jump_to
    global jumpflag
    global ds
    for msg in mid:
        global pitch_shift
        if msg.time!=0:
            i += msg.time
            
            
        if i < jump_to:
            jumpflag=0
            continue
        if i > jump_to and jump_to !=None and jumpflag==1:
            i=0
            break
        if msg.time != 0:
            ds=i
            time.sleep(msg.time*0.995)
        
        if msg.type == 'note_on' and msg.velocity != 0:
            while msg.note-pitch_shift > 95 or msg.note-pitch_shift < 36: 
                if msg.note-pitch_shift > 95: 
                    keyboard1.press(Key.up) 
                    keyboard1.release(Key.up) 
                    pitch_shift =pitch_shift+ 1 
                elif msg.note-pitch_shift < 36: 
                    keyboard1.press(Key.down) 
                    keyboard1.release(Key.down) 
                    pitch_shift =pitch_shift- 1
                
            key = note_to_key(msg.note-pitch_shift)
            if key is not None:
                if ord(key) >= 65 and ord(key) <= 90:
                    if not keyboard.is_pressed("shift"):
                        keyboard.press("shift")
                    code = ord(key)
                    code += 32
                    key=chr(code)
                elif key in '!@#$%^&*()':
                    if not keyboard.is_pressed("shift"):
                        keyboard.press("shift")
                    key=key.translate(table)
                else:
                    keyboard.release("shift")
                keyboard.press_and_release(key)
        with cond:
            while paused: 
                cond.wait()
    
    keyboard.release("shift")
    if jumpflag==0:
        jump_to=0
        i=0
        window["-PAUSE-"].update(disabled=True)
        window["-PLAY-"].update(text="Play", disabled=False)
    else:
        jumpflag=0
        
my_pink_theme = {'BACKGROUND': 'pink',
                'TEXT': 'white',
                'INPUT': 'pink',
                'TEXT_INPUT': 'white',
                'SCROLL': '#c7e78b',
                'BUTTON': ('white', 'pink'),
                'PROGRESS': ('#01826B', '#D0D0D0'),
                'BORDER': 1, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0,
                }


sg.theme_add_new('MyPink', my_pink_theme)


sg.theme('MyPink')

# 定义GUI的布局
layout = [
    [sg.Text("Unravel MIDI Player", font=("Arial", 20), background_color='pink', text_color='white')],
    [sg.Button("Play", key="-PLAY-", button_color=('white', 'pink')), sg.Button("Pause", key="-PAUSE-", button_color=('white', 'pink'), disabled=True), sg.Button("Exit", key="-EXIT-", button_color=('white', 'pink'))],
    [sg.Text("Status: Waiting for select", key="-STATUS-", size=(40, 1), background_color='pink', text_color='white')],
    [sg.ProgressBar(1, orientation='h', size=(20, 20), key='-PROG-', bar_color=('#F5DADF', 'white'))], # 添加一个进度条元素
    [sg.Text('跳转到', size=(5, 1), background_color='pink', text_color='white'), sg.InputText(size=(5, 1), key='jump'), sg.Text('秒', size=(2, 1), background_color='pink', text_color='white'), sg.Button('Ok', button_color=('white', 'pink'))], # 添加一个输入框和一个文本元素
    [sg.Text('', size=(10, 1), key='-TIME-', background_color='pink', text_color='white')],
    [sg.Text('选择一个MIDI文件', size=(10, 1), background_color='pink', text_color='white'), sg.Input(key='-FILE-', enable_events=True, text_color='#E75480',disabled=True), sg.FileBrowse(file_types=(("MIDI Files", "*.mid"),), button_color=('white', 'pink'))],

]



window = sg.Window("Unravel MIDI Player", layout)


thread = threading.Thread(target=play_midi)

cond = threading.Condition()
paused = False
while True:
    event, values = window.read()
    if event == "-PLAY-":
        if mid != None:
            
            time.sleep(1)
            if not thread.is_alive():

                window['-PROG-'].UpdateBar(0,max=mid.length)
                thread = threading.Thread(target=play_midi)
                thread.start()
            else:
                with cond:
                    paused = False
                    cond.notify()
            window["-STATUS-"].update("Status: Playing")
            window["-PLAY-"].update(disabled=True)
            window["-PAUSE-"].update(disabled=False)
            window["-PLAY-"].update(text="Resume", disabled=True)
            
            if not ui_thread.is_alive():
                ui_thread.start()
            time.sleep(0.1)
            if not thread.is_alive():
                window['-PROG-'].UpdateBar(0,max=mid.length)
                thread = threading.Thread(target=play_midi)
                thread.start()
            
        else:
            sg.popup_error('请选择midi文件')
    elif event == '-FILE-':
        file = values['-FILE-']
        if file.endswith('.mid'):
            mid = mido.MidiFile(file)
            window["-PLAY-"].update(text="Play", disabled=False)
            window["-STATUS-"].update(f"Status: Ready")
            ds=0
            jump_to=0
            if thread.is_alive():
                jumpflag=1
            
        else:
            sg.popup_error('请选择一个有效的MIDI文件')

    elif event == "-PAUSE-":
        with cond:
            paused = True
        keyboard.release("shift")
        window["-STATUS-"].update("Status: Paused")
        window["-PAUSE-"].update(disabled=True)
        window["-PLAY-"].update(text="Resume", disabled=False)
    elif event == 'Ok':
        try:
            jump_to = float(values['jump'])
            jumpflag=1
            ds=jump_to
            
        except ValueError:
            sg.popup_error('请输入一个有效的数字')
    elif event == "-EXIT-" or event == sg.WIN_CLOSED:
        break

window.close()
