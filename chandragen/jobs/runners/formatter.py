from collections.abc import Iterable
from pathlib import Path

from loguru import logger
from sqlmodel import false

from chandragen import system_config
from chandragen.db.models.job_queue import JobQueueEntry
from chandragen.formatters import FORMATTER_REGISTRY, apply_formatting_to_file
from chandragen.formatters.types import FormatterConfig
from chandragen.jobs import Job
from chandragen.jobs.runners import JobRunner, jobrunner


class FormatterJob(Job):
    @property
    def job_type(self) -> str:
        return "formatter"
    
    is_dir: bool
    is_recursive: bool
    input_path: Path
    output_path: Path
    formatter_flags: dict[str, bool | int | str]
    enabled_formatters: list[str] 
    heading: str | None                  = None
    heading_end_pattern: str | None      = None
    heading_strip_offset: int            = 0

    footing: str | None                  = None
    footing_start_pattern: str | None    = None
    footing_strip_offset: int            = 0

    preformatted_unicode_columns: int    = 80


@jobrunner("formatter")
class FormatterJobRunner(JobRunner[FormatterJob]):
    job_class = FormatterJob
    
    def collect_files(self, path: Path, recursive: bool = False) -> Iterable[Path]:
        if recursive:
            return path.rglob("*.md*")
        return path.glob("*.md*")

    def run_config(self, config: FormatterConfig) -> bool:
        all_formatters = [*FORMATTER_REGISTRY.line, *FORMATTER_REGISTRY.multiline, *FORMATTER_REGISTRY.preprocessor]
        if system_config.log_level == "DEBUG":
            for i in config.enabled_formatters:
                if not all_formatters.__contains__(i):
                    logger.warning(f"Formatter not found: {i}")
    
        if apply_formatting_to_file(config):
            logger.info(f"Successfully converted file {config.input_path}!")
            return True
        logger.error(f"Failed to convert {config.jobname}!")
        return False
       
 
    def run(self):
        job = self.job
        logger.info(f"Running formatting job {job.jobname} with strategy {"directory globbing" if job.is_dir else "single file"}")
        if job.is_dir:
            for file in self.collect_files(job.input_path, job.is_recursive):
                config = self.job
                config.input_path = file
                config.is_dir = False
                config.is_recursive = False
                config.output_path = self.job.output_path / f"{file.stem}.gmi"
                logger.debug(f"runner {str(self.job_id)[:4]} registering single-file job for path {file}")
                self.job_queue_db.add_job(
                    
                    JobQueueEntry(
                        name=f"{job.jobname}({file})",
                        job_type="formatter",
                        config_json=config.model_dump_json()
                    )
                )
        else:
            config = FormatterConfig(
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
            logger.info(f"Job {job.jobname} invoking formatter module!")
            if self.run_config(config):
                logger.info(f"Job {job.jobname} converted successfully")
                self.job_queue_db.mark_job_complete(self.job_id)
            else:
                logger.error(f"Job {job.jobname} failed to convert")
                self.job_queue_db.mark_job_failed(self.job_id)
                
    def setup(self):
        pass
    def cleanup(self) -> None:
        pass 
 