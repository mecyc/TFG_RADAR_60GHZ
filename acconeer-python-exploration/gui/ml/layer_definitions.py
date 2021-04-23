import numpy as np
import tensorflow as tf


tf_version = tf.__version__.split(".")[0]
if tf.__version__.split(".")[0] == "1":
    from keras.layers import (
        LSTM,
        BatchNormalization,
        Conv1D,
        Conv2D,
        ConvLSTM2D,
        Dense,
        Dropout,
        Flatten,
        GaussianNoise,
        MaxPool2D,
    )
elif tf.__version__.split(".")[0] == "2":
    from tensorflow.keras.layers import (
        LSTM,
        BatchNormalization,
        Conv1D,
        Conv2D,
        ConvLSTM2D,
        Dense,
        Dropout,
        Flatten,
        GaussianNoise,
        MaxPool2D,
    )
else:
    raise ImportError("Unsupported TensorFlow version...")


activations = [
    "linear",
    "relu",
    "softmax",
    "exponential",
    "elu",
    "selu",
    "softplus",
    "softsign",
    "tanh",
    "sigmoid",
    "hard_sigmoid",
]


def get_layers():
    layers = {
        "conv1d": {
            "class_str": "Conv1D",
            "class": Conv1D,
            "dimensions": 1,
            "params": {
                "filters": [32, int, [0, np.inf]],
                "kernel_size": [8, int, [1, np.inf]],
                "padding": ["drop_down", ["same", "valid", "causal"]],
                "activation": ["drop_down", activations],
            },
        },
        "conv2d": {
            "class_str": "Conv2D",
            "class": Conv2D,
            "dimensions": 2,
            "params": {
                "filters": [32, int, [0, np.inf]],
                "kernel_size": [(2, 2), int, [1, np.inf]],
                "strides": [(1, 1), int, [0, np.inf]],
                "padding": ["drop_down", ["same", "valid"]],
                "activation": ["drop_down", activations],
            },
        },
        "gaussian_noise": {
            "class_str": "GaussianNoise",
            "class": GaussianNoise,
            "dimensions": 0,
            "params": {
                "stddev": [0.3, float, [0, 1]],
            },
        },
        "batch_normalization": {
            "class_str": "BatchNormalization",
            "class": BatchNormalization,
            "dimensions": 0,
            "params": None,
        },
        "flatten": {
            "class_str": "Flatten",
            "class": Flatten,
            "dimensions": 0,
            "params": None,
        },
        "max_pooling2d": {
            "class_str": "MaxPool2D",
            "class": MaxPool2D,
            "dimensions": 2,
            "params": {
                "pool_size": [(2, 2), int, [1, np.inf]],
            },
        },
        "dropout": {
            "class_str": "Dropout",
            "class": Dropout,
            "dimensions": 0,
            "params": {
                "rate": [0.2, float, [0, 1]],
            },
        },
        "dense": {
            "class_str": "Dense",
            "class": Dense,
            "dimensions": 0,
            "params": {
                "units": [0, int, [0, np.inf]],
                "activation": ["drop_down", activations],
            },
        },
        "convlstm2d": {
            "class_str": "ConvLSTM2D",
            "class": ConvLSTM2D,
            "dimensions": 0,
            "params": {
                "filters": [32, int, [0, np.inf]],
                "kernel_size": [8, int, [1, np.inf]],
                "padding": ["drop_down", ["same", "valid", "causal"]],
            },
        },
        "lstm": {
            "class_str": "LSTM",
            "class": LSTM,
            "dimensions": 0,
            "params": {
                "steps": [60, int, [0, np.inf]],
                "units": [32, int, [0, np.inf]],
                "activation": ["drop_down", activations],
                "recurrent_activation": ["drop_down", activations],
                "return_sequences": True,
            },
        },
    }

    # TODO: Finalize "Time series support"
    layers.pop("lstm")
    layers.pop("convlstm2d")

    return layers
