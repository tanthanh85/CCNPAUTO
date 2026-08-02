from pathlib import Path

from pyats.easypy import run


def main(runtime):
    run(
        testscript=str(Path(__file__).with_name("switchport_health_test.py")),
        runtime=runtime,
        sample_interval=30,
        increase_threshold=0,
    )
