"""Setup script for ReadAloud."""

from setuptools import setup, find_packages

from readaloud import __version__

setup(
    name="readaloud",
    version=__version__,
    description="Scan printed text and have it read aloud",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="ReadAloud Team",
    url="https://github.com/yeager/ReadAloud",
    license="GPL-3.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "readaloud": ["../locale/*/LC_MESSAGES/*.mo"],
    },
    data_files=[
        ("share/applications", ["data/se.readaloud.App.desktop"]),
    ],
    entry_points={
        "console_scripts": [
            "readaloud=readaloud.main:main",
        ],
    },
    install_requires=[
        "PyGObject>=3.42",
        "opencv-python>=4.5",
        "pytesseract>=0.3",
        "pdfplumber>=0.7.0",
        "pypdf>=3.0.0",
        "python-docx>=0.8.11",
    ],
    extras_require={
        "pyttsx3": ["pyttsx3>=2.90"],
        "piper": ["piper-tts>=1.2.0"],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Topic :: Accessibility",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
    ],
)
