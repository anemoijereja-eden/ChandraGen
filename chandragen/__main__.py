from __future__ import annotations

import argparse
import sys
import time
import tomllib
from pathlib import Path

from loguru import logger

import chandragen
from chandragen import system_config
from chandragen.db import init_db
from chandragen.formatters import FORMATTER_REGISTRY
from chandragen.jobs import scheduler
from chandragen.jobs.pooler import ProcessPooler
from chandragen.jobs.runners.formatter import FormatterJob


class Parser(argparse.ArgumentParser):
    """
    A subclass of argparse.ArgumentParser to override the default
    output behavior to use loguru for printing messages.

    This modification ensures that all CLI messages are logged using
    loguru, maintaining a consistent and professional appearance in the
    terminal. This solution integrates the handling of regular
    messages with logging, instead of writing directly to stdout.
    """

    def _print_message(self, message: str, file: SupportsWrite[str] | None = None) -> None:
        logger.log("CLI", message)


def main():
    """Main entry point for the program, implements a cli via argparse."""
    set_up_logger()
    logger.log("CLI", "Starting ChandraGen CLI")
    init_db()  # ensure database is properly set up on launch

    parser = Parser(description="Chandragen Static Capsule Generation Framework")
    parser.add_argument("--shell", action="store_true", help="Launch interactive shell alongside the subcommand")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: run-pooler
    pool_parser = subparsers.add_parser("run-pooler", help="Run a ChandraGen worker process pool from the .env file")
    pool_parser.set_defaults(func=run_pooler)

    # Subcommand: run-config
    run_parser = subparsers.add_parser("run-config", help="Run ChandraGen tasks from a given config file.")
    run_parser.add_argument("config", help="Path to the config file.")
    run_parser.set_defaults(func=run_config)

    # Subcommand: list-formatters
    list_parser = subparsers.add_parser("list-formatters", help="List all available formatter modules.")
    list_parser.set_defaults(func=list_formatters_command)

    # Subcommand: formatter-info
    info_parser = subparsers.add_parser("formatter-info", help="Get information about a formatter")
    info_parser.add_argument("formatter", help="Name of a formatter")
    info_parser.set_defaults(func=formatter_info_command)

    args = parser.parse_args()

    # spawn the interactive debug shell if desired
    if args.shell:
        from chandragen.shell import InteractiveShellThread

        shell = InteractiveShellThread()
        shell.start()
    args.func(args)  # calls the right function depending on the subcommand


def set_up_logger():
    """Sets up Loguru. clears default handlers, registers the main custom handler, and adds the CLI log level."""
    # Clear any default handlers to avoid duplicate logs
    logger.remove()

    # Add custom handler (stdout)
    logger.add(
        sink=sys.stdout,
        level=system_config.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        backtrace=True,
        diagnose=True,
    )
    logger.level("CLI", no=255, color="<green>")


def apply_blacklist(formatters: list[str] | str, blacklist: list[str] | str) -> list[str]:
    """Helper function for the legacy TOML parser. uses a formatter whitelist and blacklist to generate a list of runnable formatters."""
    if isinstance(formatters, str):
        formatters = [formatters]
    if isinstance(blacklist, str):
        blacklist = [blacklist]
    return [f for f in formatters if f not in blacklist]


# Parse a config file and generate a joblist with configs to push to the file converter
def parse_config_file(toml_path: Path) -> list[FormatterJob]:
    """Legacy config parser system. takes a toml config and spits out formatting jobs."""
    with Path(toml_path).open("rb") as f:
        raw_config = tomllib.load(f)
    logger.info(f"parsing config file {toml_path} and generating joblist")

    # Parse out system options
    system = raw_config.get("system", {})
    system_config.scheduler_mode = system.get("scheduler_mode")

    # Parse out defaults
    defaults = raw_config.get("defaults", {})
    default_formatters = defaults.get("formatters", [])
    default_flags = {**defaults.get("formatter_flags", {})}
    default_outdir = Path(defaults.get("output_path"))
    default_columns = defaults.get("preformatted_text_columns", 80)
    default_interval = defaults.get("interval")
    job_list: list[FormatterJob] = []

    for section, entry in raw_config.items():
        if section == "defaults":
            continue

        if section == "file":
            for name, subentry in entry.items():
                input_path = Path(subentry.get("input_path"))
                output_path = Path(subentry.get("output_path", default_outdir / f"{name}.gmi"))
                formatters = default_formatters + subentry.get("formatters")
                blacklist = subentry.get("formatter_blacklist", [])
                final_formatters = apply_blacklist(formatters, blacklist)
                flags = {**default_flags, **subentry.get("formatter_flags", {})}
                job_list.append(
                    FormatterJob(
                        jobname=name,
                        interval=subentry.get("interval", default_interval),
                        is_dir=False,
                        is_recursive=False,
                        input_path=input_path,
                        output_path=output_path,
                        enabled_formatters=final_formatters,
                        formatter_flags=flags,
                        preformatted_unicode_columns=subentry.get("preformatted_text_columns", default_columns),
                        heading=subentry.get("heading"),
                        heading_end_pattern=subentry.get("heading_end_pattern"),
                        heading_strip_offset=subentry.get("heading_strip_offset", 0),
                        footing=subentry.get("footing"),
                        footing_start_pattern=subentry.get("footing_end_pattern"),
                        footing_strip_offset=subentry.get("footing_strip_offset", 0),
                    )
                )

        if section == "dir":
            for name, subentry in entry.items():
                input_path = Path(subentry.get("input_path"))
                output_path = Path(subentry.get("output_path", default_outdir / name))
                # Get the formatter lists, and combine them into one that has every specified formatter but removes blacklisted ones
                formatters = subentry.get("formatters", default_formatters)
                blacklist = subentry.get("formatter_blacklist", [])
                final_formatters = apply_blacklist(formatters, blacklist)
                flags = {**default_flags, **subentry.get("formatter_flags", {})}
                # Collect and batch all of the files suggested by the config entry
                recursive = subentry.get("recursive", False)
                job_list.append(
                    FormatterJob(
                        jobname=name,
                        interval=subentry.get("interval", default_interval),
                        is_dir=True,
                        is_recursive=recursive,
                        input_path=input_path,
                        output_path=output_path,
                        enabled_formatters=final_formatters,
                        formatter_flags=flags,
                        preformatted_unicode_columns=subentry.get("preformatted_text_columns", default_columns),
                        heading=subentry.get("heading"),
                        heading_end_pattern=subentry.get("heading_end_pattern"),
                        heading_strip_offset=subentry.get("heading_strip_offset", 0),
                        footing=subentry.get("footing"),
                        footing_start_pattern=subentry.get("footing_end_pattern"),
                        footing_strip_offset=subentry.get("footing_strip_offset", 0),
                    )
                )
    return job_list


def run_pooler(args: argparse.Namespace | None = None):
    """Starts a worker pool and then spins indefinitely. intended to be invoked from cli."""
    logger.log(
        "CLI",
        f"Starting dynamic pool of {system_config.minimum_workers_per_pool} to {system_config.max_workers_per_pool} worker processes ",
    )
    pooler = ProcessPooler()
    pooler.start()
    while True:
        time.sleep(10000)


def run_config(args: argparse.Namespace):
    """CLI command that uses the oneshot scheduler to run a set of Formatter jobs from a legacy TOML config"""
    updated_config = system_config
    updated_config.invoked_command = "run_config"
    updated_config.config_path = args.config
    chandragen.update_system_config(updated_config)
    joblist = parse_config_file(args.config)
    runner = scheduler.SchedulerRunner()
    runner.run(joblist)


# TODO: move the formatter system specific cli funcs into the formatter module, set up dynamic loader that adds cli subcommands from each internal module. maybe even plugin support here?
def list_formatters_command(args: argparse.Namespace):
    """CLI command that loads the formatter registry and then logs a cleanly formatted list"""
    updated_config = system_config
    updated_config.invoked_command = "list_formatters"
    chandragen.update_system_config(updated_config)
    logger.log(
        "CLI",
        f"""

        - - - Loaded formatters - - -
    
    Line formatters:
        {"        ".join(f" - {name}\n" for name in FORMATTER_REGISTRY.line)}
    Multi-line formatters:
        {"        ".join(f" - {name}\n" for name in FORMATTER_REGISTRY.multiline)}
    Document Pre-Processors:
        {"        ".join(f" - {name}\n" for name in FORMATTER_REGISTRY.preprocessor)}
    """,
    )


def formatter_info_command(args: argparse.Namespace):
    """CLI command that checks the formatter registry for the requested formatter and provides the in-class metadata for it"""
    updated_config = system_config
    updated_config.invoked_command = "formatter_info"
    chandragen.update_system_config(updated_config)
    formatter = args.formatter
    if formatter in FORMATTER_REGISTRY.line:
        formatter_cls = FORMATTER_REGISTRY.line[formatter]
        logger.log(
            "CLI",
            f"""
Line-Formatter "{formatter}":
    
        -= Description =-
{formatter_cls.description}
Valid types: {formatter_cls.valid_types}
Origin: {formatter_cls.__module__}
""",
        )
    if formatter in FORMATTER_REGISTRY.preprocessor:
        formatter_cls = FORMATTER_REGISTRY.preprocessor[formatter]
        logger.log(
            "CLI",
            f"""
Document Pre-Processor "{formatter}":
        
        -= Description =-
{formatter_cls.description}
Valid types: {formatter_cls.valid_types}
Origin: {formatter_cls.__module__}
""",
        )
    if formatter in FORMATTER_REGISTRY.multiline:
        formatter_cls = FORMATTER_REGISTRY.multiline[formatter]
        logger.log(
            "CLI",
            f"""
Multi-Line Formatter "{formatter}":
    
       -= Description =-
{formatter_cls.description}
Valid types: {formatter_cls.valid_types}
Start Regex: {formatter_cls.start_pattern} 
End Regex: {formatter_cls.end_pattern}
Origin: {formatter_cls.__module__}
""",
        )


# bootstrap nonsense
if __name__ == "__main__":
    main()
