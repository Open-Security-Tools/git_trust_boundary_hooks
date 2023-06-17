from .scan import Scanner
import subprocess
import os
from bs4 import UnicodeDammit
import logging
from typing import List
from . import errors
import time


log = logging.getLogger(__name__)


class Operations:

    def __init__(self) -> None:
        self._scanner = Scanner()

    @property
    def cached_files(self) -> List[str]:
        output = subprocess.check_output(['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM']).decode('utf-8')
        return output.splitlines(keepends=False)

    @property
    def untracked_files(self) -> List[str]:
        output = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard']).decode('utf-8')
        return output.splitlines(keepends=False)

    def scan_cached_files(self) -> None:
        log.info("Scanning cached files")
        self._scan_files(files=self.cached_files)

    def _scan_files(self, files: List[str]) -> None:
        log.info(f"Looking for bad symbols in {len(files)} file(s)...")
        for fn in files:
            log.debug(f"Scanning file '{fn}'")
            self._scanner.scan_string(context=f"FileName({fn})", value=fn)
            with open(fn, "rb") as f:
                # We use a utility to manage detection and decoding.
                raw_content = f.read()
                decoded = ""
                if raw_content:
                    dammit = UnicodeDammit(raw_content)
                    decoded = dammit.unicode_markup
                    if decoded:
                        log.debug(f"Original Encoding of {fn} = {dammit.original_encoding}")
                    else:
                        log.warning(f"Decoding content of '{fn}' as text failed")

            if decoded:
                self._scanner.scan_string(context=f"FileContent({fn})", value=decoded)

    def scan_untracked_files(self) -> None:
        log.info("Scanning untracked files")
        self._scan_files(files=self.untracked_files)

    @property
    def author_name(self) -> str:
        return os.environ["GIT_AUTHOR_NAME"]

    @property
    def author_email(self) -> str:
        return os.environ.get["GIT_AUTHOR_EMAIL"]

    def scan_author_metadata(self) -> None:
        log.info("Looking for bad symbols in git author metadata...")
        self._scanner.scan_string(context="GitAuthor", value=self.author_name)
        self._scanner.scan_string(context="GitEmail", value=self.author_email)

    def pre_commit_hook(self) -> None:
        log.info("pre-commit-hook")
        self.scan_cached_files()
        self.scan_author_metadata()
        self.assert_no_errors()

    def assert_no_errors(self) -> None:
        if self._scanner.detections:
            log.error(f"Detection of {len(self._scanner.detections)} bad symbol(s)!")
            self._scanner.display_detections()
            raise errors.BadSymbolsDetectedError("Bad symbols detected in local changes!")
        else:
            log.info("No bad symbols detected")

    def commit_message_hook(self, message: str) -> None:
        log.info("commit-message-hook")

        self._scanner.scan_string(context="CommitMessage", value=message)
        self.assert_no_errors()

    def scan_git_history(self) -> None:
        log.info("Scanning git history")
        t1 = time.time()
        history = subprocess.check_output(["git", "--no-pager", "log", "-p", "--all"]).decode('utf-8')

        t2 = time.time()
        self._scanner.scan_string(context=f"GitHistory", value=history)
        t3 = time.time()
        if log.isEnabledFor(logging.DEBUG):
            log.debug(f"History size = {len(history)} bytes")
            log.debug(f"Time to extract git history = {t2-t1} seconds")
            log.debug(f"Time to process git history = {t3-t2} seconds")

    def pre_push_hook(self) -> None:
        log.info("pre-push-hook")
        self.scan_git_history()
        self.assert_no_errors()