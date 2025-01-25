from setuptools import setup
from setuptools.command.install import install
import os
import shutil


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

setup()
