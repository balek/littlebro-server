from setuptools import setup

setup(
    name = 'littlebro-server',
    version = '0.3',
    description = 'CCTV system',
    author = 'Alexey Balekhov',
    author_email = 'a@balek.ru',
    url = 'https://github.com/balek/littlebro-server',
    license = 'AGPL-3.0',

    package_dir = {'littlebro_server': 'src'},
    packages = ['littlebro_server'],

    entry_points = {
        'console_scripts': [
            'littlebro-archive = littlebro_server.archive:main',
            'littlebro-motion = littlebro_server.motion:main',
            'littlebro-stream = littlebro_server.stream:main',
            'littlebro-trigger = littlebro_server.trigger:main',
        ],
    },
    install_requires = ['pyinotify'],
    extras_require = {
        'SMTP':  ['aiosmtpd'],
        'Hikvision': ['aiohttp'],
    }
)
