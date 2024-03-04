import argparse
import logging
import subprocess
import os
import plistlib
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


LAUNCHD_SERVICE_TEMPLATE = _template_path(app_file("templates"))


@dataclass
class SubprocessExecutor:
    execute: bool
    prefix: str

    def run(self, cmd: list[str]) -> None:
        if self.execute:
            subprocess.run(cmd, check=True)
        else:
            print(self.prefix, " ".join(cmd))


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


def _is_crowdstrike_falcon_running() -> bool:
    try:
        p = subprocess.run(
            ["/Applications/Falcon.app/Contents/Resources/falconctl", "info"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return False
    doc = plistlib.loads(p.stdout)
    return doc.get("sensor_loaded")


def _make_executor(args: argparse.Namespace) -> SubprocessExecutor:
    prefix = ">>>"
    should_execute = args.force
    reasons = []
    if not should_execute:
        if _is_crowdstrike_falcon_running():
            reasons.append(
                "CrowdStrike Falcon is running (Falcon will terminate the installer if it tries to install any launch agents)"
            )
            should_execute = False
    if not should_execute:
        message = "Nightlife's launchd installer will not execute launchd commands for the following reasons:"
        for index, reason in enumerate(reasons):
            message += "\n{:>2}) {}".format(str(index + 1), reason)
        message += f"\nYou can complete this installation by manually running these commands (lines will be prefixed with '{prefix}')"
        logging.warning(message)
    return SubprocessExecutor(execute=should_execute, prefix=prefix)


class LaunchdInstaller(InstallerInterface):
    def augment_parser(self, parser: ArgumentParser) -> ArgumentParser:
        parser.root.add_argument("--service-dir", default=DEFAULT_SERVICE_DIR)
        parser.root.add_argument("--force", action="store_true", default=False)
        parser.install_server.add_argument("--bin-dir", default=BIN_HOME)
        parser.install_event.add_argument("--bin-dir", default=BIN_HOME)
        return parser

    def install_server(self, args: argparse.Namespace) -> None:
        logging.debug(
            "Running LaunchdInstaller install hook for server %s", args.server_name
        )
        executor = _make_executor(args)
        service = Service(
            service_id=_server_id(args.server_name),
            program_arguments=[
                os.path.join(args.bin_dir, f"nightlife-{args.server_name}")
            ],
            template_dir=args.template_dir,
            service_dir=args.service_dir,
            state_dir=args.state_dir,
        )
        self._install_service(executor, service)

    def enable_server(self, args: argparse.Namespace) -> None:
        logging.debug(
            "Running LaunchdInstaller enable hook for server %s", args.server_name
        )
        executor = _make_executor(args)
        self._enable_service(executor, _server_id(args.server_name))

    def disable_server(self, args: argparse.Namespace) -> None:
        logging.debug(
            "Running LaunchdInstaller disable hook for server %s", args.server_name
        )
        executor = _make_executor(args)
        self._disable_service(executor, _server_id(args.server_name))

    def uninstall_server(self, args: argparse.Namespace) -> None:
        logging.debug(
            "Running LaunchdInstaller uninstall hook for server %s", args.server_name
        )
        executor = _make_executor(args)
        self._uninstall_service(
            executor, _server_id(args.server_name), args.service_dir
        )

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
        executor = _make_executor(args)
        self._install_service(executor, service)

    def enable_event(self, args: argparse.Namespace) -> None:
        logging.debug(
            "Running LaunchdInstaller enable hook for event %s", args.event_name
        )
        executor = _make_executor(args)
        self._enable_service(executor, _event_id(args.event_name))

    def disable_event(self, args: argparse.Namespace) -> None:
        logging.debug(
            "Running LaunchdInstaller disable hook for event %s", args.event_name
        )
        executor = _make_executor(args)
        self._disable_service(executor, _event_id(args.event_name))

    def uninstall_event(self, args: argparse.Namespace) -> None:
        logging.debug(
            "Running LaunchdInstaller uninstall hook for event %s", args.event_name
        )
        executor = _make_executor(args)
        self._uninstall_service(executor, _event_id(args.event_name), args.service_dir)

    def _install_service(self, executor: SubprocessExecutor, service: Service) -> None:
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
        executor.run(["launchctl", "load", "-w", service.service_path])

    def _enable_service(self, executor: SubprocessExecutor, service_id: str) -> None:
        service_target = _service_target(service_id)

        logging.debug("Starting service %s", service_target)
        executor.run(["launchctl", "start", service_target])

        logging.debug("Enabling service %s", service_target)
        executor.run(["launchctl", "enable", service_target])

    def _disable_service(self, executor: SubprocessExecutor, service_id: str) -> None:
        service_target = _service_target(service_id)

        logging.debug("Disabling service %s", service_target)
        executor.run(["launchctl", "disable", service_target])

        logging.debug("Stopping service %s", service_target)
        executor.run(["launchctl", "stop", service_target])

    def _uninstall_service(
        self, executor: SubprocessExecutor, service_id: str, service_dir: str
    ) -> None:
        service_path = _service_path(service_id, service_dir)

        logging.debug("Unloading service %s", service_path)
        executor.run(["launchctl", "unload", "-w", service_path])

        logging.debug("Deleting service file %s", service_path)
        os.unlink(service_path)
