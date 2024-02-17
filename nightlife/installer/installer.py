import argparse
import logging

from nightlife.installer.argument_parser import ArgumentParser
from nightlife.installer.installer_interface import InstallerInterface


class Installer(InstallerInterface):
    def __init__(self, subinstallers: list[InstallerInterface]):
        self.subinstallers = subinstallers

    def augment_parser(self, parser: ArgumentParser) -> ArgumentParser:
        for sub in self.subinstallers:
            parser = sub.augment_parser(parser)

        parser.install_server.set_defaults(action=self.install_server)
        parser.enable_server.set_defaults(action=self.enable_server)
        parser.disable_server.set_defaults(action=self.disable_server)
        parser.uninstall_server.set_defaults(action=self.uninstall_server)

        parser.install_event.set_defaults(action=self.install_event)
        parser.enable_event.set_defaults(action=self.enable_event)
        parser.disable_event.set_defaults(action=self.disable_event)
        parser.uninstall_event.set_defaults(action=self.uninstall_event)

        parser.install_topic.set_defaults(action=self.install_topic)
        parser.enable_topic.set_defaults(action=self.enable_topic)
        parser.disable_topic.set_defaults(action=self.disable_topic)
        parser.uninstall_topic.set_defaults(action=self.uninstall_topic)

        parser.install_handler.set_defaults(action=self.install_handler)
        parser.enable_handler.set_defaults(action=self.enable_handler)
        parser.disable_handler.set_defaults(action=self.disable_handler)
        parser.uninstall_handler.set_defaults(action=self.uninstall_handler)

        return parser

    def install_server(self, args: argparse.Namespace) -> None:
        logging.info("Installing server %s...", args.server_name)
        for sub in self.subinstallers:
            sub.install_server(args)
        logging.info("Installed server %s", args.server_name)

        if args.enable:
            self.enable_server(args)

    def enable_server(self, args: argparse.Namespace) -> None:
        logging.info("Enabling server %s...", args.server_name)
        for sub in self.subinstallers:
            sub.enable_server(args)
        logging.info("Enabled server %s", args.server_name)

    def disable_server(self, args: argparse.Namespace) -> None:
        logging.info("Disabling server %s...", args.server_name)
        for sub in self.subinstallers:
            sub.disable_server(args)
        logging.info("Disabled server %s", args.server_name)

    def uninstall_server(self, args: argparse.Namespace) -> None:
        if args.disable:
            self.disable_server(args)

        logging.info("Uninstalling server %s...", args.server_name)
        for sub in self.subinstallers:
            sub.uninstall_server(args)
        logging.info("Uninstalled server %s", args.server_name)

    def install_event(self, args: argparse.Namespace) -> None:
        logging.info("Installing event %s...", args.event_name)
        for sub in self.subinstallers:
            sub.install_event(args)
        logging.info("Installed event %s", args.event_name)

        if args.enable:
            self.enable_event(args)

    def enable_event(self, args: argparse.Namespace) -> None:
        logging.info("Enabling event %s...", args.event_name)
        for sub in self.subinstallers:
            sub.enable_event(args)
        logging.info("Enabled event %s", args.event_name)

    def disable_event(self, args: argparse.Namespace) -> None:
        logging.info("Disabling event %s...", args.event_name)
        for sub in self.subinstallers:
            sub.disable_event(args)
        logging.info("Disabled event %s", args.event_name)

    def uninstall_event(self, args: argparse.Namespace) -> None:
        if args.disable:
            self.disable_event(args)

        logging.info("Uninstalling event %s...", args.event_name)
        for sub in self.subinstallers:
            sub.uninstall_event(args)
        logging.info("Uninstalled event %s", args.event_name)

    def install_topic(self, args: argparse.Namespace) -> None:
        logging.info("Installing topic %s...", args.topic_name)
        for sub in self.subinstallers:
            sub.install_topic(args)
        logging.info("Installed topic %s", args.topic_name)

        if args.enable:
            self.enable_topic(args)

    def enable_topic(self, args: argparse.Namespace) -> None:
        logging.info("Enabling topic %s...", args.topic_name)
        for sub in self.subinstallers:
            sub.enable_topic(args)
        logging.info("Enabled topic %s", args.topic_name)

    def disable_topic(self, args: argparse.Namespace) -> None:
        logging.info("Disabling topic %s...", args.topic_name)
        for sub in self.subinstallers:
            sub.disable_topic(args)
        logging.info("Disabled topic %s", args.topic_name)

    def uninstall_topic(self, args: argparse.Namespace) -> None:
        if args.disable:
            self.disable_topic(args)

        logging.info("Uninstalling topic %s...", args.topic_name)
        for sub in self.subinstallers:
            sub.uninstall_topic(args)
        logging.info("Uninstalled topic %s", args.topic_name)

    def install_handler(self, args: argparse.Namespace) -> None:
        logging.info("Installing handler %s...", args.handler_name)
        for sub in self.subinstallers:
            sub.install_handler(args)
        logging.info("Installed handler %s", args.handler_name)

        if args.enable:
            self.enable_handler(args)

    def enable_handler(self, args: argparse.Namespace) -> None:
        logging.info("Enabling handler %s...", args.handler_name)
        for sub in self.subinstallers:
            sub.enable_handler(args)
        logging.info("Enabled handler %s", args.handler_name)

    def disable_handler(self, args: argparse.Namespace) -> None:
        logging.info("Disabling handler %s...", args.handler_name)
        for sub in self.subinstallers:
            sub.disable_handler(args)
        logging.info("Disabled handler %s", args.handler_name)

    def uninstall_handler(self, args: argparse.Namespace) -> None:
        if args.disable:
            self.disable_handler(args)

        logging.info("Uninstalling handler %s...", args.handler_name)
        for sub in self.subinstallers:
            sub.uninstall_handler(args)
        logging.info("Uninstalled handler %s", args.handler_name)
