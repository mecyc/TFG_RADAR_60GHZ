import numpy as np

from acconeer.exptool import configs, utils
from acconeer.exptool.clients import SocketClient, SPIClient, UARTClient
from acconeer.exptool.mpl_process import FigureUpdater, PlotProccessDiedException, PlotProcess


def main():
    args = utils.ExampleArgumentParser().parse_args()
    utils.config_logging(args)

    if args.socket_addr:
        client = SocketClient(args.socket_addr)
    elif args.spi:
        client = SPIClient()
    else:
        port = args.serial_port or utils.autodetect_serial_port()
        client = UARTClient(port)

    client.squeeze = False

    config = configs.IQServiceConfig()
    config.sensor = args.sensors
    config.update_rate = 60

    session_info = client.setup_session(config)
    depths = utils.get_range_depths(config, session_info)

    fig_updater = ExampleFigureUpdater(depths)
    plot_process = PlotProcess(fig_updater)
    plot_process.start()

    client.start_session()

    interrupt_handler = utils.ExampleInterruptHandler()
    print("Press Ctrl-C to end session")

    while not interrupt_handler.got_signal:
        info, data = client.get_next()

        plot_data = {
            "amplitude": np.abs(data),
            "phase": np.angle(data),
        }

        try:
            plot_process.put_data(plot_data)
        except PlotProccessDiedException:
            break

    print("Disconnecting...")
    plot_process.close()
    client.disconnect()


class ExampleFigureUpdater(FigureUpdater):
    def __init__(self, depths):
        self.depths = depths

    def setup(self, fig):
        self.axs = {
            "amplitude": fig.add_subplot(2, 1, 1),
            "phase": fig.add_subplot(2, 1, 2),
        }

        for ax in self.axs.values():
            ax.grid(True)
            ax.set_xlabel("Depth (m)")
            ax.set_xlim(self.depths[0], self.depths[-1])

        self.axs["amplitude"].set_title("Amplitude")
        self.axs["amplitude"].set_ylim(0, 5000)
        self.axs["phase"].set_title("Phase")
        utils.mpl_setup_yaxis_for_phase(self.axs["phase"])

        fig.canvas.set_window_title("Acconeer matplotlib process example")
        fig.set_size_inches(8, 6)
        fig.tight_layout()

    def first(self, d):
        xs = self.depths
        self.all_arts = {}
        for key, ax in self.axs.items():
            self.all_arts[key] = [ax.plot(xs, ys)[0] for ys in d[key]]
        return [art for arts in self.all_arts.values() for art in arts]

    def update(self, d):
        for key, arts in self.all_arts.items():
            for art, ys in zip(arts, d[key]):
                art.set_ydata(ys)


if __name__ == "__main__":
    main()
