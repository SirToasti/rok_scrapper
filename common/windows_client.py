import pyautogui
import pygetwindow
import time
import subprocess

class PC_Client:
    def __init__(self):
        self.target_window_size = (2560, 1440)
        pass

    def initialize(self):
        # subprocess.Popen(["C:\Program Files (x86)\ROK\launcher.exe"], cwd="C:\Program Files (x86)\ROK")
        # subprocess.Popen(["C:\Program Files (x86)\ROK\MASS.exe", "a451462f83e7af0865bfbf8293b58d7a"], cwd="C:\Program Files (x86)\ROK")
        pass

    def make_fullscreen(self):
        game_window = pygetwindow.getWindowsWithTitle('Rise of Kingdoms')[0]
        game_window.activate()
        print(game_window.isMaximized)
        if (game_window.width == self.target_window_size[0] and game_window.height == self.target_window_size[1]):
            return
        pyautogui.hotkey('alt', 'enter')
        self.make_fullscreen()

    def tap_location(self, coords, delay=1):
        pyautogui.moveTo(*coords)
        time.sleep(delay)
        pyautogui.click()
        pass

    def search_for_governor(self, gov_id):
        self.tap_location((300, 1355))
        self.tap_location((55, 45))
        self.tap_location((125, 325))
        self.tap_location((800, 275))
        pyautogui.write(str(gov_id))
        self.tap_location((1740, 275))
        self.tap_location((790, 550))
        self.tap_location((780, 285))


def main():
    client = PC_Client()
    client.initialize()
    client.make_fullscreen()
    client.search_for_governor(70180227)


    while True:
        x, y = pyautogui.position()
        positionStr = 'X: ' + str(x).rjust(4) + ' Y: ' + str(y).rjust(4)
        # print(positionStr)
        time.sleep(1)


if __name__ == "__main__":
    main()