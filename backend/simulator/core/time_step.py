"""One clock advance and geometry refresh at the committed timestamp."""
from datetime import timedelta
from simulator.core.model import GeometryAction, StepContext


def step_context(environment) -> StepContext:
    remaining = (environment.t_end - environment.time_recorder).total_seconds()
    dt_s = min(environment.slot_in_num, remaining)
    # Stop at a geometry-period boundary, including non-divisible slot sizes.
    boundary = environment.datetime_list[min(environment.period_counter + 1,
                                              environment.max_period_numbers - 1)]
    to_boundary = (boundary - environment.time_recorder).total_seconds()
    if to_boundary > 0:
        dt_s = min(dt_s, to_boundary)
    return StepContext(environment.time_recorder, dt_s, environment.frame_counter)


def advance_time(environment, context: StepContext) -> None:
    environment.time_recorder = min(context.time + timedelta(seconds=context.dt_s), environment.t_end)
    environment.frame_counter += 1
    elapsed_s = (environment.time_recorder - environment.t_start).total_seconds()
    period_s = environment.period.total_seconds()
    environment.period_counter = min(environment.frame_counter, environment.max_period_numbers - 1)
    environment.slot_counter = 0
    # Fractional sample indices calculate Skyfield geometry at the actual slot
    # timestamp, without preloading or changing algorithms' lookahead grid.
    sample_index = elapsed_s / period_s
    action = GeometryAction(sample_index, environment.slot_counter)
    for entity in [*environment.sat, *environment.gs, *environment.roi, environment.eth, environment.sun]:
        entity.transition(action, context)
    environment.net.transition(action, context)
    for satellite in environment.sat:
        satellite.connections = {link.dst: link for link in environment.net._all_links if link.src == satellite.id}
    environment.entity_collection.reset(environment.sat, [link for link in environment.net._all_links if link.type == "ISL"])
