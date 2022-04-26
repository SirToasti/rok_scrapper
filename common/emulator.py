import subprocess
from ppadb.client import Client as AdbClient
from PIL import Image, ImageChops
import re
import time
import urllib.parse
import boto3
import logging
import config
import common.ocr

client = AdbClient(host='127.0.0.1', port=5037)
ec2_client = boto3.client('ec2')
ec2_resource = boto3.resource('ec2')

logger = logging.getLogger(__name__)

reference_patch = Image.open(r'samples\test_patch_a.png')
reference_patch_b = Image.open(r'samples\test_patch_b.png')
reference_patch_c = Image.open(r'samples\test_patch_c.png')

class Rok_Emulator:
    def __init__(self, config):
        self.config = config
        self.device = None
        self.name = config['name']

    def initialize(self):
        if self.config['type'] == 'genymotion':
            instance = ec2_resource.Instance(self.config['name'])
            logger.info('starting instance {}'.format(self.config['name']))
            instance.start()
            waiter = ec2_client.get_waiter('instance_status_ok')
            waiter.wait(InstanceIds=[self.config['name']])
            logger.info('instance {} ready'.format(self.config['name']))
        subprocess.run(['adb.exe', 'connect', self.config['address']])
        self.device = client.device(self.config['address'])

    def start_rok(self):
        self.device.shell("monkey -p com.lilithgame.roc.gp -c android.intent.category.LAUNCHER 1")
        i = 0
        while i < 12:
            screen = self.get_screen()
            if self.need_to_reconnect(screen):
                logger.warning('Need to reconnect...')
                self.tap_location((960, 700))
                i = 0
                continue
            result = self.finished_loading(screen)
            if result is not None:
                print('layout {}'.format(result))
                break
            time.sleep(10)
            i += 1
        # time.sleep(60)  # naive sleep for now. TODO: handle KE screen and stuff
        self.get_screen().save('output/{}_startup_{}.png'.format(self.name, 'end'))


    def need_to_reconnect(self, screen):
        try:
            result, _ = common.ocr.get_text(screen.crop(config.coordinates['1920x1080']['connect']))
            return 'CONFIRM' in result
        except:
            return False

    def finished_loading(self, screen):
        test_patch = screen.crop((18, 0, 130, 122))
        test_patch.save('output/test_patch.png')
        im = ImageChops.difference(reference_patch, test_patch).convert('1')
        if im.getbbox() is None:
            return 'a'
        im2 = ImageChops.difference(reference_patch_b, test_patch).convert('1')
        if im2.getbbox() is None:
            return 'b'
        im3 = ImageChops.difference(reference_patch_c, test_patch).convert('1')
        if im3.getbbox() is None:
            return 'c'
        return None

    def close_rok(self):
        self.device.shell("input keyevent KEYCODE_HOME")
        self.device.shell("am force-stop com.lilithgame.roc.gp")

    def tap_location(self, coords):
        self.device.shell("input tap {} {}".format(coords[0], coords[1]))
        time.sleep(1)

    def get_screen(self):
        self.device.shell("screencap -p /sdcard/Pictures/screen.png")
        self.device.pull("/sdcard/Pictures/screen.png", "output/{}.png".format(self.name))
        im = Image.open("output/{}.png".format(self.name))
        return im

    def get_clipboard(self):
        response = None
        def handler(connection):
            nonlocal response
            data = connection.read_all()
            output = data.decode('utf-8')
            resultMatcher = re.compile("^.*\n.*result=([\-]{0,1}[0-9]*).*")
            resultMatch = resultMatcher.match(output)
            if resultMatch and len(resultMatch.groups()) > 0:
                if len(resultMatch.group(1)) == 0:
                    logger.error('error getting clipboard. len is 0: {}'.format(resultMatch.group(1)))
                status = int(resultMatch.group(1))
                if status == -1:
                    # re.DOTALL to match newline as well
                    dataMatcher = re.compile("^.*\n.*data=\"(.*)\"$", re.DOTALL)
                    dataMatch = dataMatcher.match(output)
                    if dataMatch and len(dataMatch.groups()) > 0:
                        response = dataMatch.group(1)
            connection.close()

        self.device.shell("am broadcast -n ch.pete.adbclipboard/.ReadReceiver", handler=handler)
        return response

    def set_clipboard(self, text):
        def handler(connection):
            data = connection.read_all()
            output = data.decode('utf-8')
            resultMatcher = re.compile("^.*\n.*result=([\-]{0,1}[0-9]*).*")
            resultMatch = resultMatcher.match(output)
            if resultMatch and len(resultMatch.groups()) > 0:
                if len(resultMatch.group(1)) == 0:
                    logger.error('error pasting text. len is 0: {}'.format(resultMatch.group(1)))
                status = int(resultMatch.group(1))
                if status != -1:
                    logger.error('error pasting text. output: {}'.format(output))
        self.device.shell(r"am broadcast -n ch.pete.adbclipboard/.WriteReceiver -e text {}".format(urllib.parse.quote(text)), handler=handler)

    def paste(self):
        self.device.shell("input keyevent KEYCODE_PASTE")

    def stop(self):
        if self.config['type'] == 'genymotion':
            instance = ec2_resource.Instance(self.config['name'])
            instance.stop()
            logger.info('stopping instance {}'.format(self.config['name']))
