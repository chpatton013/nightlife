import argparse
import logging
import os

from nightlife.config import config_file
from nightlife.system import copy, symlink, unlink
from nightlife.installer.installer_interface import InstallerInterface


def _install_handlers(topic_name: str, handler_paths: list[str]) -> None:
    for handler_path in handler_paths:
        copy(handler_path, config_file("handlers", topic_name, os.path.basename(handler_path)))


def _enable_handlers(topic_name: str, handler_names: list[str]) -> None:
    for handler_name in handler_names:
        symlink(
            config_file("handlers", topic_name, handler_name),
            config_file("enabled/handlers", topic_name, handler_name),
        )


class ConfigInstaller(InstallerInterface):
    def install_event(self, args: argparse.Namespace) -> None:
        logging.debug("Running ConfigInstaller install hook for event %s with path %s", args.event_name, args.event_path)
        copy(args.event_path, config_file("events", args.event_name))

    def enable_event(self, args: argparse.Namespace) -> None:
        logging.debug("Running ConfigInstaller enable hook for event %s", args.event_name)
        symlink(
            config_file("events", args.event_name),
            config_file("enabled/events", args.event_name),
        )

    def disable_event(self, args: argparse.Namespace) -> None:
        logging.debug("Running ConfigInstaller disable hook for event %s", args.event_name)
        unlink(config_file("enabled/events", args.event_name))

    def uninstall_event(self, args: argparse.Namespace) -> None:
        logging.debug("Running ConfigInstaller uninstall hook for event %s", args.event_name)
        unlink(config_file("events", args.event_name))

    def install_topic(self, args: argparse.Namespace) -> None:
        logging.debug("Running ConfigInstaller install hook for topic %s with path %s", args.topic_name, args.topic_path)
        handlers = [os.path.abspath(os.path.join(args.topic_path, f)) for f in sorted(os.listdir(args.topic_path))]
        _install_handlers(args.topic_name, handlers)

    def enable_topic(self, args: argparse.Namespace) -> None:
        logging.debug("Running ConfigInstaller enable hook for topic %s", args.topic_name)
        handlers = sorted(os.listdir(config_file("handlers", args.topic_name)))
        _enable_handlers(args.topic_name, handlers)

    def disable_topic(self, args: argparse.Namespace) -> None:
        logging.debug("Running ConfigInstaller disable hook for topic %s", args.topic_name)
        unlink(config_file("enabled/handlers", args.topic_name))

    def uninstall_topic(self, args: argparse.Namespace) -> None:
        logging.debug("Running ConfigInstaller uninstall hook for topic %s", args.topic_name)
        unlink(config_file("handlers", args.topic_name))

    def install_handler(self, args: argparse.Namespace) -> None:
        logging.debug("Running ConfigInstaller install hook for topic %s with handlers %s", args.topic_name, str(args.handler_path))
        _install_handlers(args.topic_name, args.handler_path)

    def enable_handler(self, args: argparse.Namespace) -> None:
        logging.debug("Running ConfigInstaller enable hook for topic %s with handlers %s", args.topic_name, str(args.handler_name))
        _enable_handlers(args.topic_name, args.handler_name)

    def disable_handler(self, args: argparse.Namespace) -> None:
        logging.debug("Running ConfigInstaller disable hook for topic %s with handlers %s", args.topic_name, str(args.handler_name))
        for handler_name in args.handler_name:
            unlink(config_file("enabled/handlers", args.topic_name, handler_name))

    def uninstall_handler(self, args: argparse.Namespace) -> None:
        logging.debug("Running ConfigInstaller uninstall hook for topic %s with handlers %s", args.topic_name, str(args.handler_name))
        for handler_name in args.handler_name:
            unlink(config_file("handlers", args.topic_name, handler_name))
