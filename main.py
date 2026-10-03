import subprocess
import sys

from config import PROJECT_ROOT, SRC_DIR, validate_config


PIPELINE_STAGES = (
    ("Extract", SRC_DIR / "extract.py"),
    ("Transform", SRC_DIR / "transform..py"),
    ("Load", SRC_DIR / "load.py"),
)


def main():
    try:
        validate_config()
        for stage_name, script_path in PIPELINE_STAGES:
            print(f"\n{stage_name} >-------> ", flush=True, end='    ')
            subprocess.run(
                [sys.executable, str(script_path)],
                cwd=PROJECT_ROOT,
                check=True,
            )
    except (EnvironmentError, subprocess.CalledProcessError) as error:
        print(f"\nETL pipeline stopped: {error}", file=sys.stderr)
        return 1

    print("\nETL pipeline completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())