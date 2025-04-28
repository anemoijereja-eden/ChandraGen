
from datetime import UTC, datetime

from apscheduler import job
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from chandragen.jobs.runners import run_converter_job
from chandragen.jobs.types import ConverterJob

#TODO: Add support for cron schedule to JobConfig type
#TODO: Add function that builds a registry of Jobs to run
#TODO: Add funtion that registers jobs
#TODO: Add an API endpoint that allows for job registration and triggering
#TODO: Allow modification of system config from api maybe?
JOB_REGISTRY: dict[str, tuple[job.Job, ConverterJob]] = {}
scheduler = BackgroundScheduler(
    executors = {
        "default": ThreadPoolExecutor(5) ,
    },
    job_defaults = {
    "coalesce": False,
    "max_instances": 1,
    }
)

if not scheduler.running:
    print("scheduler started")
    scheduler.start()
 
def run_converter_job_from_registry(jobname: str):
    try:
        job = JOB_REGISTRY[jobname][1]
    except KeyError:
        print(f'Error! config for job "{jobname}" missing from registry! {JOB_REGISTRY}')
        return
    run_converter_job(job)

def enter_joblist_to_scheduler(joblist: list[ConverterJob]):
    for config in joblist:
        print(f"registering {config.jobname} to scheduler")
        job = scheduler.add_job(
            run_converter_job_from_registry,
            CronTrigger.from_crontab(config.interval),
            next_run_time = datetime.now(UTC),
            args = [config.jobname]
        )
        JOB_REGISTRY[config.jobname] = (job, config)
    
__all__ = [
    "ConverterJob",
    "enter_joblist_to_scheduler",
    "scheduler",
]