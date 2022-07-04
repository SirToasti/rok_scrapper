import pyautogui
import keyboard
import pygetwindow
import time
import subprocess
import config
from tkinter import Tk

def make_upscaled_coords():
    coords = {}
    h_factor = 2560/1920
    v_factor = 1440/1080
    for key, value in config.coordinates['1920x1080'].items():
        if len(value) == 4:
            coords[key] = (value[0]*h_factor, value[1]*v_factor, value[2]*h_factor, value[3]*v_factor)
        if len(value) == 2:
            coords[key] = (value[0] * h_factor, value[1] * v_factor)
    return coords

coords = make_upscaled_coords()

class PC_Client:
    def __init__(self):
        self.target_window_size = (1920, 1080)
        # self.target_window_size = (2560, 1440)
        self.game_client = None
        pass

    def initialize(self):
        # subprocess.Popen(["C:\Program Files (x86)\ROK\launcher.exe"], cwd="C:\Program Files (x86)\ROK")
        self.game_client = subprocess.Popen(["C:\Program Files (x86)\ROK\MASS.exe", "a5117180fe06c8dcc14ff00346d486c8"], cwd="C:\Program Files (x86)\ROK")
        time.sleep(30)
        self.make_fullscreen()
        self.setup_governor_search()
        pass

    def close_rok(self):
        if self.game_client:
            self.game_client.terminate()

    def make_fullscreen(self):
        game_window = pygetwindow.getWindowsWithTitle('Rise of Kingdoms')[0]
        game_window.activate()
        print(game_window.size)
        print(game_window.isMaximized)
        if (game_window.width == self.target_window_size[0] and game_window.height == self.target_window_size[1]):
            return
        keyboard.press_and_release('alt+enter')
        print('sent keystroke')
        time.sleep(2)
        self.make_fullscreen()

    def tap_location(self, coords, delay=1):
        print(coords)
        pyautogui.moveTo(*coords)
        time.sleep(.3)
        pyautogui.mouseDown()
        pyautogui.mouseUp()
        time.sleep(delay-.3)
        pass

    def setup_governor_search(self):
        print('setting up governor search')
        self.tap_location((300 * self.target_window_size[0]/2560, 1355 * self.target_window_size[1]/1440))
        self.tap_location((55 * self.target_window_size[0]/2560, 45 * self.target_window_size[1]/1440))
        self.tap_location((1890 * self.target_window_size[0]/2560, 725 * self.target_window_size[1]/1440))



    def get_screen(self):
        return pyautogui.screenshot(region=(0, 0, self.target_window_size[0], self.target_window_size[1]))

    def get_clipboard(self):
        return Tk().clipboard_get()

    def type(self, s):
        pyautogui.write(str(s))

    def process_profile(self):
        self.tap_location(coords['name'])
        self.tap_location(coords['expand_kill_points'])
        kills = self.get_screen()
        kills.show()
        governor_id = self.extract_governor_id(kills)
        name = self.get_clipboard()
        print(name)
        self.tap_location(coords['more_info'])
        more_info = self.get_screen()
        more_info.show()
        self.storage.save_text(name, '{}_name.txt'.format(governor_id))
        self.storage.save_image(kills, '{}_kills.png'.format(governor_id))
        self.storage.save_image(more_info, '{}_more_info.png'.format(governor_id))
        self.tap_location(coords['close_more_info'])
        self.tap_location(coords['close_profile'])


def main():
    print(coords)
    return
    time.sleep(2)
    client = PC_Client()
    client.initialize()
    client.make_fullscreen()
    client.setup_governor_search()
    client.search_for_governor(70180227)
    client.process_profile()


    while True:
        x, y = pyautogui.position()
        positionStr = 'X: ' + str(x).rjust(4) + ' Y: ' + str(y).rjust(4)
        print(positionStr)
        time.sleep(1)


if __name__ == "__main__":
    main()