from setuptools import setup, find_packages

import nadex


def read(path):
    with open(path, 'rb') as f:
        return f.read().strip()


setup(
    name='nadex',
    packages=find_packages(),
    version=nadex.__version__,
    description='Nadex API client',
    author='Kenji Noguchi',
    author_email='tokyo246@gmail.com',
    url='https://github.com/knoguchi/nadex',
    download_url = 'https://github.com/knoguchi/nadex/tarball/{}'.format(nadex.__version__),
    keywords=['nadex', 'forex', 'bitcoin', 'option', 'trading', 'api'],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Topic :: Office/Business :: Financial :: Investment',
        'Topic :: Software Development :: Libraries',
    ],
    scripts=['scripts/cancel-all-orders',
             'scripts/create-order',
             'scripts/get-contracts',
             'scripts/get-orders',
             'scripts/get-quote',
             'scripts/get-balance',
             'scripts/get-markets',
             'scripts/get-positions',
             'scripts/get-timeseries',
             'scripts/streamer',
    ],
)
