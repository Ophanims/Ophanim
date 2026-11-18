"""Export bounded native training metrics as a standalone figure."""
import csv
from collections import deque
from pathlib import Path
import numpy as np


def plot_training_report(directory):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    directory = Path(directory)
    with (directory / "training.csv").open() as stream:
        rows = deque(csv.DictReader(stream), maxlen=10000)
    if not rows:
        return
    steps = np.asarray([float(row["steps"]) for row in rows])
    figure, axes = plt.subplots(2, 2, figsize=(10, 7), constrained_layout=True)
    for axis, field, title in zip(axes.flat, ("mean_reward", "entropy", "policy_loss", "value_loss"),
                                   ("Reward", "Policy entropy", "Policy loss", "Value loss")):
        axis.plot(steps, [float(row[field]) for row in rows])
        axis.set_title(title)
        axis.set_xlabel("Training decisions")
        axis.grid(alpha=0.25)
    figure.savefig(directory / "ppo_training.png", dpi=150)
    plt.close(figure)
