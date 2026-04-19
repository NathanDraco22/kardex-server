from typing import Any
import onnxruntime as ort
from onnxruntime import InferenceSession


class MLService:
    def load_onnx_model(self, model_path: str) -> InferenceSession:
        session = ort.InferenceSession(model_path)
        return session

    pass


class ProductClassifierService(MLService):
    _instance: "ProductClassifierService|None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls)
        return cls._instance

    _model_session: InferenceSession

    _initialized = False

    def __init__(self) -> None:
        if self._initialized:
            return
        model_path = "assets/ml_models/product_classifier.onnx"
        self._model_session = self.load_onnx_model(model_path)
        print("🤖 Product Classifier Model Loaded")

        self._initialized = True

    def process_batch(self, data: list[list]) -> Any:
        input_name = self._model_session.get_inputs()[0].name
        label_name = self._model_session.get_outputs()[0].name
        result = self._model_session.run(
            [label_name],
            {
                input_name: data,
            },
        )

        return result[0]
