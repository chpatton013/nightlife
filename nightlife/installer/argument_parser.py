import argparse

from nightlife.config import config_file, state_file

SERVER_NAME_CHOICES = ["principal", "agent"]
DEFAULT_TEMPLATE_DIR = config_file("templates")
DEFAULT_STATE_DIR = state_file()


class ArgumentParser:
    def __init__(self):
        self.root = argparse.ArgumentParser()
        subparsers = self.root.add_subparsers(required=True)

        self.install = subparsers.add_parser("install")
        self.install.add_argument("--template-dir", default=DEFAULT_TEMPLATE_DIR)
        self.install.add_argument("--state-dir", default=DEFAULT_STATE_DIR)
        self.install.add_argument("--enable", action="store_true", default=False)
        install_subparsers = self.install.add_subparsers(required=True)

        self.enable = subparsers.add_parser("enable")
        enable_subparsers = self.enable.add_subparsers(required=True)

        self.disable = subparsers.add_parser("disable")
        disable_subparsers = self.disable.add_subparsers(required=True)

        self.uninstall = subparsers.add_parser("uninstall")
        self.uninstall.add_argument("--disable", action="store_true", default=False)
        uninstall_subparsers = self.uninstall.add_subparsers(required=True)

        self.install_server = install_subparsers.add_parser("server")
        self.install_server.add_argument("server_name", choices=SERVER_NAME_CHOICES)

        self.enable_server = enable_subparsers.add_parser("server")
        self.enable_server.add_argument("server_name", choices=SERVER_NAME_CHOICES)

        self.disable_server = disable_subparsers.add_parser("server")
        self.disable_server.add_argument("server_name", choices=SERVER_NAME_CHOICES)

        self.uninstall_server = uninstall_subparsers.add_parser("server")
        self.uninstall_server.add_argument("server_name", choices=SERVER_NAME_CHOICES)

        self.install_event = install_subparsers.add_parser("event")
        self.install_event.add_argument("event_name")
        self.install_event.add_argument("event_path")
        self.install_event.add_argument("--run-under", nargs="+", required=True)

        self.enable_event = enable_subparsers.add_parser("event")
        self.enable_event.add_argument("event_name")

        self.disable_event = disable_subparsers.add_parser("event")
        self.disable_event.add_argument("event_name")

        self.uninstall_event = uninstall_subparsers.add_parser("event")
        self.uninstall_event.add_argument("event_name")

        self.install_topic = install_subparsers.add_parser("topic")
        self.install_topic.add_argument("topic_name")
        self.install_topic.add_argument("topic_path")

        self.enable_topic = enable_subparsers.add_parser("topic")
        self.enable_topic.add_argument("topic_name")

        self.disable_topic = disable_subparsers.add_parser("topic")
        self.disable_topic.add_argument("topic_name")

        self.uninstall_topic = uninstall_subparsers.add_parser("topic")
        self.uninstall_topic.add_argument("topic_name")

        self.install_handler = install_subparsers.add_parser("handler")
        self.install_handler.add_argument("topic_name")
        self.install_handler.add_argument("handler_path", nargs="+")

        self.enable_handler = enable_subparsers.add_parser("handler")
        self.enable_handler.add_argument("topic_name")
        self.enable_handler.add_argument("handler_name", nargs="+")

        self.disable_handler = disable_subparsers.add_parser("handler")
        self.disable_handler.add_argument("topic_name")
        self.disable_handler.add_argument("handler_name", nargs="+")

        self.uninstall_handler = uninstall_subparsers.add_parser("handler")
        self.uninstall_handler.add_argument("topic_name")
        self.uninstall_handler.add_argument("handler_name", nargs="+")

    def parse_args(self, argv: list[str] | None = None) -> argparse.Namespace:
        return self.root.parse_args(argv)
