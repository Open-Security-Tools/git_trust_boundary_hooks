from setuptools import setup, find_packages
import os


setup(
    name=find_packages()[0],
    version="0.0.1",  # We are using python module versioning. All handled through docker.
    packages=find_packages(),
    include_package_data=True,  # We are installing via `pip -e`, so we don't need to worry about package data. 
    python_requires=">=3.8",
    install_requires=[
        "click==8.0.1",
        "humanize==4.0.0",
        "minio==7.1.9",
        "click-log==0.4.0",
        "bs4==0.0.1"
    ],
    entry_points={
        'console_scripts': [
            'tbh-setup = trust_boundary_hooks.cli:tbh_setup',
            'tbh-hook-pre-push = trust_boundary_hooks.cli:tbh_hook_pre_push',
            'tbh-hook-pre-commit = trust_boundary_hooks.cli:tbh_hook_pre_commit',
            'tbh-hook-commit-msg = trust_boundary_hooks.cli:tbh_hook_commit_msg',
            'tbh-utils = trust_boundary_hooks.cli:tbh_utils',
        ]
    }
)