from setuptools import setup

setup(
    name='Vkbot_diary',
    version='1.0.0',
    description='Useful bot for VK',
    author='Valyon, Andrew, Sergey',
    author_email='astyn37@gmail.com',
    packages=['Vkbot_diary'],
    install_requires=[s for s in
                      [line.split('#', 1)[0].strip(' \t\n') for line in open('requirements.txt', 'r').readlines()] if
                      s != '']
)
