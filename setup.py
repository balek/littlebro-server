from setuptools import setup, find_packages

setup(
    name='littlebro-server',
    version='0.5.4',
    description='CCTV system',
    author='Alexey Balekhov',
    author_email='a@balek.ru',
    url='https://github.com/balek/littlebro-server',
    license='AGPL-3.0',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'littlebro-http = littlebro_server.http:main',
            'littlebro-archive = littlebro_server.archive:main',
            'littlebro-motion = littlebro_server.motion:main',
            'littlebro-stream = littlebro_server.stream:main',
            'littlebro-trigger = littlebro_server.trigger:main',
        ],
    },
    install_requires=['aiohttp', 'aiohttp_session', 'pyjwt', 'pyinotify'],
    extras_require={
        'SMTP': ['aiosmtpd'],
    })
