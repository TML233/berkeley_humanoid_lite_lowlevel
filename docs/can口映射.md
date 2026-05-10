# 问题：CAN口通信映射
## 描述
humanoid走路场景下（`src/robot/humanoid.py`）写死了can0左腿can1右腿。同理在bimanual手臂模式下也写死了can0can1对应左手右手。
机器人平常都是四个can口全连接，can口0123分配不固定。
## 解决方案
使用udev规则匹配can口设备序列号，固定成can_left_leg这类语义化名称，然后在humanoid.py源码里直接改成can_left_leg这种名字。
udev可以使用usb拓扑路径（可以理解为代表了usb插口位置），但是鉴于我们机器人使用了usb拓展坞，并且设备插口众多，只要扩展坞插在主机的不同位置，或者拓展坞上can口插了不同位置，usb拓扑路径都可能会变，因此选择使用can口的序列号来鉴别。

### 检查设备序列号
```bash
udevadm info -a -p /sys/class/net/can0 | grep -E 'KERNELS|SUBSYSTEMS|idVendor|idProduct|serial'
# can0改成1 2 3看其他三个can口
```
看`KERNELS=="1-2.1"`，`1-2.1`指的是usb1总线-主机第2个usb口-扩展坞的第1个口。
看下面的ATTRS{serial}找到序列号。四个can口板子如果同型号，idProduct和idVendor应该相同。
四个板子序列号不同就可以按照序列号来定。目前我们的4个板子

### 编写udev规则
保存在`/etc/udev/rules.d/100-can-names.rules`里，rules文件名字可以任意。
```
SUBSYSTEM=="net", ACTION=="add", ATTRS{serial}=="001C00304759530920353831", NAME="can_right_leg"
SUBSYSTEM=="net", ACTION=="add", ATTRS{serial}=="0030002A4759530A20353831", NAME="can_right_arm"
SUBSYSTEM=="net", ACTION=="add", ATTRS{serial}=="001D00274759530C20353831", NAME="can_left_leg"
SUBSYSTEM=="net", ACTION=="add", ATTRS{serial}=="004800214759530C20353831", NAME="can_left_arm"
```

usb设备连接电脑的那一刻，linux内核就会调用驱动，首先分配默认名称can0123，然后再调用udev流程做后处理。这也是为什么在udev规则里不把can口命名回代码里写的0123，因为可能重名，所以选择使用can_left_leg文字名称并改py代码。

### 修改脚本
udev把can口重命名后，start_can_transports.sh中也要改成对应的名字。
can口连接之后，电脑里就已经存在这些设备了，使用ip link show可以看见设备在down状态，需要使用`source start_can_transports.sh`手动up这些设备并且设置bitrate通信频率。

### 测试脚本
使用`uv run scripts/motor/ping_all.py`来测试can口是否ping通，以及各关节id是否在线。