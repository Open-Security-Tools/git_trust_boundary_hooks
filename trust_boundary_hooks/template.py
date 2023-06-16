import os
import logging
from . import errors
import sys
from pathlib import Path
import json
from minio import Minio
from minio.error import S3Error
import urllib3
import subprocess


log = logging.getLogger(__name__)


class Template:

    def __init__(self) -> None:
        self._path = os.path.expanduser("~/.git-template")
        self._confirm_ownership_file = os.path.join(self._path, "managed_by_tbh")
        self._hooks_path = os.path.join(self._path, "hooks")
        self._bad_symbols_path = os.path.expanduser("~/.tbh_bad_symbols")
        self._minio_config = os.path.expanduser("~/.tbh_minio_config")

    @property
    def bad_symbols_path(self) -> str:
        return self._bad_symbols_path

    @property
    def can_setup(self) -> bool:
        if not os.path.exists(self._path):
            return True
        
        return os.path.exists(self._confirm_ownership_file)

    def _dsl_link_script_name(self, link_name: str, python_script_name: str) -> None:
        bin_path = Path(sys.executable).parent.absolute()
        python_script_path = os.path.join(bin_path, python_script_name)
        if not os.path.exists(python_script_path):
            raise RuntimeError(f"Missing python script entry point '{python_script_path}'")
        link_path = os.path.join(self._hooks_path, link_name)
        link_exists = os.path.exists(link_path)
        link_content = None
        if link_exists:
            link_content = os.readlink(link_path)
        if link_content != python_script_path:
            action = "Updating" if link_exists else "Creating"
            log.info(f"{action} sym link from '{link_name}' to python entrypoint '{python_script_name}'")
            os.symlink(src=python_script_path, dst=link_path)


    def _setup_hooks_directory(self) -> None:
        if not self.can_setup:
            raise errors.CannotOverwriteTemplateDirectoryError(f"Unable to overwrite templates at '{self._path}'!")
        log.info(f"Setting up hooks template in '{self._path}'")

        # Main template directory        
        if not os.path.exists(self._path):
            log.info(f"Creating directory '{self._path}'")
            os.mkdir(self._path)

            # If we are creating the main path, then assert ownership
            with open(self._confirm_ownership_file, "w") as f:
                f.write("This directory is managed by the Trust Boundary Hooks python utility.")

        # Hooks subdirectory
        if not os.path.exists(self._hooks_path):
            log.info(f"Creating directory '{self._hooks_path}'")
            os.mkdir(self._hooks_path)

        # Hook symlinks
        for link_name, python_script_name in (
            ("pre-commit", "tbh-hook-pre-commit"),
            ("pre-push", "tbh-hook-pre-push"),
            ("commit-msg", "tbh-hook-commit-msg"),
            ("tbh-utils", "tbh-utils"),
        ):
            self._dsl_link_script_name(link_name=link_name, python_script_name=python_script_name)


    def _setup_minio_config(self) -> None:
        if os.path.exists(self._minio_config):
            return
        example_config = {
            "access_key": "",
            "secret_key": "",
            "bucket": "",
            "object": "",
            "endpoint": "",
            "ca_path": "",
        }
        log.info(f"Creating example MINIO configuration at '{self._minio_config}'")
        with open(self._minio_config, "w") as f:
            f.write(json.dumps(example_config, indent=4))

    def update_bad_symbols(self) -> None:
        with open(self._minio_config, "r") as f:
            config = json.load(fp=f)

        def _get_val(k: str) -> str:
            try:
                v = config[k]
            except KeyError:
                raise errors.MinioConfigError(f"Minio config ({self._minio_config}) missing key '{k}'") from None
            if not v:
                raise errors.MinioConfigError(f"Minio config ({self._minio_config}) empty key '{k}'")
            return v

        access_key = _get_val("access_key")
        secret_key = _get_val("secret_key")
        bucket = _get_val("bucket")
        object = _get_val("object")
        endpoint = _get_val("endpoint")
 
        # Minio doesn't use protocol prefixes
        if endpoint.startswith("https://"):
            endpoint = endpoint[len("https://"):]

        ca_path = os.path.expanduser(_get_val("ca_path"))

        if not os.path.exists(ca_path):
            raise errors.MinioConfigError(f"Minio config ({self._minio_config}) points to bad CA path '{ca_path}'")

        log.info(f"Connecting to MINIO server {endpoint}")
        http_client = urllib3.PoolManager(cert_reqs="CERT_REQUIRED", ca_certs=ca_path)
        c = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            http_client=http_client,
        )
        log.info(f"Comparing bad symbols with bucket '{bucket}' object '{object}'")
        try:
            resp = c.get_object(
                bucket_name=bucket,
                object_name=object,
            )
            file_content = resp.read().decode('utf-8')
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise errors.MinioObjectMissingError(f"Minio bucket '{bucket}' missing object '{object}'") from e
            raise

        old_file_content = None
        if os.path.exists(self._bad_symbols_path):
            with open(self._bad_symbols_path, "r") as f:
                old_file_content = f.read()

        if old_file_content is None or old_file_content != file_content:
            action = "Creating" if old_file_content is None else "Updating"
            log.info(f"{action} bad symbols file '{self._bad_symbols_path}'")

            with open(self._bad_symbols_path, "w") as f:
                f.write(file_content)

    def _setup_git_global_template_configuration(self) -> None:
        old_value = subprocess.check_output(["git", "config", "--global", "init.templateDir"]).decode('utf-8').strip()
        if old_value != self._path:
            log.info(f"Setting the git global template directory to '{self._path}'")
            _ = subprocess.check_output(["git", "config", "--global", "init.templateDir", self._path])

    def setup(self) -> None:
        """
    3. Calls git set the global configuration for template hooks
    5. Prompts for credentials to access the Minio object store with bad symbols
    6. Stores the bad symbols in ~/.badsymbols

        """
        self._setup_hooks_directory()
        self._setup_minio_config()
        self.update_bad_symbols()
        self._setup_git_global_template_configuration()
