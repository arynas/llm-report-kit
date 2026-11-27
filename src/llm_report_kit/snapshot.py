"""Download and verify the frozen GDELT release used by the demo."""
import gzip
import hashlib
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import Request, urlopen

SNAPSHOT = "data-2026-10-v2"
SOURCE_URL = "https://www.gdeltproject.org/"
RELEASE = "https://github.com/arynas/Social-Listening-MCP/releases"
ASSETS = {
    "posts-2026-09.labelled.jsonl": (
        "5e4bd7781bea2b4fa55f34daa3fc69b7eaa36cf76dd0bb01aff998752c54f6a5",
        "aa901105550abadbd99668d521f5782a7739a56b45bdadabdd33156f9b00735f",
    ),
    "posts-2026-10.labelled.jsonl": (
        "d2dcc8e70efbaefe2893c1026a11c013369d16846739600abec31c194269303e",
        "eded825aad992856e2c734169b11db9aeb72342eb21d2901704287e2e6b09624",
    ),
}


def sha256(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def fetch_snapshot(data_dir):
    data_dir.mkdir(parents=True, exist_ok=True)
    for name, (archive_digest, data_digest) in ASSETS.items():
        destination = data_dir / name
        if destination.is_file() and sha256(destination) == data_digest:
            print(f"Verified existing {name}")
            continue
        with TemporaryDirectory(prefix=".download-", dir=data_dir) as staging:
            archive = Path(staging, name + ".gz")
            url = f"{RELEASE}/download/{SNAPSHOT}/{archive.name}"
            request = Request(url, headers={"User-Agent": "llm-report-kit/0.1.2"})
            with urlopen(request, timeout=60) as response, archive.open("wb") as output:
                shutil.copyfileobj(response, output)
            if sha256(archive) != archive_digest:
                raise ValueError(f"Download checksum mismatch for {archive.name}")
            unpacked = Path(staging, name)
            with gzip.open(archive, "rb") as source, unpacked.open("wb") as output:
                shutil.copyfileobj(source, output)
            if sha256(unpacked) != data_digest:
                raise ValueError(f"Unpacked checksum mismatch for {name}")
            unpacked.replace(destination)
        print(f"Downloaded and verified {name}")


def snapshot_paths(data_dir):
    paths = []
    for name, (_, data_digest) in ASSETS.items():
        path = (data_dir / name).resolve()
        if not path.is_file() or sha256(path) != data_digest:
            raise ValueError(f"Missing or invalid {name}. Run fetch-data with the same --data-dir.")
        paths.append(str(path))
    return tuple(paths)
