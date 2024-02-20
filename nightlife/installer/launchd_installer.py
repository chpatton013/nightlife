import argparse
import logging
import os

# import subprocess
from dataclasses import dataclass

from nightlife.config import BIN_HOME, app_file
from nightlife.installer.argument_parser import ArgumentParser
from nightlife.installer.installer_interface import InstallerInterface
from nightlife.system import symlink

DEFAULT_SERVICE_DIR = os.path.join(os.path.expanduser("~"), "Library/LaunchAgents")
DOMAIN_TARGET = f"user/{os.getuid()}"


def _template_path(template_dir: str) -> str:
    return os.path.join(template_dir, "launchd/service.plist.in")


def _service_path(service_id: str, service_dir: str) -> str:
    return os.path.join(service_dir, f"{service_id}.plist")


def _service_target(service_id: str) -> str:
    return os.path.join(DOMAIN_TARGET, service_id)


def _server_id(server_name: str) -> str:
    return f"chpatton013.nightlife.server-{server_name}"


def _event_id(event_name: str) -> str:
    return f"chpatton013.nightlife.event-{event_name}"


def subprocess_run(cmd, check: bool = False) -> None:
    """
    TODO: Restore calls to subprocess.run after sorting out Falcon issues.
    """
    logging.info("DRYRUN:%s", " ".join(cmd))


LAUNCHD_SERVICE_TEMPLATE = _template_path(app_file("templates"))


@dataclass
class ServiceTemplate:
    template: str
    label: str
    log_dir: str
    program_arguments: list[str]

    def render(self) -> str:
        program_arguments = "\n         ".join(
            f"<string>{arg}</string>" for arg in self.program_arguments
        )
        rendered = self.template[:]
        rendered = rendered.replace("{{label}}", self.label)
        rendered = rendered.replace("{{log_dir}}", self.log_dir)
        rendered = rendered.replace("{{program_arguments}}", program_arguments)
        return rendered


@dataclass
class Service:
    service_id: str
    program_arguments: list[str]
    template_dir: str
    service_dir: str
    state_dir: str

    @property
    def template_path(self) -> str:
        return _template_path(self.template_dir)

    @property
    def service_path(self) -> str:
        return _service_path(self.service_id, self.service_dir)

    @property
    def service_target(self) -> str:
        return _service_target(self.service_id)

    def render(self, template: str) -> str:
        return ServiceTemplate(
            template=template,
            label=self.service_id,
            log_dir=os.path.join(self.state_dir, self.service_id),
            program_arguments=self.program_arguments,
        ).render()


def _install_service(service: Service) -> None:
    # TODO: Copy this file if DNE? (instead of symlink always)
    symlink(LAUNCHD_SERVICE_TEMPLATE, service.template_path)

    logging.debug("Reading service template from %s", service.template_path)
    with open(service.template_path, "r") as f:
        template = f.read()

    logging.debug("Rendering template")
    rendered = service.render(template)

    logging.debug("Writing rendered template to %s", service.service_path)
    with open(service.service_path, "w") as f:
        f.write(rendered)

    logging.debug("Loading service %s", service.service_path)
    subprocess_run(["launchctl", "load", "-w", service.service_path], check=True)


def _enable_service(service_id: str) -> None:
    service_target = _service_target(service_id)

    logging.debug("Starting service %s", service_target)
    subprocess_run(["launchctl", "start", service_target], check=True)

    logging.debug("Enabling service %s", service_target)
    subprocess_run(["launchctl", "enable", service_target], check=True)


def _disable_service(service_id: str) -> None:
    service_target = _service_target(service_id)

    logging.debug("Disabling service %s", service_target)
    subprocess_run(["launchctl", "disable", service_target], check=True)

    logging.debug("Stopping service %s", service_target)
    subprocess_run(["launchctl", "stop", service_target], check=True)


def _uninstall_service(service_id: str, service_dir: str) -> None:
    service_path = _service_path(service_id, service_dir)

    logging.debug("Unloading service %s", service_path)
    subprocess_run(["launchctl", "unload", "-w", service_path], check=True)

    logging.debug("Deleting service file %s", service_path)
    os.unlink(service_path)


class LaunchdInstaller(InstallerInterface):
    def augment_parser(self, parser: ArgumentParser) -> ArgumentParser:
        parser.root.add_argument("--service-dir", default=DEFAULT_SERVICE_DIR)
        parser.install_server.add_argument("--bin-dir", default=BIN_HOME)
        parser.install_event.add_argument("--bin-dir", default=BIN_HOME)
        return parser

    def install_server(self, args: argparse.Namespace) -> None:
        logging.debug(
            "Running LaunchdInstaller install hook for server %s", args.server_name
        )
        service = Service(
            service_id=_server_id(args.server_name),
            program_arguments=[
                os.path.join(args.bin_dir, f"nightlife-{args.server_name}")
            ],
            template_dir=args.template_dir,
            service_dir=args.service_dir,
            state_dir=args.state_dir,
        )
        _install_service(service)

    def enable_server(self, args: argparse.Namespace) -> None:
        logging.debug(
            "Running LaunchdInstaller enable hook for server %s", args.server_name
        )
        _enable_service(_server_id(args.server_name))

    def disable_server(self, args: argparse.Namespace) -> None:
        logging.debug(
            "Running LaunchdInstaller disable hook for server %s", args.server_name
        )
        _disable_service(_server_id(args.server_name))

    def uninstall_server(self, args: argparse.Namespace) -> None:
        logging.debug(
            "Running LaunchdInstaller uninstall hook for server %s", args.server_name
        )
        _uninstall_service(_server_id(args.server_name), args.service_dir)

    def install_event(self, args: argparse.Namespace) -> None:
        logging.debug(
            "Running LaunchdInstaller install hook for event %s", args.event_name
        )
        service = Service(
            service_id=_event_id(args.event_name),
            program_arguments=args.run_under
            + [
                os.path.join(args.bin_dir, "nightlife-notify"),
                args.event_name,
            ],
            template_dir=args.template_dir,
            service_dir=args.service_dir,
            state_dir=args.state_dir,
        )
        _install_service(service)

    def enable_event(self, args: argparse.Namespace) -> None:
        logging.debug(
            "Running LaunchdInstaller enable hook for event %s", args.event_name
        )
        _enable_service(_event_id(args.event_name))

    def disable_event(self, args: argparse.Namespace) -> None:
        logging.debug(
            "Running LaunchdInstaller disable hook for event %s", args.event_name
        )
        _disable_service(_event_id(args.event_name))

    def uninstall_event(self, args: argparse.Namespace) -> None:
        logging.debug(
            "Running LaunchdInstaller uninstall hook for event %s", args.event_name
        )
        _uninstall_service(_event_id(args.event_name), args.service_dir)
