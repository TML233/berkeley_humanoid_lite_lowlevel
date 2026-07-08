from loop_rate_limiters import RateLimiter

import berkeley_humanoid_lite_lowlevel.recoil as recoil

def to_printable(v):
    if v is None:
        return "None"
    if v is float:
        return f"{v:.6f}"
    return str(v)
rate = RateLimiter(frequency=200.0)

args = recoil.util.get_args()
bus = recoil.Bus(channel=args.channel, bitrate=1000000)
device_id = args.id

try:
    while True:
        position_measured, position_offset  = bus.read_position_measured(device_id), bus.read_position_offset(device_id)
        print(f"{to_printable(position_measured)} - {to_printable(position_offset)}")
        
        rate.sleep()
except KeyboardInterrupt:
    pass

bus.stop()