from pathlib import Path

from pyats.easypy import run


def main(runtime):
    run(
        testscript=str(Path(__file__).with_name("crc_test.py")),
        runtime=runtime,
        sample_interval=30,
        crc_threshold=0,
    )
