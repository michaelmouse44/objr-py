from abc import ABC, abstractmethod
from collections import namedtuple
from enum import Enum
from tempfile import TemporaryDirectory
from typing import Callable
from pandas import DataFrame
import pandas
import subprocess
import os
from getpass import getpass

Credentials = namedtuple('Credentials', ['username', 'password'])

FileType = Enum("FileType", ["EXCEL", "CSV"])

class CredentialGetter(ABC):
    @abstractmethod
    def get_credentials(self) -> Credentials:
        pass

class PromptCredentialGetter(CredentialGetter):
    def __init__(self, username_prompt: str = "Username", password_prompt: str = "Password"):
        self.username_prompt = username_prompt
        self.password_prompt = password_prompt

    def get_credentials(self) -> Credentials:
        username = input(f"{self.username_prompt}: ")
        password = getpass(f"{self.password_prompt}: ")
        return Credentials(username, password)

class EnvCredentialGetter(CredentialGetter):
    def __init__(self, username_var: str = "OBJR_USR", password_var: str = "OBJR_PWD"):
        self.username_var = username_var
        self.password_var = password_var

    @staticmethod
    def _get_env_var(var: str) -> str:
        value = os.getenv(var)
        if value is None:
            raise KeyError(f"{var} not found in environment variables")
        return value

    def get_credentials(self) -> Credentials:
        username = self._get_env_var(self.username_var)
        password = self._get_env_var(self.password_var)
        return Credentials(username, password)

class Objr:
    def __init__(self, credential_getter: CredentialGetter):
        self.credential_getter = credential_getter

    @staticmethod
    def get_environment_copy() -> dict[str, str]:
        return os.environ.copy()

    @staticmethod
    def run_download_process(script_path: str, uuid: str, directory: str, env: dict[str, str]) -> str:
        output = subprocess.run(["Rscript", script_path, uuid, directory], env=env, check=True, capture_output=True)
        return output.stdout.decode()

    @staticmethod
    def get_data_loader(file_type: FileType) -> Callable[[str], DataFrame]:
        data_loaders: dict[FileType, Callable[[str], DataFrame]] = {
            FileType.EXCEL: pandas.read_excel,
            FileType.CSV: pandas.read_csv
        }
        return data_loaders[file_type]
    
    @staticmethod
    def temp_dir():
        return TemporaryDirectory()

    def download(self, uuid: str, file_type: FileType):
        env = self.get_environment_copy()
        credentials = self.credential_getter.get_credentials()
        env["OBJR_USR"] = credentials.username
        env["OBJR_PWD"] = credentials.password
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "oc_download.R")
        with self.temp_dir() as directory:
            output = self.run_download_process(script_path=script_path, uuid=uuid, directory=directory, env=env)
            quoted_data_filename = output.split()[1]
            data_filename = quoted_data_filename[1:-1]
            data_path = os.path.join(directory, data_filename)
            loader = self.get_data_loader(file_type)
            return loader(data_path)

def download_data(uuid: str, file_type: FileType, prompt: bool = False):
    credential_getter = PromptCredentialGetter() if prompt else EnvCredentialGetter()
    objr = Objr(credential_getter)
    return objr.download(uuid, file_type)
