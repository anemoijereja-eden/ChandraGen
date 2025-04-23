import argparse
import tomllib
from collections.abc import Iterable
from pathlib import Path

from chandragen import converter
from chandragen.formatters import FORMATTER_REGISTRY
from chandragen.types import JobConfig


def collect_files(path: Path, recursive: bool = False) -> Iterable[Path]:
    if recursive:
        return path.rglob("*.md*")
    return path.glob("*.md*")

def apply_blacklist(formatters: list[str] | str, blacklist: list[str] | str) -> list[str]:
    if isinstance(formatters, str):
        formatters = [formatters]
    if isinstance(blacklist, str):
        blacklist = [blacklist]
    return [f for f in formatters if f not in blacklist]

#Parse a config file and generate a joblist with configs to push to the file converter
def parse_config_file(toml_path: Path) -> list[JobConfig]:
    with Path(toml_path).open("rb") as f:
        raw_config = tomllib.load(f)
    print(f"parsing config file {toml_path} and generating joblist")
    defaults = raw_config.get("defaults", {})
    default_formatters = defaults.get("formatters", [])
    default_flags = {**defaults.get("formatter_flags", {})}
    default_outdir = Path(defaults.get("output_path"))
    default_columns = defaults.get("preformatted_text_columns", 80)
    
    job_list: list[JobConfig] = []
    
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
                job_list.append(JobConfig(
                    jobname = name,
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
                job_list += [ JobConfig(
                        jobname = name,
                        input_path = file,
                        output_path = output_path / f"{file.stem}.gmi",
                        enabled_formatters = final_formatters,
                        formatter_flags = flags,
                        preformatted_unicode_columns=subentry.get("preformatted_text_columns", default_columns),
                        heading=subentry.get("heading"),
                        heading_end_pattern=subentry.get("heading_end_pattern"),
                        heading_strip_offset=subentry.get("heading_strip_offset", 0),
                        footing=subentry.get("footing"),
                        footing_start_pattern=subentry.get("footing_end_pattern"),
                        footing_strip_offset=subentry.get("footing_strip_offset", 0)
                        ) for file in collect_files(input_path, recursive)    
                ]
    return job_list

# joblist runner
def run_joblist(joblist: list[JobConfig]):
    all_formatters = [*FORMATTER_REGISTRY.line, *FORMATTER_REGISTRY.multiline, *FORMATTER_REGISTRY.preprocessor]
    print("Running formatting jobs!")
    success_count: int = 0
    failure_count: int = 0
    for job in joblist:   
        if converter.apply_formatting_to_file(job):
            print(f"Successfully converted {job.jobname}!")
            success_count += 1
        else:
            print(f"Failed to convert {job.jobname}!")
            failure_count += 1
        for i in job.enabled_formatters:
            if not all_formatters.__contains__(i):
                print(f"Formatter not found: {i}")
    
    print(f"✨ Done converting! {success_count} succeeded, {failure_count} failed.")
    
def run_config(args: argparse.Namespace):
    joblist = parse_config_file(args.config)
    run_joblist(joblist)
    
def list_formatters_command(args: argparse.Namespace):
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