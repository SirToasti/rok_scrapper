import subprocess
from ppadb.client import Client as AdbClient
from PIL import Image
import re
import time
import urllib.parse
import boto3
import logging

client = AdbClient(host='127.0.0.1', port=5037)
ec2_client = boto3.client('ec2')
ec2_resource = boto3.resource('ec2')

logger = logging.getLogger(__name__)

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
        time.sleep(60)  # naive sleep for now. TODO: handle KE screen and stuff
        self.get_screen()


    def close_rok(self):
        self.device.shell("input keyevent KEYCODE_HOME")

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
