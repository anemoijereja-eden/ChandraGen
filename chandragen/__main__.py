import argparse
import tomllib
from pathlib import Path
from time import sleep

from chandragen import system_config
from chandragen.db import init_db
from chandragen.formatters import FORMATTER_REGISTRY
from chandragen.jobs import scheduler
from chandragen.jobs.runners.formatter import FormatterJob


def apply_blacklist(formatters: list[str] | str, blacklist: list[str] | str) -> list[str]:
    if isinstance(formatters, str):
        formatters = [formatters]
    if isinstance(blacklist, str):
        blacklist = [blacklist]
    return [f for f in formatters if f not in blacklist]

#Parse a config file and generate a joblist with configs to push to the file converter
def parse_config_file(toml_path: Path) -> list[FormatterJob]:
    with Path(toml_path).open("rb") as f:
        raw_config = tomllib.load(f)
    print(f"parsing config file {toml_path} and generating joblist")
    
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
                job_list.append(FormatterJob(
                    jobname=name,
                    interval = subentry.get("interval", default_interval),
                    is_dir=False,
                    is_recursive=False,
                    input_path=input_path,
                    output_path=output_path,
                    enabled_formatters = final_formatters,
                    formatter_flags = flags,
                    preformatted_unicode_columns=subentry.get("preformatted_text_columns", default_columns),
                    heading=subentry.get("heading"),
                    heading_end_pattern=subentry.get("heading_end_pattern"),
                    heading_strip_offset=subentry.get("heading_strip_offset", 0),
                    footing=subentry.get("footing"),
                    footing_start_pattern=subentry.get("footing_end_pattern"),
                    footing_strip_offset=subentry.get("footing_strip_offset", 0)
                            ))

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
                job_list.append(FormatterJob(
                        jobname = name,
                        interval = subentry.get("interval", default_interval),
                        is_dir = True,
                        is_recursive = recursive,
                        input_path = input_path,
                        output_path = output_path,
                        enabled_formatters = final_formatters,
                        formatter_flags = flags,
                        preformatted_unicode_columns=subentry.get("preformatted_text_columns", default_columns),
                        heading=subentry.get("heading"),
                        heading_end_pattern=subentry.get("heading_end_pattern"),
                        heading_strip_offset=subentry.get("heading_strip_offset", 0),
                        footing=subentry.get("footing"),
                        footing_start_pattern=subentry.get("footing_end_pattern"),
                        footing_strip_offset=subentry.get("footing_strip_offset", 0)
                        )   
                )
    return job_list

   
def run_config(args: argparse.Namespace):
    system_config.invoked_command = "run_config"
    system_config.config_path = args.config
    joblist = parse_config_file(args.config)
    scheduler.run_scheduler(joblist)

def list_formatters_command(args: argparse.Namespace):
    system_config.invoked_command = "list_formatters"
    print("   - - - Loaded formatters - - -")
    print("Line formatters:")
    for formatter_name in FORMATTER_REGISTRY.line:
        print(f" - {formatter_name}")
    print("Multi-line formatters:")
    for formatter_name in FORMATTER_REGISTRY.multiline:
        print(f" - {formatter_name}")
    print("Document Pre-Processors:")
    for formatter_name in FORMATTER_REGISTRY.preprocessor:
        print(f" - {formatter_name}")

def formatter_info_command(args: argparse.Namespace):
    system_config.invoked_command = "formatter_info"
    formatter = args.formatter
    if formatter in FORMATTER_REGISTRY.line:
        formatter_cls = FORMATTER_REGISTRY.line[formatter]
        print(f"""
Line-Formatter "{formatter}":
    
        -= Description =-
{formatter_cls.description}
Valid types: {formatter_cls.valid_types}
Origin: {formatter_cls.__module__}
""")
    if formatter in FORMATTER_REGISTRY.preprocessor:
        formatter_cls = FORMATTER_REGISTRY.preprocessor[formatter]
        print(f"""
Document Pre-Processor "{formatter}":
        
        -= Description =-
{formatter_cls.description}
Valid types: {formatter_cls.valid_types}
Origin: {formatter_cls.__module__}
""")
    if formatter in FORMATTER_REGISTRY.multiline:
        formatter_cls = FORMATTER_REGISTRY.multiline[formatter]
        print(f"""
Multi-Line Formatter "{formatter}":
    
       -= Description =-
{formatter_cls.description}
Valid types: {formatter_cls.valid_types}
Start Regex: {formatter_cls.start_pattern} 
End Regex: {formatter_cls.end_pattern}
Origin: {formatter_cls.__module__}
""")
def main():
    print("Starting ChandraGen CLI~ :3")
    init_db() # ensure database is properly set up on launch

    parser = argparse.ArgumentParser(description="ChandraGen Static Site Generator uwu~")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Subcommand: run-config
    run_parser = subparsers.add_parser("run-config", help="Run ChandraGen with a given config file.")
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
    args.func(args)  # calls the right function depending on the subcommand


if __name__ == "__main__":
    main()