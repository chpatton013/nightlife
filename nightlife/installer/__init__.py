from nightlife.installer.config_installer import ConfigInstaller
from nightlife.installer.launchd_installer import LaunchdInstaller
from nightlife.installer.installer import Installer
from nightlife.installer.argument_parser import ArgumentParser


def install(installer: Installer, argv: list[str] | None = None) -> None:
    parser = installer.augment_parser(ArgumentParser())
    args = parser.parse_args(argv)
    args.action(args)


def install_launchd(argv: list[str] | None = None) -> None:
    installer = Installer(
        [
            ConfigInstaller(),
            LaunchdInstaller(),
        ]
    )
    install(installer, argv)
