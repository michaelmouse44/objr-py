from typing import Any
from unittest.mock import MagicMock
from objr_py import CredentialGetter, Credentials, FileType, Objr
from contextlib import contextmanager
from pandas import DataFrame
import os

class FakeCredentialGetter(CredentialGetter):
    def get_credentials(self) -> Credentials:
        return Credentials(username="test_user", password="test_pass")

@contextmanager
def temp_dir(dirs: dict[str, str]):
    dir = "temp-dir"
    dirs[dir] = {}
    yield dir
    del dirs[dir]

def test_something():
    # Arrange
    uuid = "abcd"
    objr = Objr(FakeCredentialGetter())
    objr.get_environment_copy = MagicMock(return_value={"PATH": "mypath"})
    dirs = {}
    objr.temp_dir = MagicMock(return_value=temp_dir(dirs))
    def rdp(script_path, uuid, directory, env):
        dirs[directory]["test.xlsx"] = None
        return '[1] "test.xlsx"'
    objr.run_download_process = MagicMock(side_effect=rdp)
    load_data = MagicMock(return_value=DataFrame(range(0, 10) for _ in range(0, 5)))
    objr.get_data_loader = MagicMock(return_value=load_data)

    # Act
    result = objr.download(uuid, FileType.EXCEL)

    # Assert
    objr.get_environment_copy.assert_called_once()
    objr.temp_dir.assert_called_once()
    objr.run_download_process.assert_called_once()
    rdp_args = objr.run_download_process.call_args.kwargs
    env = rdp_args["env"]
    assert env["OBJR_USR"] == "test_user"
    assert env["OBJR_PWD"] == "test_pass"
    assert env["PATH"] == "mypath"
    assert len(env) == 3
    assert rdp_args["directory"] == "temp-dir"
    assert os.path.isfile(rdp_args["script_path"])
    objr.get_data_loader.assert_called_once_with(FileType.EXCEL)
    load_data.assert_called_once_with(os.path.join("temp-dir", "test.xlsx"))
    assert len(result) == 5
    assert len(dirs) == 0
