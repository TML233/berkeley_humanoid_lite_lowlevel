from abc import ABC, abstractmethod
import onnxruntime as ort
import torch
import numpy as np

class Policy(ABC):
    """
    Abstract base class for all policies.
    """
    def __init__(self):
        pass

    @abstractmethod
    def forward(self, observations: np.ndarray) -> np.ndarray:
        pass


class TorchPolicy(Policy):
    """
    PyTorch policy inference runner.

    Loads and executes PyTorch models for robot control policies.
    """
    def __init__(self, checkpoint_path: str, device: str = "cpu"):
        self.device = device
        self.model: torch.nn.Module = torch.load(checkpoint_path, map_location=self.device)
        self.model.eval()

    def forward(self, observations: np.ndarray) -> np.ndarray:
        observations_tensor = torch.from_numpy(observations).unsqueeze(0).to(self.device)
        actions_tensor = self.model(observations_tensor)
        return actions_tensor.detach().cpu().squeeze(0).numpy()


class OnnxPolicy(Policy):
    """
    ONNX policy inference runner

    Loads and executes ONNX models for robot control policies.
    """
    def __init__(self, checkpoint_path: str):
        self.model: ort.InferenceSession = ort.InferenceSession(checkpoint_path)

        input_shape = self.model.get_inputs()[0].shape
        try:
            self.model.run(None, {"obs": np.zeros(input_shape, dtype=np.float32)})[0]
            self.key = "obs"
        except Exception as e:
            print(e)
            self.key = "onnx::Gemm_0"

    def forward(self, observations: np.ndarray) -> np.ndarray:
        return np.array(self.model.run(None, {self.key: observations})[0])