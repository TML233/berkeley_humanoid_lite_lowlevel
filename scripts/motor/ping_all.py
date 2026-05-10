import berkeley_humanoid_lite_lowlevel.recoil as recoil
import argparse

PRESET_CHANNELS = {
    "@numbers": ["can0", "can1", "can2", "can3"],
    "@names": ["can_left_leg", "can_right_leg", "can_left_arm", "can_right_arm"],
}

IDS_LEFT_ARM=[1,3,5,7,9] 
IDS_RIGHT_ARM=[2,4,6,8,10] 
IDS_LEFT_LEG=[1,3,5,7,11,13] 
IDS_RIGHT_LEG=[2,4,6,8,12,14]

IDS_ALL = sorted(set()
    .union(IDS_LEFT_ARM)
    .union(IDS_RIGHT_ARM)
    .union(IDS_LEFT_LEG)
    .union(IDS_RIGHT_LEG)
)


def scan_channel(channel: str) -> set[int]:
    """扫描一个 CAN 口上能 ping 通的所有设备 ID。"""
    found = set()

    bus = recoil.Bus(channel=channel, bitrate=1_000_000)
    try:
        for device_id in IDS_ALL:
            try:
                ok = bus.ping(device_id)
            except Exception as e:
                print(f"[WARN] {channel} ping id={device_id} failed: {e}")
                ok = False

            if ok:
                found.add(device_id)
    finally:
        bus.stop()

    return found


def parse_channels() -> list[str]:
    parser = argparse.ArgumentParser(
        description="自动扫描并 Ping 指定 CAN 接口上的 ID"
    )
    parser.add_argument(
        "channels",
        nargs="*",
        default=["@names"],
        help="要扫描的 CAN 接口，可以使用 @numbers 或者 @names 预设",
    )
    args = parser.parse_args()

    channels: list[str] = []
    for item in args.channels:
        channels.extend(PRESET_CHANNELS.get(item, [item]))

    seen = set()
    deduped_channels = []
    for channel in channels:
        if channel not in seen:
            seen.add(channel)
            deduped_channels.append(channel)

    return deduped_channels


def main():
    channels = parse_channels()

    print("正在扫描 CAN 接口...\n")
    results: dict[str, set[int]] = {}
    for channel in channels:
        found = scan_channel(channel)
        results[channel] = found

        print(f"{channel} 上发现的 ID 有：{sorted(found)}")

    expected = {
        "左手": set(IDS_LEFT_ARM),
        "右手": set(IDS_RIGHT_ARM),
        "左腿": set(IDS_LEFT_LEG),
        "右腿": set(IDS_RIGHT_LEG),
    }

    print("\n==== 扫描结果 ====")

    for channel, found in results.items():
        matched_part = None

        for part, expected_ids in expected.items():
            if found == expected_ids:
                matched_part = part
                break

        if matched_part is not None:
            print(f"{channel} 是 {matched_part}")
        else:
            print(f"{channel} 无法匹配部位，扫描到的 ID 有：{sorted(found)}")


if __name__ == "__main__":
    main()
