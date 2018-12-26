import subprocess
import platform
import requests
import tempfile
import os
from loguru import logger


# connection
DEFAULT_CHARSET = 'utf-8'

# installer
MNC_PREBUILT_URL = r'https://github.com/williamfzc/stf-binaries/raw/master/node_modules/minicap-prebuilt/prebuilt'
MNC_HOME = '/data/local/tmp/minicap'
MNC_SO_HOME = '/data/local/tmp/minicap.so'
TEMP_PIC_ANDROID_PATH = '/data/local/tmp/fastcap_temp.png'

# system
# 'Linux', 'Windows' or 'Darwin'.
SYSTEM_NAME = platform.system()
NEED_SHELL = SYSTEM_NAME != 'Windows'
if SYSTEM_NAME == 'Windows':
    ADB_EXECUTOR = subprocess.getoutput('where adb')
else:
    ADB_EXECUTOR = subprocess.getoutput('which adb')


def download_file(target_url):
    """ download file to temp path, and return its file path for further usage """
    resp = requests.get(target_url)
    with tempfile.NamedTemporaryFile('wb+', delete=False) as f:
        file_name = f.name
        f.write(resp.content)
    return file_name


def is_device_connected(device_id):
    """ return True if device connected, else return False """
    try:
        device_name = subprocess.check_output([ADB_EXECUTOR, '-s', device_id, 'shell', 'getprop', 'ro.product.model'])
        device_name = device_name.decode(DEFAULT_CHARSET).replace('\n', '').replace('\r', '')
        logger.info('device {} online'.format(device_name))
    except subprocess.CalledProcessError:
        return False
    return True


class MNCInstaller(object):
    """ install minicap for android devices """
    def __init__(self, device_id):
        assert is_device_connected(device_id)

        self.device_id = device_id
        self.abi = self.get_abi()
        self.sdk = self.get_sdk()
        if self.is_mnc_installed():
            logger.info('minicap already existed in {}'.format(device_id))
        else:
            self.download_target_mnc()
            self.download_target_mnc_so()

    def get_abi(self):
        """ get abi (application binary interface) """
        abi = subprocess.getoutput('{} -s {} shell getprop ro.product.cpu.abi'.format(ADB_EXECUTOR, self.device_id))
        logger.info('device {} abi is {}'.format(self.device_id, abi))
        return abi

    def get_sdk(self):
        """ get sdk version """
        sdk = subprocess.getoutput('{} -s {} shell getprop ro.build.version.sdk'.format(ADB_EXECUTOR, self.device_id))
        logger.info('device {} sdk is {}'.format(self.device_id, sdk))
        return sdk

    def download_target_mnc(self):
        """ download specific minicap """
        target_url = '{}/{}/bin/minicap'.format(MNC_PREBUILT_URL, self.abi)
        logger.info('target minicap url: ' + target_url)
        mnc_path = download_file(target_url)

        # push and grant
        subprocess.check_call([ADB_EXECUTOR, '-s', self.device_id, 'push', mnc_path, MNC_HOME], stdout=subprocess.DEVNULL)
        subprocess.check_call([ADB_EXECUTOR, '-s', self.device_id, 'shell', 'chmod', '777', MNC_HOME])
        logger.info('minicap installed in {}'.format(MNC_HOME))

        # remove temp
        os.remove(mnc_path)

    def download_target_mnc_so(self):
        """ download specific minicap.so (they should work together) """
        target_url = '{}/{}/lib/android-{}/minicap.so'.format(MNC_PREBUILT_URL, self.abi, self.sdk)
        logger.info('target minicap.so url: ' + target_url)
        mnc_so_path = download_file(target_url)

        # push and grant
        subprocess.check_call([ADB_EXECUTOR, '-s', self.device_id, 'push', mnc_so_path, MNC_SO_HOME], stdout=subprocess.DEVNULL)
        subprocess.check_call([ADB_EXECUTOR, '-s', self.device_id, 'shell', 'chmod', '777', MNC_SO_HOME])
        logger.info('minicap.so installed in {}'.format(MNC_SO_HOME))

    def is_installed(self, name):
        """ check if is existed in /data/local/tmp """
        return bool(subprocess.check_output([
            ADB_EXECUTOR, '-s', self.device_id, 'shell',
            'find', '/data/local/tmp', '-name', name])
        )

    def is_mnc_installed(self):
        """ check if minicap installed """
        return self.is_installed('minicap') and self.is_installed('minicap.so')


class MNCDevice(object):
    """ device operator """
    def __init__(self, device_id):
        self.device_id = device_id
        MNCInstaller(device_id)
        self.screen = self.get_size()

    def get_size(self):
        """ get screen size, return value looks like (1080, 1920) """
        result_str = subprocess.check_output([
            ADB_EXECUTOR, '-s', self.device_id, 'shell',
            'wm', 'size'
        ]).decode(DEFAULT_CHARSET)
        width, height = result_str.replace('\n', '').replace('\r', '').split(' ')[-1].split('x')
        return width, height

    def screen_shot(self):
        """ take a screen shot """
        screen_size = '{}x{}@{}x{}/0'.format(self.screen[0], self.screen[1], self.screen[0], self.screen[1])
        subprocess.check_call([
            ADB_EXECUTOR, '-s', self.device_id, 'shell',
            'LD_LIBRARY_PATH=/data/local/tmp', '/data/local/tmp/minicap', '-s', '-P', screen_size,
            '>', TEMP_PIC_ANDROID_PATH
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info('screen shot saved in {}'.format(TEMP_PIC_ANDROID_PATH))

    def export_screen(self, target_path):
        """ pull screen shot and move it to target path """
        subprocess.check_call([
            ADB_EXECUTOR, '-s', self.device_id,
            'pull', TEMP_PIC_ANDROID_PATH, target_path
        ], stdout=subprocess.DEVNULL)
        logger.info('export screen shot to {}'.format(target_path))


if __name__ == '__main__':
    d = MNCDevice('3d33076e')
    d.screen_shot()
    d.export_screen('./aaa.png')
