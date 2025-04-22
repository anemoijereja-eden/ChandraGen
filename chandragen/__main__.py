import chandragen.converter as converter
from pathlib import Path
import tomllib
import argparse
from typing import Iterable
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
    with open(toml_path, "rb") as f:
        raw_config = tomllib.load(f)
    
    defaults = raw_config.get("defaults", {})
    default_formatters = defaults.get("formatters", [])
    default_flags = {**defaults.get("formatter_flags", {})}
    default_outdir = Path(defaults.get("output_path"))
    print(str(default_outdir))
    default_columns = defaults.get("preformatted_text_columns", 80)
    
    job_list: list[JobConfig] = []
    
    for section, entry in raw_config.items():
        if section == "defaults":
            continue
        
        if section == "file":
            for name, subentry in entry.items():
                input_path = Path(subentry.get("input_path"))
                output_path = Path(subentry.get("output_path", default_outdir / f"{name}.gmi"))
                formatters = subentry.get("formatters", default_formatters)
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
                for file in collect_files(input_path, recursive):
                    job_list.append(JobConfig(
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
                    
                ))
    return job_list

# joblist runner
def run_joblist(joblist: list[JobConfig]):
    success_count: int = 0
    failure_count: int = 0
    for job in joblist:
        if converter.apply_formatting_to_file(job):
            print(f"Successfully converted {job.jobname}!")
            success_count += 1
        else:
            print(f"Failed to convert {job.jobname}!")
            failure_count += 1
    print(f"✨ Done converting! {success_count} succeeded, {failure_count} failed.")
    
def run_config(config_path: Path):
    joblist = parse_config_file(config_path)
    run_joblist(joblist)
    
def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Run ChandraGen with a given config.")
    parser.add_argument("config", help="Path to the config file.")
    args = parser.parse_args()
    run_config(args.config)

if __name__ == "__main__":
    main()