"""Shared helper for the FRS scripts: fetch a JSON page from the EPA Envirofacts API, retrying on bad responses."""
import json
import logging
import time

import urllib3


def get_json(url, timeout=100, retries=5, wait=10):
    """GET url and return the parsed JSON.

    The Envirofacts service sometimes answers with an empty body or an HTML error page (timeouts, 5xx,
    rate limiting). Retry those with a growing pause, and raise if every attempt fails so that a state is
    never written from a partial download.
    """
    last_problem = None
    for attempt in range(1, retries + 1):
        try:
            resp = urllib3.request("GET", url, timeout=timeout)
            if resp.status == 200:
                return resp.json()
            last_problem = f"HTTP {resp.status}: {resp.data[:200]!r}"
        except (urllib3.exceptions.HTTPError, json.JSONDecodeError) as e:
            last_problem = f"{type(e).__name__}: {e}"
        logging.warning(f"Attempt {attempt}/{retries} failed for {url} ({last_problem})")
        print(f"attempt {attempt}/{retries} failed ({last_problem})")
        if attempt < retries:
            time.sleep(wait * attempt)
    logging.error(f"Giving up on {url} after {retries} attempts ({last_problem})")
    raise RuntimeError(f"Could not get valid JSON from {url} after {retries} attempts: {last_problem}")
