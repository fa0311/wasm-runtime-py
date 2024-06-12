import glob
import os
import pathlib
import subprocess

if __name__ == "__main__":
    filelist = glob.glob("testsuite/*.wast")
    for path in filelist:
        name = pathlib.Path(path).stem
        os.makedirs(f".cache/{name}", exist_ok=True)
        subprocess.run(
            ["wast2json", f"testsuite/{name}.wast", "-o", f".cache/{name}/{name}.json"],
        )
