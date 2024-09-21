from setuptools import setup, find_packages

setup(
    version="1.0",
    name="auto_subtitle",
    packages=find_packages(),
    py_modules=["auto_subtitle"],
    author="Bilal ahmed",
    install_requires=[
        'openai-whisper',
    ],
    description="Auto generate and add subtitles to your videos",
    entry_points={
        'console_scripts': ['auto_subtitle=main:main'],
    },
    include_package_data=True,
)