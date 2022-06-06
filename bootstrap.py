from concurrent.futures import ProcessPoolExecutor
from logging import FileHandler, getLogger
from os import getenv
from pathlib import Path
from shutil import copy2
from subprocess import run

from dotenv import load_dotenv
from minio import Minio
from minio.datatypes import Object

ROOT_PATH = "/root/Arma3Server"
MINIO_BUCKET_NAME = "mtool"

logger = getLogger("bootstrap_logger")
handler = FileHandler(f"{ROOT_PATH}/bootstrap_logs.txt")

logger.setLevel("INFO")
logger.addHandler(handler)


def download_and_extract_modfile(object: Object):
    name: str = object.object_name
    temp_path = f"/tmp/mods/{name}"
    extract_path = Path(f"{ROOT_PATH}/mods/{name}").parent

    logger.info(f"Downloading '{name}'...")

    client.fget_object(MINIO_BUCKET_NAME, name, temp_path)

    logger.info(f"Extracting '{name}'...")

    # Create parent dir before extracting
    extract_path.mkdir(parents=True, exist_ok=True)

    run(
        [
            "7z",
            "x",
            temp_path,
            f"-o{extract_path}",
            "-pGk6pu2W4cPJ7V5CSYv4p",
            "-aoa",
        ]
    )

    if name.endswith(".bikey.7z"):
        copy2(f"{ROOT_PATH}/mods/{name[0:-3]}", f"{ROOT_PATH}/keys")


if __name__ == "__main__":
    # Loads /root/Arma3Server/.env
    load_dotenv()

    # Add passwords to config
    config_file = Path(f"{ROOT_PATH}/configs/server.cfg")
    config_text = config_file.read_text()

    config_file.write_text(
        config_text.replace(
            "SERVER_PASSWORD_REPLACE",
            getenv("ARMA_SERVER_PASSWORD"),
        ).replace(
            "SERVER_ADMIN_PASSWORD_REPLACE",
            getenv("ARMA_ADMIN_PASSWORD"),
        )
    )

    # Create keys folder
    Path(f"{ROOT_PATH}/keys").mkdir()

    # Get mods from minio
    client = Minio(
        "min.mcore.xyz",
        access_key=getenv("MINIO_ACCESS_KEY"),
        secret_key=getenv("MINIO_SECRET_KEY"),
        secure=False,
    )

    objects = client.list_objects(MINIO_BUCKET_NAME, "@", True)

    with ProcessPoolExecutor():
        for object in objects:
            download_and_extract_modfile(object)
