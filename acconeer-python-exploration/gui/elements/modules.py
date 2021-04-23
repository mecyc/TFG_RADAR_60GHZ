from collections import namedtuple
from types import ModuleType

from acconeer.exptool.modes import Mode

import examples.processing.breathing as breathing_module
import examples.processing.button_press as button_press_module
import examples.processing.distance_detector as distance_detector_module
import examples.processing.obstacle_detection as obstacle_detection_module
import examples.processing.parking as parking_module
import examples.processing.phase_tracking as phase_tracking_module
import examples.processing.presence_detection_sparse as presence_detection_sparse_module
import examples.processing.sleep_breathing as sleep_breathing_module
import examples.processing.sparse_fft as sparse_fft_module
import examples.processing.sparse_inter_fft as sparse_inter_fft_module
import examples.processing.sparse_speed as sparse_speed_module
import service_modules.envelope as envelope_module
import service_modules.iq as iq_module
import service_modules.power_bins as power_bins_module
import service_modules.sparse as sparse_module
from helper import PassthroughProcessor


def multi_sensor_wrap(module):
    processor_cls = module.__dict__["Processor"]

    class WrappedProcessor:
        def __init__(self, sensor_config, processing_config, session_info):
            self.processors = []
            for _ in sensor_config.sensor:
                p = processor_cls(sensor_config, processing_config, session_info)
                self.processors.append(p)

        def update_processing_config(self, processing_config):
            if hasattr(processor_cls, "update_processing_config"):
                for p in self.processors:
                    p.update_processing_config(processing_config)

        def process(self, data):
            return [p.process(d) for p, d in zip(self.processors, data)]

    updater_cls = module.__dict__["PGUpdater"]

    class WrappedPGUpdater:
        def __init__(self, sensor_config, processing_config, session_info):
            self.updaters = []
            for _ in sensor_config.sensor:
                u = updater_cls(sensor_config, processing_config, session_info)
                self.updaters.append(u)

        def update_processing_config(self, processing_config):
            if hasattr(updater_cls, "update_processing_config"):
                for u in self.updaters:
                    u.update_processing_config(processing_config)

        def setup(self, win):
            for i, u in enumerate(self.updaters):
                sublayout = win.addLayout(row=0, col=i)
                u.setup(sublayout)

        def update(self, data):
            for u, d in zip(self.updaters, data):
                u.update(d)

    obj = ModuleType("wrapped_" + module.__name__.split(".")[-1])
    obj.__dict__["Processor"] = WrappedProcessor
    obj.__dict__["PGUpdater"] = WrappedPGUpdater
    for k, v in module.__dict__.items():
        if k not in obj.__dict__:
            obj.__dict__[k] = v

    return obj


multi_sensor_distance_detector_module = multi_sensor_wrap(distance_detector_module)
multi_sensor_parking_module = multi_sensor_wrap(parking_module)
multi_sensor_sparse_speed_module = multi_sensor_wrap(sparse_speed_module)
multi_sensor_presence_detection_sparse_module = multi_sensor_wrap(presence_detection_sparse_module)

ModuleInfo = namedtuple("ModuleInfo", [
    "key",
    "label",
    "module",
    "sensor_config_class",
    "processor",
    "multi_sensor",
    "allow_ml",
    "docs_url",
])

MODULE_INFOS = [
    ModuleInfo(
        None,
        "Select service or detector",
        None,
        None,
        None,
        True,
        True,
        "https://acconeer-python-exploration.readthedocs.io/en/latest/services/index.html",
    ),
    ModuleInfo(
        Mode.ENVELOPE.name.lower(),
        "Envelope",
        envelope_module,
        envelope_module.get_sensor_config,
        envelope_module.Processor,
        True,
        True,
        "https://acconeer-python-exploration.readthedocs.io/"
        "en/latest/services/envelope.html",
    ),
    ModuleInfo(
        Mode.IQ.name.lower(),
        "IQ",
        iq_module,
        iq_module.get_sensor_config,
        iq_module.Processor,
        True,
        True,
        "https://acconeer-python-exploration.readthedocs.io/"
        "en/latest/services/iq.html",
    ),
    ModuleInfo(
        Mode.POWER_BINS.name.lower(),
        "Power bins",
        power_bins_module,
        power_bins_module.get_sensor_config,
        PassthroughProcessor,
        False,
        False,
        "https://acconeer-python-exploration.readthedocs.io/"
        "en/latest/services/pb.html",
    ),
    ModuleInfo(
        Mode.SPARSE.name.lower(),
        "Sparse",
        sparse_module,
        sparse_module.get_sensor_config,
        sparse_module.Processor,
        True,
        True,
        "https://acconeer-python-exploration.readthedocs.io"
        "/en/latest/services/sparse.html",
    ),
    ModuleInfo(
        "sparse_presence",
        "Presence detection (sparse)",
        multi_sensor_presence_detection_sparse_module,
        multi_sensor_presence_detection_sparse_module.get_sensor_config,
        multi_sensor_presence_detection_sparse_module.Processor,
        True,
        False,
        "https://acconeer-python-exploration.readthedocs.io"
        "/en/latest/processing/presence_detection_sparse.html",
    ),
    ModuleInfo(
        "sparse_fft",
        "Sparse short-time FFT (sparse)",
        sparse_fft_module,
        sparse_fft_module.get_sensor_config,
        sparse_fft_module.Processor,
        False,
        False,
        None,
    ),
    ModuleInfo(
        "sparse_inter_fft",
        "Sparse long-time FFT (sparse)",
        sparse_inter_fft_module,
        sparse_inter_fft_module.get_sensor_config,
        sparse_inter_fft_module.Processor,
        False,
        False,
        None,
    ),
    ModuleInfo(
        "sparse_speed",
        "Speed (sparse)",
        multi_sensor_sparse_speed_module,
        multi_sensor_sparse_speed_module.get_sensor_config,
        multi_sensor_sparse_speed_module.Processor,
        True,
        False,
        None,
    ),
    ModuleInfo(
        "iq_breathing",
        "Breathing (IQ)",
        breathing_module,
        breathing_module.get_sensor_config,
        breathing_module.BreathingProcessor,
        False,
        False,
        None,
    ),
    ModuleInfo(
        "iq_phase_tracking",
        "Phase tracking (IQ)",
        phase_tracking_module,
        phase_tracking_module.get_sensor_config,
        phase_tracking_module.PhaseTrackingProcessor,
        False,
        False,
        "https://acconeer-python-exploration.readthedocs.io"
        "/en/latest/processing/phase_tracking.html",
    ),
    ModuleInfo(
        "iq_sleep_breathing",
        "Sleep breathing (IQ)",
        sleep_breathing_module,
        sleep_breathing_module.get_sensor_config,
        sleep_breathing_module.PresenceDetectionProcessor,
        False,
        False,
        "https://acconeer-python-exploration.readthedocs.io"
        "/en/latest/processing/sleep_breathing.html",
    ),
    ModuleInfo(
        "iq_obstacle",
        "Obstacle detection (IQ)",
        obstacle_detection_module,
        obstacle_detection_module.get_sensor_config,
        obstacle_detection_module.ObstacleDetectionProcessor,
        [1, 2],
        False,
        "https://acconeer-python-exploration.readthedocs.io"
        "/en/latest/processing/obstacle.html",
    ),
    ModuleInfo(
        "envelope_button_press",
        "Button Press (envelope)",
        button_press_module,
        button_press_module.get_sensor_config,
        button_press_module.ButtonPressProcessor,
        False,
        False,
        "https://acconeer-python-exploration.readthedocs.io/"
        "en/latest/processing/button_press.html",
    ),
    ModuleInfo(
        "envelope_distance",
        "Distance Detector (envelope)",
        multi_sensor_distance_detector_module,
        multi_sensor_distance_detector_module.get_sensor_config,
        multi_sensor_distance_detector_module.Processor,
        True,
        False,
        "https://acconeer-python-exploration.readthedocs.io/"
        "en/latest/processing/distance_detector.html",
    ),
    ModuleInfo(
        "envelope_parking",
        "Parking (envelope)",
        multi_sensor_parking_module,
        multi_sensor_parking_module.get_sensor_config,
        multi_sensor_parking_module.Processor,
        True,
        False,
        "https://acconeer-python-exploration.readthedocs.io/"
        "en/latest/processing/parking.html",
    ),
]

MODULE_KEY_TO_MODULE_INFO_MAP = {mi.key: mi for mi in MODULE_INFOS}
MODULE_LABEL_TO_MODULE_INFO_MAP = {mi.label: mi for mi in MODULE_INFOS}
