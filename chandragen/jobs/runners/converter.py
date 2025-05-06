from collections.abc import Iterable
from pathlib import Path
from threading import Lock, Thread

from chandragen import converter, system_config
from chandragen.formatters import FORMATTER_REGISTRY
from chandragen.jobs.runners import JobRunner, jobrunner
from chandragen.jobs.types import ConverterJob
from chandragen.types import ConverterConfig


@jobrunner("converter")
class ConverterJobRunner(JobRunner):
    
    def collect_files(self, path: Path, recursive: bool = False) -> Iterable[Path]:
        if recursive:
            return path.rglob("*.md*")
        return path.glob("*.md*")

    def run_config(self, config: ConverterConfig) -> bool:
        all_formatters = [*FORMATTER_REGISTRY.line, *FORMATTER_REGISTRY.multiline, *FORMATTER_REGISTRY.preprocessor]
        if system_config.debug_jobs:
            for i in config.enabled_formatters:
                if not all_formatters.__contains__(i):
                    print(f"Formatter not found: {i}")
    
        if converter.apply_formatting_to_file(config):
            print(f"Successfully converted file {config.input_path}!")
            return True
        print(f"Failed to convert {config.jobname}!")
        return False
       
 
    def run(self):
        job = ConverterJob(
            jobname = self.job_name,
            interval = self.config["interval"],
            is_dir = self.config["is_dir"] == "True",
            is_recursive = self.config["is_recursive"] == "true",
            input_path = Path(self.config["input_path"]),
            output_path = Path(self.config["output_path"]),
            
        )
        print(f"Running conversion job {job.jobname}")
        config_list: list[ConverterConfig] = []
        if job.is_dir:
            config_list += [
                ConverterConfig(
                    jobname = f"{job.jobname}({file})",
                    input_path = file,
                    enabled_formatters = job.enabled_formatters,
                    formatter_flags = job.formatter_flags,
                    preformatted_unicode_columns = job.preformatted_unicode_columns,
                    heading = job.heading,
                    heading_end_pattern = job.heading_end_pattern,
                    heading_strip_offset = job.heading_strip_offset,
                    footing = job.footing,
                    footing_start_pattern = job.footing_start_pattern,
                    footing_strip_offset = job.footing_strip_offset,
                    output_path = job.output_path / f"{file.stem}.gmi",
                ) for file in self.collect_files(job.input_path, job.is_recursive)
            ]
            success_count: int = 0
            failure_count: int = 0
            lock = Lock()
            threads: list[Thread] = []

            def worker(config: ConverterConfig):
                nonlocal success_count, failure_count
                if self.run_config(config):
                    with lock:
                        success_count += 1
                else:
                    with lock:
                        failure_count += 1

            for config in config_list:
                thread = Thread(target=worker, args=(config,))
                thread.start()
                threads.append(thread)
            
            for thread in threads:
                thread.join()

            print(f"✨ Done converting! {success_count} succeeded, {failure_count} failed.")
        else:
            config = ConverterConfig(
                    jobname = job.jobname,
                    input_path = job.input_path,
                    output_path = job.output_path,
                    enabled_formatters = job.enabled_formatters,
                    formatter_flags = job.formatter_flags,
                    preformatted_unicode_columns = job.preformatted_unicode_columns,
                    heading = job.heading,
                    heading_end_pattern = job.heading_end_pattern,
                    heading_strip_offset = job.heading_strip_offset,
                    footing = job.footing,
                    footing_start_pattern = job.footing_start_pattern,
                    footing_strip_offset = job.footing_strip_offset
            )
            print(f"Job {job.jobname} {"converted successfully" if self.run_config(config) else "failed to convert"}")
        
 