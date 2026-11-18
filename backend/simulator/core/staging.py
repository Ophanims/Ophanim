"""Fork runtime state while sharing read-only ephemeris inputs and I/O handles."""
from copy import deepcopy


def fork_environment(environment):
    memo = {}

    def share(value):
        if value is not None:
            memo[id(value)] = value

    # SampleSeries and Skyfield calculators are read-only inputs (their bounded
    # memoization caches affect speed only); mutable entities/queues/RNGs copy.
    for name in ("input", "datetime_list", "logger"):
        share(getattr(environment, name, None))
    for entity in [*getattr(environment, "sat", []), *getattr(environment, "gs", []),
                   *getattr(environment, "roi", []), getattr(environment, "eth", None),
                   getattr(environment, "sun", None)]:
        if entity is not None:
            share(getattr(entity, "time_series", None))
    network = getattr(environment, "net", None)
    if network is not None:
        for name in ("sat_datas", "gs_datas", "times", "hardware"):
            share(getattr(network, name, None))
    return deepcopy(environment, memo)
