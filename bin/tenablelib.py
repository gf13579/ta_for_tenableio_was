import sys
import argparse
import os

import requests
from loguru import logger
from datetime import datetime
import time


class tenablelib:
    def __init__(self, api_key: str, earliest_date: str):
        self._api_key = api_key
        self.earliest_date = earliest_date

    def get_results(self, entities, queries):
        results = []
        return results


#################################################


def main() -> int:
    parser = argparse.ArgumentParser(description="Query tenable.io for WAS results")
    parser.add_argument("--api_key", nargs=1, required=True)
    parser.add_argument("--earliest_date", nargs=1, required=True)
    args = parser.parse_args()

    earliest_date = args.earliest_date[0]

    if "TENABLEIO_API_KEY" in os.environ:
        api_key = os.environ["TENABLEIO_API_KEY"]
    else:
        logger.error("Store API key in env var for testing: TENABLEIO_API_KEY")
        logger.error("e.g. export TENABLEIO_API_KEY=your_api_key_here")
        return 1

    tlib = tenablelib.dorklib(
        api_key=api_key,
    )

    results = tlib.get_results(earliest_date=earliest_date)

    print(results)


if __name__ == "__main__":
    sys.exit(main())
