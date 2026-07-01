class DataFrame:
    def __init__(
        self,
        device_id: int = 0,
        func_id: int | None = None,
        size: int = 0,
        data: bytes | bytearray = b""
    ):
        self.device_id = device_id
        self.func_id = func_id
        self.size = size
        self.data = data

        assert self.size == len(self.data)


class CANFrame(DataFrame):
    ID_STANDARD = 0
    ID_EXTENDED = 1

    DEVICE_ID_MSK = 0x7F
    FUNC_ID_POS = 7
    FUNC_ID_MSK = 0x0F << FUNC_ID_POS

    @staticmethod
    def build_arbitation_id(device_id:int,func_id:int)->int:
        return func_id << CANFrame.FUNC_ID_POS | device_id

    def __init__(
        self,
        device_id: int = 0,
        func_id: int | None = None,
        size: int = 0,
        data: bytes | bytearray = b""
    ):
        super().__init__(device_id, func_id, size, data)
        assert self.size <= 8
