"""
AGCP - Member 1: Telemetry Ingestion & Feature Engineering Pipeline
-------------------------------------------------------------------
Polls live CPU / memory / network / disk metrics from Prometheus,
stores them as raw history, and creates a cleaned training dataset.

Merged into Member 3's FastAPI application.
"""

import asyncio
import json
import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse


# ============================================================
# CONFIGURATION
# ============================================================

PROM_URL = os.getenv(
    "PROM_URL",
    "http://localhost:9090"
)

POLL_SECONDS = int(
    os.getenv("POLL_SECONDS", "15")
)

STEP_SEC = int(
    os.getenv("STEP_SEC", "15")
)

DATA_DIR = os.getenv(
    "DATA_DIR",
    "data"
)

RAW_CSV = os.path.join(
    DATA_DIR,
    "raw_telemetry.csv"
)

TRAIN_CSV = os.path.join(
    DATA_DIR,
    "training_dataset.csv"
)

os.makedirs(
    DATA_DIR,
    exist_ok=True
)


# ============================================================
# PROMETHEUS QUERIES
# ============================================================

QUERIES = {

    "cpu_util":
        '100 - (avg by (instance, job) '
        '(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)',

    "mem_util":
        '(1 - (node_memory_MemAvailable_bytes '
        '/ node_memory_MemTotal_bytes)) * 100',

    "net_rx_bps":
        'sum by (instance, job) '
        '(rate(node_network_receive_bytes_total{device!="lo"}[1m]))',

    "net_tx_bps":
        'sum by (instance, job) '
        '(rate(node_network_transmit_bytes_total{device!="lo"}[1m]))',

    "disk_io":
        'sum by (instance, job) '
        '(rate(node_disk_io_time_seconds_total[1m]))',

    "load1":
        'node_load1',
}


METRICS = list(
    QUERIES.keys()
)

RAW_COLS = [
    "timestamp",
    "instance",
    "job"
] + METRICS


# ============================================================
# LOGGING / STATE
# ============================================================

log = logging.getLogger(
    "telemetry"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)


_lock = threading.Lock()


STATE = {
    "latest": [],
    "last_poll": None,
    "polls": 0,
    "errors": 0,
    "last_error": None
}


# ============================================================
# LIVE TELEMETRY COLLECTION
# ============================================================

def poll_once() -> list[dict]:
    """
    Perform one Prometheus instant-query sweep.

    Returns one telemetry row per node.
    """

    ts = time.time()

    rows = {}

    for name, query in QUERIES.items():

        response = requests.get(
            f"{PROM_URL}/api/v1/query",
            params={
                "query": query,
                "time": ts
            },
            timeout=10
        )

        response.raise_for_status()

        results = response.json()["data"]["result"]

        for sample in results:

            key = (
                sample["metric"].get("instance"),
                sample["metric"].get("job")
            )

            row = rows.setdefault(
                key,
                {
                    "timestamp": pd.to_datetime(
                            ts,
                            unit="s",
                            utc=True
                        ).tz_convert(
                            ZoneInfo("Asia/Kolkata")
                        ).isoformat(),

                    "instance": key[0],

                    "job": key[1]
                }
            )

            value = float(
                sample["value"][1]
            )

            # Prometheus CPU query returns CPU utilization
            # as a fraction on this setup, while the ML model
            # expects percentage values.
            if name == "cpu_util":
                value *= 100

            row[name] = value

    return list(
        rows.values()
    )


# ============================================================
# SAVE RAW TELEMETRY
# ============================================================

def append_raw(rows: list[dict]) -> None:

    if not rows:
        return

    dataframe = (
        pd.DataFrame(rows)
        .reindex(columns=RAW_COLS)
    )

    with _lock:

        dataframe.to_csv(
            RAW_CSV,
            mode="a",
            header=not os.path.exists(RAW_CSV),
            index=False
        )


# ============================================================
# CONTINUOUS POLLING
# ============================================================

def poll_loop() -> None:

    while True:

        try:

            rows = poll_once()

            append_raw(rows)

            STATE.update(
                latest=rows,
                last_poll=time.time(),
                polls=STATE["polls"] + 1
            )

        except Exception as error:

            STATE.update(
                errors=STATE["errors"] + 1,
                last_error=str(error)
            )

            log.warning(
                "poll failed: %s",
                error
            )

        time.sleep(
            POLL_SECONDS
        )


def start_poller() -> None:

    threading.Thread(
        target=poll_loop,
        daemon=True
    ).start()


# ============================================================
# PROMETHEUS BACKFILL
# ============================================================

def backfill(hours: int) -> int:
    """
    Pull historical telemetry already stored in Prometheus.
    """

    end = time.time()

    start = (
        end -
        hours * 3600
    )

    frames = []

    for name, query in QUERIES.items():

        current_start = start

        while current_start < end:

            current_end = min(
                current_start + 6 * 3600,
                end
            )

            response = requests.get(
                f"{PROM_URL}/api/v1/query_range",
                timeout=60,
                params={
                    "query": query,
                    "start": current_start,
                    "end": current_end,
                    "step": STEP_SEC
                }
            )

            response.raise_for_status()

            results = response.json()["data"]["result"]

            for sample in results:

                dataframe = pd.DataFrame(
                    sample["values"],
                    columns=[
                        "ts",
                        "value"
                    ]
                )

                dataframe["metric"] = name

                dataframe["instance"] = (
                    sample["metric"].get("instance")
                )

                dataframe["job"] = (
                    sample["metric"].get("job")
                )

                frames.append(
                    dataframe
                )

            current_start = current_end

    if not frames:
        return 0

    long_dataframe = pd.concat(
        frames
    )

    long_dataframe["timestamp"] = pd.to_datetime(
    long_dataframe["ts"].astype(float),
    unit="s",
    utc=True
    ).dt.tz_convert(
        "Asia/Kolkata"
    )

    long_dataframe["value"] = (
        long_dataframe["value"].astype(float)
    )

    # IMPORTANT:
    # CPU values from Prometheus must use percentage scale
    # just like the live poller.
    cpu_mask = (
        long_dataframe["metric"] == "cpu_util"
    )

    long_dataframe.loc[
        cpu_mask,
        "value"
    ] *= 100

    wide_dataframe = (
        long_dataframe
        .pivot_table(
            index=[
                "timestamp",
                "instance",
                "job"
            ],
            columns="metric",
            values="value"
        )
        .reset_index()
        .reindex(columns=RAW_COLS)
    )

    wide_dataframe["timestamp"] = (
        wide_dataframe["timestamp"]
        .dt.strftime(
            "%Y-%m-%dT%H:%M:%S%z"
        )
    )

    with _lock:

        wide_dataframe.to_csv(
            RAW_CSV,
            mode="a",
            header=not os.path.exists(RAW_CSV),
            index=False
        )

    return len(
        wide_dataframe
    )


# ============================================================
# CLEANING + FEATURE ENGINEERING
# ============================================================

def build_training_dataset() -> pd.DataFrame:

    if not os.path.exists(RAW_CSV):

        raise FileNotFoundError(
            "No raw telemetry yet - "
            "run the poller or /pipeline/backfill first"
        )

    with _lock:

        raw = pd.read_csv(
            RAW_CSV
        )

    raw["timestamp"] = pd.to_datetime(
        raw["timestamp"],
        utc=True,
        format="ISO8601"
    )

    w5 = max(
        1,
        300 // STEP_SEC
    )

    w15 = max(
        1,
        900 // STEP_SEC
    )

    parts = []

    for (
        instance,
        job
    ), group in raw.groupby(
        ["instance", "job"]
    ):

        group = (
            group
            .drop_duplicates("timestamp")
            .set_index("timestamp")
            .sort_index()[METRICS]
            .resample(
                f"{STEP_SEC}s"
            )
            .mean()
        )

        group = (
            group
            .interpolate(limit=4)
            .ffill(limit=4)
        )

        group = group.dropna(
            subset=[
                "cpu_util",
                "mem_util"
            ]
        )

        group[
            ["cpu_util", "mem_util"]
        ] = group[
            ["cpu_util", "mem_util"]
        ].clip(
            0,
            100
        )

        group[
            ["net_rx_bps", "net_tx_bps", "disk_io"]
        ] = group[
            ["net_rx_bps", "net_tx_bps", "disk_io"]
        ].clip(
            lower=0
        )

        for column in (
            "cpu_util",
            "mem_util"
        ):

            group[
                f"{column}_mean_5m"
            ] = group[
                column
            ].rolling(
                w5,
                min_periods=1
            ).mean()

            group[
                f"{column}_std_5m"
            ] = group[
                column
            ].rolling(
                w5,
                min_periods=2
            ).std()

            group[
                f"{column}_mean_15m"
            ] = group[
                column
            ].rolling(
                w15,
                min_periods=1
            ).mean()

            group[
                f"{column}_lag_1"
            ] = group[
                column
            ].shift(1)

        hour_of_day = (
            group.index.hour +
            group.index.minute / 60
        )

        group["hour_sin"] = np.sin(
            2 * np.pi * hour_of_day / 24
        )

        group["hour_cos"] = np.cos(
            2 * np.pi * hour_of_day / 24
        )

        group["day_of_week"] = (
            group.index.dayofweek
        )

        group["instance"] = instance

        group["region"] = job

        parts.append(
            group.reset_index()
        )

    if not parts:

        raise ValueError(
            "Raw file has no usable rows"
        )

    dataset = (
        pd.concat(parts)
        .dropna()
        .sort_values(
            [
                "instance",
                "timestamp"
            ]
        )
    )

    dataset.to_csv(
        TRAIN_CSV,
        index=False
    )

    return dataset


# ============================================================
# FASTAPI ROUTER
# ============================================================

router = APIRouter()


@router.get("/health")
def health():

    return {
        "status": "ok",
        "prometheus": PROM_URL
    }


@router.get("/pipeline/status")
def status():

    raw_rows = (
        sum(
            1
            for _ in open(RAW_CSV)
        ) - 1
        if os.path.exists(RAW_CSV)
        else 0
    )

    return {
        **{
            key: value
            for key, value in STATE.items()
            if key != "latest"
        },

        "raw_rows": raw_rows,

        "poll_seconds": POLL_SECONDS
    }


@router.get("/telemetry/live")
def live():

    return {
        "timestamp": STATE["last_poll"],
        "nodes": STATE["latest"]
    }


@router.get("/telemetry/stream")
async def stream():

    async def generate():

        while True:

            yield (
                "data: "
                + json.dumps(
                    {
                        "timestamp": STATE["last_poll"],
                        "nodes": STATE["latest"]
                    }
                )
                + "\n\n"
            )

            await asyncio.sleep(
                POLL_SECONDS
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@router.post("/pipeline/backfill")
def run_backfill(
    hours: int = 24
):

    try:

        rows_added = backfill(
            hours
        )

        return {
            "rows_added": rows_added
        }

    except Exception as error:

        raise HTTPException(
            502,
            f"Prometheus backfill failed: {error}"
        )


@router.post("/pipeline/build-dataset")
def run_build():

    try:

        dataset = build_training_dataset()

    except Exception as error:

        raise HTTPException(
            400,
            str(error)
        )

    return {
        "rows": len(dataset),

        "columns": list(
            dataset.columns
        ),

        "nodes": dataset[
            "instance"
        ].nunique(),

        "from": str(
            dataset["timestamp"].min()
        ),

        "to": str(
            dataset["timestamp"].max()
        )
    }


@router.get("/dataset/download")
def download():

    if not os.path.exists(
        TRAIN_CSV
    ):

        raise HTTPException(
            404,
            "Dataset not built yet - "
            "POST /pipeline/build-dataset"
        )

    return FileResponse(
        TRAIN_CSV,
        filename="training_dataset.csv"
    )


# ============================================================
# FASTAPI LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(_: FastAPI):

    start_poller()

    yield


# ============================================================
# STANDALONE FASTAPI APP
# ============================================================

app = FastAPI(
    title="AGCP Telemetry Pipeline (Member 1)",
    lifespan=lifespan
)

app.include_router(
    router
)
