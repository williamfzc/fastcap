import subprocess
import platform
import requests
import tempfile
import os
from loguru import logger


# connection
DEFAULT_HOST = '127.0.0.1'
DEFAULT_CHARSET = 'utf-8'

# installer
MNC_PREBUILT_URL = r'https://github.com/williamfzc/stf-binaries/raw/master/node_modules/minicap-prebuilt/prebuilt'
MNC_HOME = '/data/local/tmp/minicap'
MNC_SO_HOME = '/data/local/tmp/minicap.so'

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
        abi = subprocess.getoutput('{} -s {} shell getprop ro.product.cpu.abi'.format(ADB_EXECUTOR, self.device_id))
        logger.info('device {} abi is {}'.format(self.device_id, abi))
        return abi

    def get_sdk(self):
        sdk = subprocess.getoutput('{} -s {} shell getprop ro.build.version.sdk'.format(ADB_EXECUTOR, self.device_id))
        logger.info('device {} sdk is {}'.format(self.device_id, sdk))
        return sdk

    def download_target_mnc(self):
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
        return self.is_installed('minicap') and self.is_installed('minicap.so')


if __name__ == '__main__':
    MNCInstaller('3d33076e')
