from setuptools import setup, find_packages

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
)
