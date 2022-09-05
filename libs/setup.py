from setuptools import setup, find_packages

setup(
    name='libs',
    version='0.0.1',
    packages=find_packages(where='.'),
    install_requires=[
        'nats-py',
        'python-dotenv'
    ]
)