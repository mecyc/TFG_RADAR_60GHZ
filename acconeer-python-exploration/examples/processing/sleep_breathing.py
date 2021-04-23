import numpy as np
import pyqtgraph as pg
from scipy import signal

from acconeer.exptool import configs, utils
from acconeer.exptool.clients import SocketClient, SPIClient, UARTClient
from acconeer.exptool.pg_process import PGProccessDiedException, PGProcess


def main():
    args = utils.ExampleArgumentParser(num_sens=1).parse_args()
    utils.config_logging(args)

    if args.socket_addr:
        client = SocketClient(args.socket_addr)
    elif args.spi:
        client = SPIClient()
    else:
        port = args.serial_port or utils.autodetect_serial_port()
        client = UARTClient(port)

    sensor_config = get_sensor_config()
    sensor_config.sensor = args.sensors
    processing_config = get_processing_config()

    session_info = client.setup_session(sensor_config)

    pg_updater = PGUpdater(sensor_config, processing_config, session_info)
    pg_process = PGProcess(pg_updater)
    pg_process.start()

    client.start_session()

    interrupt_handler = utils.ExampleInterruptHandler()
    print("Press Ctrl-C to end session")

    processor = PresenceDetectionProcessor(sensor_config, processing_config, session_info)

    while not interrupt_handler.got_signal:
        info, sweep = client.get_next()
        plot_data = processor.process(sweep)

        if plot_data is not None:
            try:
                pg_process.put_data(plot_data)
            except PGProccessDiedException:
                break

    print("Disconnecting...")
    pg_process.close()
    client.disconnect()


def get_sensor_config():
    config = configs.IQServiceConfig()
    config.range_interval = [0.4, 0.8]
    config.update_rate = 60
    config.gain = 0.6
    return config


def get_processing_config():
    return {
        "n_dft": {
            "name": "Estimation window [s]",
            "value": 15,
            "limits": [2, 20],
            "type": float,
            "text": "s",
        },
        "t_freq_est": {
            "name": "Time between estimation [s]",
            "value": 0.2,
            "limits": [0.1, 10],
            "type": float,
            "text": "s",
        },
        "D": {
            "name": "Distance down sampling",
            "value": 124,
            "limits": [0, 248],
            "type": int,
            "text": None,
        },
        "f_high": {
            "name": "Bandpass high freq [Hz]",
            "value": 0.8,
            "limits": [0, 10],
            "type": float,
            "text": None,
        },
        "f_low": {
            "name": "Bandpass low freq [Hz]",
            "value": 0.2,
            "limits": [0, 10],
            "type": float,
            "text": None,
        },
        "lambda_p": {
            "name": "Threshold: Peak to noise ratio",
            "value": 40,
            "limits": [1, 1000],
            "type": float,
            "text": None,
        },
        "lambda_05": {
            "name": "Threshold: Peak to half harmonic ratio",
            "value": 1.0,
            "limits": [0, 10],
            "type": float,
            "text": None,
        },
    }


class PresenceDetectionProcessor:
    def __init__(self, sensor_config, processing_config, session_info):
        self.config = sensor_config

        # Settings
        # Data length for frequency estimation [s] | 20
        n_dft = processing_config["n_dft"]["value"]
        # Time between frequency estimations [s] | 2
        t_freq_est = processing_config["t_freq_est"]["value"]
        # Time constant low-pass filter on IQ-data [s] | 0.04
        tau_iq = 0.04
        # Time constant low-pass filter on IQ-data [s] | 150
        self.f_s = self.config.update_rate
        # Spatial or Range down sampling factor | 124
        self.D = int(processing_config["D"]["value"])
        # Lowest frequency of interest [Hz] | 0.1
        self.f_low = processing_config["f_low"]["value"]
        # Highest frequency of interest [Hz] | 1
        self.f_high = processing_config["f_high"]["value"]
        # Time down sampling for DFT | 40 f_s/M ~ 10 Hz
        self.M = int(self.f_s / 10)
        # Threshold: spectral peak to noise ratio [1] | 50
        self.lambda_p = processing_config["lambda_p"]["value"]
        # Threshold: ratio fundamental and half harmonic
        self.lambda_05 = processing_config["lambda_05"]["value"]
        # Interpolation between DFT points
        self.interpolate = True

        self.delta_f = 1 / n_dft
        self.dft_f_vec = np.arange(self.f_low, self.f_high, self.delta_f)
        self.dft_points = np.size(self.dft_f_vec)

        # Butterworth bandpass filter
        f_n = self.f_s / 2
        v_low = self.f_low / f_n
        v_high = self.f_high / f_n
        self.b, self.a = signal.butter(4, [v_low, v_high], btype="bandpass")

        # Exponential lowpass filter
        self.alpha_iq = np.exp(-2 / (self.f_s * tau_iq))
        self.alpha_phi = np.exp(-2 * self.f_low / self.f_s)

        # Parameter init
        self.sweeps_in_block = int(np.ceil(n_dft * self.f_s))
        self.new_sweeps_per_results = int(np.ceil(t_freq_est * self.f_s))
        self.phi_vec = np.zeros((self.sweeps_in_block, 1))
        self.f_est_vec = np.zeros(1)
        self.f_dft_est_vec = np.zeros(1)
        self.snr_vec = 0

        self.sweep_index = 0

    def process(self, sweep):
        if self.sweep_index == 0:
            delay_points = int(np.ceil(np.size(sweep) / self.D))
            self.data_s_d_mat = np.zeros((self.sweeps_in_block, delay_points), dtype="complex")
            self.data_s_d_mat[self.sweep_index, :] = self.downsample(sweep, self.D)

            out_data = None
        elif self.sweep_index < self.sweeps_in_block:
            self.data_s_d_mat[self.sweep_index, :] = self.iq_lp_filter_time(
                self.data_s_d_mat[self.sweep_index - 1, :],
                self.downsample(sweep, self.D)
            )

            temp_phi = self.unwrap_phase(
                self.phi_vec[self.sweep_index - 1],
                self.data_s_d_mat[self.sweep_index, :],
                self.data_s_d_mat[self.sweep_index - 1, :]
            )

            self.phi_vec[self.sweep_index] = self.unwrap_phase(
                self.phi_vec[self.sweep_index - 1],
                self.data_s_d_mat[self.sweep_index, :],
                self.data_s_d_mat[self.sweep_index - 1, :]
            )

            phi_filt = signal.lfilter(self.b, self.a, self.phi_vec, axis=0)

            out_data = {
                "phi_raw": self.phi_vec,
                "phi_filt": phi_filt,
                "power_spectrum": np.zeros(self.dft_points),
                "x_dft": np.linspace(self.f_low, self.f_high, self.dft_points),
                "f_dft_est_hist": self.f_dft_est_vec,
                "f_est_hist": self.f_est_vec,
                "f_dft_est": 0,
                "f_est": 0,
                "f_low": self.f_low,
                "f_high": self.f_high,
                "snr": 0,
                "lambda_p": self.lambda_p,
                "lambda_05": self.lambda_05,
                "dist_range": self.config.range_interval,
                "init_progress": round(100 * self.sweep_index / self.sweeps_in_block),
            }
        else:
            # Lowpass filter IQ data downsampled in distance points
            self.data_s_d_mat = np.roll(self.data_s_d_mat, -1, axis=0)
            self.data_s_d_mat[-1, :] = self.iq_lp_filter_time(
                self.data_s_d_mat[-2, :],
                self.downsample(sweep, self.D)
            )

            # Phase unwrapping of IQ data
            temp_phi = self.unwrap_phase(
                self.phi_vec[-1],
                self.data_s_d_mat[-1, :],
                self.data_s_d_mat[-2, :]
            )
            self.phi_vec = np.roll(self.phi_vec, -1, axis=0)
            self.phi_vec[-1] = temp_phi

            if np.mod(self.sweep_index, self.new_sweeps_per_results - 1) == 0:
                # Bandpass filter unwrapped data
                phi_filt_vec = signal.lfilter(self.b, self.a, self.phi_vec, axis=0)
                P, dft_est, _ = self.dft(self.downsample(phi_filt_vec, self.M))
                f_breath_est, _, snr, _ = self.breath_freq_est(P)

                self.f_est_vec = np.append(self.f_est_vec, f_breath_est)
                self.f_dft_est_vec = np.append(self.f_dft_est_vec, dft_est)
                self.snr_vec = np.append(self.snr_vec, snr)

                out_data = {
                    "phi_raw": self.phi_vec,
                    "phi_filt": phi_filt_vec,
                    "power_spectrum": P,
                    "x_dft": np.linspace(self.f_low, self.f_high, self.dft_points),
                    "f_dft_est_hist": self.f_dft_est_vec,
                    "f_est_hist": self.f_est_vec,
                    "f_dft_est": dft_est,
                    "f_est": f_breath_est,
                    "f_low": self.f_low,
                    "f_high": self.f_high,
                    "snr": snr,
                    "lambda_p": self.lambda_p,
                    "lambda_05": self.lambda_05,
                    "dist_range": self.config.range_interval,
                    "init_progress": None,
                }
            else:
                out_data = None

        self.sweep_index += 1
        return out_data

    def downsample(self, data, n):
        return data[:: n]

    def iq_lp_filter_time(self, state, new_data):
        return self.alpha_iq * state + (1 - self.alpha_iq) * new_data

    def unwrap_phase(self, phase_lp, data_1, data_2):
        return phase_lp * self.alpha_phi + np.angle(np.mean(data_2 * np.conjugate(data_1)))

    def dft(self, data):
        data = np.squeeze(data)
        n_vec = np.arange(data.size) * self.M
        dft = np.exp((2j * np.pi / self.f_s) * np.outer(self.dft_f_vec, n_vec))
        P = np.square(np.abs(np.matmul(dft, data)))
        idx_f = np.argmax(P)
        dft_est = self.dft_f_vec[idx_f]
        return P, dft_est, P[idx_f]

    def noise_est(self, P):
        return np.mean(np.sort(P)[: (self.dft_points // 2) - 1])

    def half_peak_frequency(self, P, f_est):
        idx_half = int(f_est / (2 * self.delta_f))
        if idx_half < self.f_low:
            return 0
        else:
            return (1 / self.delta_f) * (
                (self.dft_f_vec[idx_half + 1] - f_est / 2) * P[idx_half]
                + (f_est / 2 - self.dft_f_vec[idx_half]) * P[idx_half + 1]
            )

    def breath_freq_est(self, P):
        f_idx = np.argmax(P)
        P_peak = P[f_idx]

        if self.interpolate:
            f_est, P_peak = self.freq_quad_interpolation(P)
        else:
            f_est = self.dft_f_vec[f_idx]

        P_half = self.half_peak_frequency(P, f_est)

        if (P_peak < self.lambda_05 * P_half):
            f_est = f_est / 2
            P_peak = P_half

        if self.f_low < f_est < self.f_high and P_peak > self.lambda_p * self.noise_est(P):
            f_est_valid = True
        else:
            f_est_valid = False
            f_est = 0

        snr = P_peak / self.noise_est(P)
        return f_est, P_peak, snr, f_est_valid

    def freq_quad_interpolation(self, P):
        f_idx = np.argmax(P)

        if 0 < f_idx < P.size and P.size > 3:
            f_est = self.dft_f_vec[f_idx] + self.delta_f / 2 * (
                (np.log(P[f_idx + 1]) - np.log(P[f_idx - 1]))
                / (2 * np.log(P[f_idx]) - np.log(P[f_idx + 1]) - np.log(P[f_idx - 1]))
            )
            P_peak = P[f_idx] + np.exp(
                1 / 8 * np.square(np.log(P[f_idx + 1]) - np.log(P[f_idx - 1]))
                / (2 * np.log(P[f_idx]) - np.log(P[f_idx + 1]) - np.log(P[f_idx - 1]))
            )

            if not (self.f_low < f_est < self.f_high):
                f_est = 0
        else:
            f_est = 0
            P_peak = 0

        return f_est, P_peak


class PGUpdater:
    def __init__(self, sensor_config, processing_config, session_info):
        self.config = sensor_config

    def setup(self, win):
        win.resize(800, 600)
        win.setWindowTitle("Acconeer sleep breathing estimation example")

        phi_title = "Breathing motion (detection range: {} m to {} m)" \
                    .format(*self.config.range_interval)
        self.phi_plot = win.addPlot(title=phi_title)
        self.phi_plot.setMenuEnabled(False)
        self.phi_plot.setMouseEnabled(x=False, y=False)
        self.phi_plot.hideButtons()
        self.phi_plot.showGrid(x=True, y=True)
        self.phi_plot.setLabel("left", "Amplitude")
        self.phi_plot.setLabel("bottom", "Samples")
        self.phi_plot.addLegend()
        self.filt_phi_curve = self.phi_plot.plot(
            pen=utils.pg_pen_cycler(0),
            name="Filtered",
        )
        self.raw_phi_curve = self.phi_plot.plot(
            pen=utils.pg_pen_cycler(1),
            name="Raw",
        )

        win.nextRow()

        self.spect_plot = win.addPlot(title="Power spectrum")
        self.spect_plot.setMenuEnabled(False)
        self.spect_plot.setMouseEnabled(x=False, y=False)
        self.spect_plot.hideButtons()
        self.spect_plot.showGrid(x=True, y=True)
        self.spect_plot.setLabel("left", "Power")
        self.spect_plot.setLabel("bottom", "Frequency (Hz)")
        self.spect_curve = self.spect_plot.plot(pen=utils.pg_pen_cycler(1))
        self.spect_smax = utils.SmoothMax(self.config.update_rate / 15)
        self.spect_dft_inf_line = pg.InfiniteLine(pen=utils.pg_pen_cycler(1, "--"))
        self.spect_plot.addItem(self.spect_dft_inf_line)
        self.spect_est_inf_line = pg.InfiniteLine(pen=utils.pg_pen_cycler(0, "--"))
        self.spect_plot.addItem(self.spect_est_inf_line)
        self.spect_plot.setXRange(0, 1)
        self.spect_plot.setYRange(0, 1)
        self.spect_text_item = pg.TextItem("Initiating...", anchor=(0.5, 0.5), color="k")
        self.spect_text_item.setPos(0.5, 0.5)
        self.spect_plot.addItem(self.spect_text_item)

        win.nextRow()
        self.fest_plot = win.addPlot(title="Breathing estimation history")
        self.fest_plot.setMenuEnabled(False)
        self.fest_plot.setMouseEnabled(x=False, y=False)
        self.fest_plot.hideButtons()
        self.fest_plot.showGrid(x=True, y=True)
        self.fest_plot.setLabel("left", "Frequency (Hz)")
        self.fest_plot.setLabel("bottom", "Samples")
        self.fest_plot.addLegend()
        self.fest_curve = self.fest_plot.plot(
            pen=utils.pg_pen_cycler(0),
            name="Breathing est.",
        )
        self.fest_dft_curve = self.fest_plot.plot(
            pen=utils.pg_pen_cycler(1),
            name="DFT est.",
        )
        self.fest_plot.setXRange(0, 1)
        self.fest_plot.setYRange(0, 0.5)
        self.fest_text_item = pg.TextItem(anchor=(0, 0), color="k")
        self.fest_text_item.setPos(0, 0.5)
        self.fest_plot.addItem(self.fest_text_item)

    def update(self, data):
        self.filt_phi_curve.setData(np.squeeze(data["phi_filt"]))
        self.raw_phi_curve.setData(np.squeeze(data["phi_raw"]))

        if data["init_progress"] is not None:
            self.spect_text_item.setText("Initiating: {} %".format(data["init_progress"]))
        else:
            snr = data["snr"]
            if snr == 0:
                s = "SNR: N/A | {:.0f} dB".format(10 * np.log10(data["lambda_p"]))
            else:
                fmt = "SNR: {:.0f} | {:.0f} dB"
                s = fmt.format(10 * np.log10(snr), 10 * np.log10(data["lambda_p"]))
            self.spect_text_item.setText(s)
            self.spect_text_item.setAnchor((0, 1))
            self.spect_text_item.setPos(0, 0)

            f_est = data["f_est"]
            if f_est > 0:
                s = "Latest frequency estimate: {:.2f} Hz | {:.0f} BPM".format(f_est, f_est * 60)
                self.fest_text_item.setText(s)

            self.fest_plot.enableAutoRange(x=True)
            self.spect_curve.setData(data["x_dft"], data["power_spectrum"])
            self.spect_dft_inf_line.setValue(data["f_dft_est"])
            self.spect_est_inf_line.setValue(data["f_est"])
            self.spect_plot.setYRange(0, self.spect_smax.update(data["power_spectrum"]))
            self.fest_curve.setData(np.squeeze(data["f_est_hist"]))
            self.fest_dft_curve.setData(np.squeeze(data["f_dft_est_hist"]))


if __name__ == "__main__":
    main()
