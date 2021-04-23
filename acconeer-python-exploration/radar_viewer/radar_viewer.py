import multiprocessing
import sys
import threading
import time
import traceback
import webbrowser

from acconeer.exptool import clients, utils

from server import http_server


def check_connection(args):
    print("Checking connection to radar")
    try:
        if args.socket_addr:
            client = clients.SocketClient(args.socket_addr)
        elif args.spi:
            client = clients.SPIClient()
        else:
            port = args.serial_port or utils.autodetect_serial_port()
            client = clients.UARTClient(port)

        client.connect()
        client.disconnect()
        return True
    except Exception:
        print()
        traceback.print_exc()
        print()
        return False


def open_browser_delayed():
    time.sleep(5)  # TODO: Add proper synchronization so we can be sure that the server has started

    webbrowser.open_new_tab("http://127.0.0.1:5000")


def main():
    args = utils.ExampleArgumentParser(num_sens=1).parse_args()
    utils.config_logging(args)

    if not check_connection(args):
        print("Please check connection to radar sensor module or streaming server")
        sys.exit(1)

    print("Please wait for the radar viewer to open your web browser...\n\n")

    threading.Thread(target=open_browser_delayed, args=()).start()
    http_server.start_server(args)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
