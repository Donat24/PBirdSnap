import datetime
import os
import tempfile
from io import BufferedReader
from pathlib import Path
from typing import BinaryIO, Union
from uuid import UUID

import magic


class BadFileTypeError(Exception):
    pass


class UnknownImagePathError(Exception):
    pass


class StorageException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class Storage:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        if self.path.is_file():
            raise StorageException("path is a file")

    def setup(self) -> None:
        if not self.path.exists():
            os.mkdir(self.path)

    def save_birdsnapimage(
        self,
        device_id: UUID,
        file: Union[bytes, tempfile.SpooledTemporaryFile, BinaryIO],
        snap_time: datetime.datetime,
    ) -> str:

        # create dir
        file_path = self.path / str(device_id)
        if not os.path.exists(file_path):
            os.mkdir(file_path)

        # check filetype
        if isinstance(file, tempfile.SpooledTemporaryFile) or isinstance(
            file, BinaryIO
        ):
            buff = file.read(2024)
            file.seek(0)
        elif isinstance(file, bytes):
            buff = file

        filetype = magic.from_buffer(buff)
        filetype = filetype.split(" ")[0].lower()

        if filetype not in ["jpeg", "jpg", "png"]:
            raise BadFileTypeError()

        # compelte path
        file_path = file_path / (
            snap_time.strftime("%Y_%m_%d_%H_%M_%S") + "." + filetype
        )

        # write
        if isinstance(file, tempfile.SpooledTemporaryFile) or isinstance(
            file, BinaryIO
        ):
            file_path.write_bytes(file.read())
        else:
            file_path.write_bytes(file)

        return str(file_path.relative_to(self.path))

    def get_birdsnapimage(self, storage_path: str) -> Path:
        path = self.path / storage_path
        if not path.exists():
            raise UnknownImagePathError()
        return path
