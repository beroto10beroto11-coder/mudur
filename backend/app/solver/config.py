import os


class ConstraintPriority:
    HARD = 1_000_000
    IMPORTANT = 10_000
    NORMAL = 100
    SOFT = 1


class SolverConfig:
    MAX_TIME_IN_SECONDS: int = 300
    # Utilize maximum CPU logical cores for parallel portfolio search
    NUM_SEARCH_WORKERS: int = max(4, os.cpu_count() or 8)
    ENABLE_PROGRESS_LOGGING: bool = False
    LINEARIZATION_LEVEL: int = 2
