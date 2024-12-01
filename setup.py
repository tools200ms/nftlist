from setuptools import setup, find_packages
#from setuptools.command.install ct install
from setuptools.command.install import install
import os
import shutil

# HowTo prepare package and push:
# install necessary tools:
# pip install setuptools wheel twine
# Build package:
# python setup.py sdist bdist_wheel
# Install locally to test it:
# pip install ./dist/pip install ./dist/my_project-0.1.0-py3-none-any.whl-0.1.0-py3-none-any.whl
#
# Upload to repository:
# twine upload dist/*

class PostInstallCommand(install):
    def run(self):
        # Run the standard installation process
        install.run(self)
        # Copy systemd service file
        setup_files_dir = os.path.join(os.path.dirname(__file__), 'setup')

        if shutil.which("systemctl") is not None:
            shutil.copy(os.path.join(setup_files_dir, 'nftlist.service'), '/etc/systemd/system/nftlist.service')
            os.system('systemctl daemon-reload')
            os.system('systemctl enable nftlist.service')
        elif shutil.which("rc-update") is not None:
            shutil.copy(os.path.join(setup_files_dir, 'nftlist.init'), '/etc/init.d/nftlist')
            os.system('rc-update add nftlist boot')

setup(
    name="nftlist",
    version="0.1.0",
    description="NFT complementing tool for blocking/allowing traffic based on domain names, IP or mac adresses.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/tools200ms/nftlist",
    author="Mateusz (Barnaba) Piwek",
    author_email="barnaba@200ms.net",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux"
    ],
    packages=find_packages(),
    python_requires=">=3.12",
    install_requires=[
        "nft>=2.7"
    ],
    cmdclass={
        'install': PostInstallCommand
    }
)
