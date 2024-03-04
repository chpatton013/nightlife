import argparse

from nightlife.installer.argument_parser import ArgumentParser


class InstallerInterface:
    def augment_parser(self, parser: ArgumentParser) -> ArgumentParser:
        return parser

    def install_server(self, args: argparse.Namespace) -> None:
        pass

    def enable_server(self, args: argparse.Namespace) -> None:
        pass

    def disable_server(self, args: argparse.Namespace) -> None:
        pass

    def uninstall_server(self, args: argparse.Namespace) -> None:
        pass

    def install_event(self, args: argparse.Namespace) -> None:
        pass

    def enable_event(self, args: argparse.Namespace) -> None:
        pass

    def disable_event(self, args: argparse.Namespace) -> None:
        pass

    def uninstall_event(self, args: argparse.Namespace) -> None:
        pass

    def install_topic(self, args: argparse.Namespace) -> None:
        pass

    def enable_topic(self, args: argparse.Namespace) -> None:
        pass

    def disable_topic(self, args: argparse.Namespace) -> None:
        pass

    def uninstall_topic(self, args: argparse.Namespace) -> None:
        pass

    def install_handler(self, args: argparse.Namespace) -> None:
        pass

    def enable_handler(self, args: argparse.Namespace) -> None:
        pass

    def disable_handler(self, args: argparse.Namespace) -> None:
        pass

    def uninstall_handler(self, args: argparse.Namespace) -> None:
        pass
