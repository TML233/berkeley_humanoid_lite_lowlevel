# Copyright (c) 2025, The Berkeley Humanoid Lite Project Developers.

import argparse
import threading
import time
from typing import Dict, List

import berkeley_humanoid_lite_lowlevel.recoil as recoil


def parse_group(group_text: str):
    """
    Parse one CAN group.

    Example:
        can0:1,3,5,7
        can1:1,3,5,7,11,13
    """
    if ":" not in group_text:
        raise ValueError(
            f"Invalid group format: {group_text}. "
            "Expected format: can0:1,3,5,7"
        )

    channel, ids_text = group_text.split(":", 1)
    channel = channel.strip()

    if not channel:
        raise ValueError(f"Empty CAN channel in group: {group_text}")

    ids = []

    for item in ids_text.split(","):
        item = item.strip()
        if not item:
            continue
        ids.append(int(item))

    if not ids:
        raise ValueError(f"No motor IDs found in group: {group_text}")

    return channel, ids


def calibrate_one_channel(
    channel: str,
    motor_ids: List[int],
    bitrate: int,
    wait_seconds: float,
    per_id_delay: float,
    start_event: threading.Event,
    results: Dict[str, str],
):
    """
    Calibrate all motors on one CAN channel.
    Each CAN channel runs in its own thread.
    """
    bus = None

    try:
        print(f"[{channel}] Opening CAN bus, bitrate={bitrate} ...")
        bus = recoil.Bus(channel=channel, bitrate=bitrate)

        print(f"[{channel}] Ready. Motor IDs: {motor_ids}")

        # Wait until all CAN channels are ready.
        start_event.wait()

        print(f"[{channel}] Start CALIBRATION commands.")

        for device_id in motor_ids:
            print(f"[{channel}] Set motor {device_id} to CALIBRATION mode.")
            bus.set_mode(device_id, recoil.Mode.CALIBRATION)

            if per_id_delay > 0:
                time.sleep(per_id_delay)

        print(f"[{channel}] Waiting {wait_seconds} seconds for calibration...")
        time.sleep(wait_seconds)

        results[channel] = "OK"
        print(f"[{channel}] Calibration finished.")

    except Exception as exc:
        results[channel] = f"ERROR: {exc}"
        print(f"[{channel}] ERROR: {exc}")

    finally:
        if bus is not None:
            try:
                bus.stop()
                print(f"[{channel}] CAN bus stopped.")
            except Exception as exc:
                print(f"[{channel}] Failed to stop CAN bus: {exc}")


def main():
    parser = argparse.ArgumentParser(
        description="Calibrate electrical offset for motors on one or multiple CAN channels."
    )

    # New usage:
    #   --group can0:1,3,5,7 --group can1:1,3,5,7,11,13
    parser.add_argument(
        "-g",
        "--group",
        action="append",
        help=(
            "CAN group in format channel:id1,id2,id3. "
            "Example: --group can0:1,3,5,7"
        ),
    )

    # Compatible with old usage:
    #   -c can0 -i 1 -i 3
    parser.add_argument(
        "-c",
        "--channel",
        help="Single CAN channel, for example: can0",
    )

    parser.add_argument(
        "-i",
        "--id",
        action="append",
        type=int,
        help="Motor ID for single-channel mode. Can be used multiple times.",
    )

    parser.add_argument(
        "--bitrate",
        type=int,
        default=1000000,
        help="CAN bitrate. Default: 1000000.",
    )

    parser.add_argument(
        "--wait",
        type=float,
        default=20.0,
        help="Wait time after calibration starts. Default: 20 seconds.",
    )

    parser.add_argument(
        "--per-id-delay",
        type=float,
        default=0.0,
        help=(
            "Delay between sending calibration commands to motors on the same CAN channel. "
            "Default: 0.0 seconds."
        ),
    )

    args = parser.parse_args()

    groups: Dict[str, List[int]] = {}

    if args.group:
        for group_text in args.group:
            channel, ids = parse_group(group_text)

            if channel in groups:
                groups[channel].extend(ids)
            else:
                groups[channel] = ids

    elif args.channel and args.id:
        groups[args.channel] = args.id

    else:
        raise SystemExit(
            "No motors specified.\n\n"
            "Multi-CAN example:\n"
            "  uv run ./scripts/motor/calibrate_electrical_offset_multi.py "
            "--group can0:1,3,5,7 --group can1:1,3,5,7,11,13\n\n"
            "Single-CAN example:\n"
            "  uv run ./scripts/motor/calibrate_electrical_offset_multi.py "
            "-c can0 -i 1 -i 3"
        )

    print("======================================")
    print("Electrical Offset Calibration")
    print("Mode: MULTI-CAN PARALLEL")
    print("======================================")

    for channel, ids in groups.items():
        print(f"{channel}: {ids}")

    print("--------------------------------------")
    print(f"Bitrate      : {args.bitrate}")
    print(f"Wait seconds : {args.wait}")
    print(f"Per-ID delay : {args.per_id_delay}")
    print("======================================")

    start_event = threading.Event()
    results: Dict[str, str] = {}
    threads = []

    for channel, ids in groups.items():
        thread = threading.Thread(
            target=calibrate_one_channel,
            args=(
                channel,
                ids,
                args.bitrate,
                args.wait,
                args.per_id_delay,
                start_event,
                results,
            ),
            daemon=False,
        )
        threads.append(thread)
        thread.start()

    # Give every CAN thread a short time to open its bus.
    time.sleep(1.0)

    print("======================================")
    print("All CAN channels are starting calibration NOW.")
    print("======================================")

    start_event.set()

    for thread in threads:
        thread.join()

    print("======================================")
    print("Calibration Summary")
    print("======================================")

    has_error = False

    for channel, result in results.items():
        print(f"{channel}: {result}")
        if result != "OK":
            has_error = True

    if has_error:
        raise SystemExit(1)

    print("All requested CAN groups finished.")


if __name__ == "__main__":
    main()
