from setuptools import setup, find_packages


setup(
    name='fastcap',
    version='0.1.0',
    description='fast screen cap on android, with minicap.',
    author='williamfzc',
    author_email='fengzc@vip.qq.com',
    url='https://github.com/williamfzc/fastcap',
    packages=find_packages(),
    install_requires=[
        'loguru',
        'requests',
    ]
)
