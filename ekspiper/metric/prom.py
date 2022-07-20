from prometheus_client import (
    CollectorRegistry,
    Gauge,
    Summary,
    push_to_gateway,
)
from timeit import default_timer


class ScriptExecutionMetrics:
    def __init__(self,
        prom_registry: CollectorRegistry,
        job_name: str,
    ):
        self.job_name = job_name
        self.start_gauge = Gauge(
            "rx_job_exec_start_time",
            "Start time of the RippleX executable job",
            ["job_name"],
            registry = prom_registry,
        )
        self.start_gauge.labels(job_name)

        self.end_gauge = Gauge(
            "rx_job_exec_end_time",
            "End time of the RippleX executable job",
            ["job_name"],
            registry = prom_registry,
        )
        self.end_gauge.labels(job_name)

        self.exec_duration_summary = Summary(
            "request_latency_seconds", 
            "Description of summary",
            ["job_name"],
            registry = prom_registry,
        )
        self.exec_duration_summary.labels(job_name)

        self.start_time = None
    
    async def __aenter__(self):
        self.__enter__()

    async def __aexit__(self, typ, value, traceback):
        self.__exit__(typ, value, traceback)

    def __enter__(self):
        self.start_gauge.labels(self.job_name).set_to_current_time()
        self.start_time = default_timer()
        return self

    def __exit__(self, typ, value, traceback):
        self.end_gauge.labels(self.job_name).set_to_current_time()

        # Time can go backwards.
        duration = max(default_timer() - self.start_time, 0)
        self.exec_duration_summary.labels(self.job_name).observe(duration)
        