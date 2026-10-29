"""Run all state-level FRS triplification scripts in succession for one state.

Usage:
    python run_state.py ME
    python run_state.py ME RI VT      # several states, one after another
    python run_state.py               # prompts for the state abbreviation

Each script normally prompts for the state abbreviation; here it is supplied on stdin.
Output goes to the triples/ folder, and each script logs to ./log as usual.
"""
import subprocess
import sys
import time
from pathlib import Path

script_dir = Path(__file__).resolve().parent

scripts = [
    "facilities_api.py",                  # epa-frs-data-<ST>-facility-main-site.ttl
    "facilities_program_naics.py",        # epa-frs-data-<ST>-facility-naics.ttl
    "facilities_program_records.py",      # epa-frs-data-<ST>-program-record.ttl
    "facilities_program_supplemental.py", # epa-frs-data-<ST>-program-sup-record.ttl
    #"facilities_pat.py",                  # epa-frs-data-<ST>-pat.ttl
]


def run_state(state_code):
    print(f"===== {state_code} =====", flush=True)
    for script in scripts:
        print(f"--- {script} ({state_code})", flush=True)
        start = time.time()
        # cwd=script_dir so the relative "log" file lands next to the scripts, as when run by hand
        result = subprocess.run([sys.executable, script], input=f"{state_code}\n",
                                text=True, cwd=script_dir)
        if result.returncode != 0:
            print(f"!!! {script} failed for {state_code} (exit code {result.returncode}); stopping this state.",
                  flush=True)
            return False
        print(f"    done in {time.time() - start:.0f}s", flush=True)
    return True


def main():
    states = [s.strip().upper() for s in sys.argv[1:]] or [input("state abbreviation? ").strip().upper()]
    failed = [s for s in states if not run_state(s)]
    if failed:
        print(f"Failed states: {', '.join(failed)}")
        sys.exit(1)
    print("All done.")


if __name__ == "__main__":
    main()
