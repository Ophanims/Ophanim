import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def _plot_combined_curve(callback: TrainingMetricsCallback, out_dir: str) -> None:
    """Plot reward (EMA) and policy entropy on the same X-axis (training steps).

    - Left Y axis: Average Reward (EMA, red line)
    - Right Y axis: Policy Entropy (blue line)
    - X axis: Training Steps
    """

    # Need at least some entropy data
    if not callback.entropy_steps or not callback.entropy_values:
        return

    # 1) Load reward & episode length from Monitor logs to map episodes -> steps
    log_dir = LOG_DIR
    if not os.path.isdir(log_dir):
        return

    files = [
        os.path.join(log_dir, f)
        for f in os.listdir(log_dir)
        if f.endswith(".monitor.csv")
    ]
    if not files:
        return

    dfs = []
    for path in files:
        try:
            df = pd.read_csv(path, comment="#")
            dfs.append(df)
        except Exception:
            continue
    if not dfs:
        return

    df_all = pd.concat(dfs, ignore_index=True)
    if "r" not in df_all.columns:
        return

    # 1) Reward vs. episode steps from Monitor logs
    #    Prefer built-in 't' (cumulative steps), otherwise use cumsum of 'l'.
    if "t" in df_all.columns:
        steps_episode = df_all["t"].to_numpy()
    elif "l" in df_all.columns:
        steps_episode = df_all["l"].cumsum().to_numpy()
    else:
        # Fallback: use episode index if no step info is available
        steps_episode = np.arange(1, len(df_all) + 1, dtype=float)

    # Smooth reward with EMA on the episode axis
    reward_ema = df_all["r"].ewm(alpha=0.1).mean().to_numpy()

    # 2) Entropy data from callback (per training step).
    #    We will use this as the common Training Steps axis, and
    #    interpolate the EMA reward onto it so that the X range
    #    matches the standalone entropy plot (e.g. up to 50k steps).
    x_entropy = np.asarray(callback.entropy_steps, dtype=float)
    y_entropy = np.asarray(callback.entropy_values, dtype=float)

    if x_entropy.size == 0 or y_entropy.size == 0:
        return

    # ensure entropy steps are strictly increasing
    order = np.argsort(x_entropy)
    x_entropy = x_entropy[order]
    y_entropy = y_entropy[order]

    # guard against NaNs in reward/step data
    mask_valid = np.isfinite(steps_episode) & np.isfinite(reward_ema)
    if mask_valid.sum() < 2:
        return
    steps_episode_valid = steps_episode[mask_valid].astype(float)
    reward_ema_valid = reward_ema[mask_valid].astype(float)

    # interpolate EMA reward onto the entropy step axis
    reward_on_entropy_steps = np.interp(x_entropy, steps_episode_valid, reward_ema_valid)

    # --- Plot on common Training Steps axis (x_entropy) ---
    os.makedirs(out_dir, exist_ok=True)
    plt.rcParams["font.family"] = "Times New Roman"

    fig, ax1 = plt.subplots(figsize=(8, 4))

    # Left axis: Reward (red)
    color_reward = "tab:red"
    ax1.set_xlabel("Training Steps")
    ax1.set_ylabel("Average Reward (EMA)", color=color_reward)
    l1, = ax1.plot(
        x_entropy,
        reward_on_entropy_steps,
        color=color_reward,
        linewidth=2.0,
        label="EMA Reward",
    )
    ax1.tick_params(axis="y", labelcolor=color_reward)
    ax1.grid(True, linestyle="--", alpha=0.35)

    # Right axis: Entropy (blue)
    ax2 = ax1.twinx()
    color_entropy = "tab:blue"
    ax2.set_ylabel("Policy Entropy", color=color_entropy)
    l2, = ax2.plot(
        x_entropy,
        y_entropy,
        color=color_entropy,
        linewidth=1.8,
        linestyle="-",
        label="Entropy",
    )
    ax2.tick_params(axis="y", labelcolor=color_entropy)

    # Style & legend
    ax1.set_title("Reward & Policy Entropy vs Training Steps")
    ax1.set_facecolor("#fbfbfb")
    fig.tight_layout()

    lines = [l1, l2]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="upper left", fontsize=8, framealpha=0.9)

    out_path = os.path.join(out_dir, "ppo_reward_entropy_combined.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _plot_policy_entropy(callback: TrainingMetricsCallback, out_dir: str) -> None:
    """Policy entropy curve: Steps vs. empirical action entropy.

    Styling: Times New Roman + soft pastel rainbow tone.
    """

    if not callback.entropy_steps:
        return

    os.makedirs(out_dir, exist_ok=True)
    plt.rcParams["font.family"] = "Times New Roman"

    fig, ax = plt.subplots(figsize=(8, 4))
    # soft, light rainbow-like color for entropy curve
    cmap = plt.get_cmap("rainbow")
    base_color = np.array(cmap(0.15))  # pick a gentle hue
    pastel_color = 0.5 * base_color + 0.5 * np.array([1, 1, 1, 1])

    ax.plot(
        callback.entropy_steps,
        callback.entropy_values,
        label="Policy Entropy",
        color=pastel_color,
        linewidth=2.0,
    )
    ax.set_xlabel("Training Steps")
    ax.set_ylabel("Policy Entropy (empirical)")
    ax.set_title("Policy Entropy Curve")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.set_facecolor("#faf9f7")  # very light background for soft contrast
    fig.tight_layout()

    out_path = os.path.join(out_dir, "ppo_policy_entropy.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _plot_action_distribution(callback: TrainingMetricsCallback, out_dir: str) -> None:
    """Stacked area chart of action distribution evolution.

    Styling: Times New Roman + pastel rainbow stack colors with low contrast.
    """

    if not callback.action_dist_steps or not callback.action_dist_probs:
        return

    os.makedirs(out_dir, exist_ok=True)
    steps = np.array(callback.action_dist_steps)
    probs_mat = np.stack(callback.action_dist_probs, axis=0)  # [num_checkpoints, action_dim]
    action_dim = probs_mat.shape[1]
    action_labels = [f"Action {i}" for i in range(action_dim)]

    plt.rcParams["font.family"] = "Times New Roman"

    fig, ax = plt.subplots(figsize=(8, 4))
    # build a soft rainbow (pastel) palette for the stacked areas
    cmap = plt.get_cmap("rainbow")
    xs = np.linspace(0.05, 0.95, action_dim)
    colors = []
    for x in xs:
        c = np.array(cmap(x))
        # mix with white to get low-contrast pastel colors
        pastel = 0.55 * c + 0.45 * np.array([1, 1, 1, 1])
        colors.append(pastel)

    ax.stackplot(steps, probs_mat.T, labels=action_labels, colors=colors, alpha=0.9)
    ax.set_xlabel("Training Steps")
    ax.set_ylabel("Action Probability")
    ax.set_title("Action Distribution Evolution (Stacked Area)")
    ax.legend(loc="upper right", fontsize=8, framealpha=0.85)
    ax.set_facecolor("#fbfbfb")
    ax.grid(True, axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()

    out_path = os.path.join(out_dir, "ppo_action_distribution.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _plot_learning_curve(log_dir: str, out_dir: str) -> None:
    """Plot training convergence curve using Monitor CSV logs.

    X: Episodes, Y: Average Reward (EMA-smoothed).
    """

    if not os.path.isdir(log_dir):
        return

    files = [
        os.path.join(log_dir, f)
        for f in os.listdir(log_dir)
        if f.endswith(".monitor.csv")
    ]
    if not files:
        return

    dfs = []
    for path in files:
        try:
            df = pd.read_csv(path, comment="#")
            dfs.append(df)
        except Exception:
            continue
    if not dfs:
        return

    df_all = pd.concat(dfs, ignore_index=True)
    if "r" not in df_all.columns:
        return

    df_all = df_all.sort_index().reset_index(drop=True)
    df_all["episode"] = np.arange(1, len(df_all) + 1)
    # Exponential moving average for smoother curve
    df_all["reward_ema"] = df_all["r"].ewm(alpha=0.1).mean()

    os.makedirs(out_dir, exist_ok=True)
    plt.rcParams["font.family"] = "Times New Roman"

    fig, ax = plt.subplots(figsize=(8, 4))
    # soft rainbow-inspired color for convergence curve
    cmap = plt.get_cmap("rainbow")
    base_color = np.array(cmap(0.8))
    pastel_color = 0.55 * base_color + 0.45 * np.array([1, 1, 1, 1])

    ax.plot(df_all["episode"], df_all["reward_ema"], label="EMA Reward", color=pastel_color, linewidth=2.0)
    ax.set_xlabel("Training Episodes")
    ax.set_ylabel("Average Reward (EMA)")
    ax.set_title("Learning Convergence Curve")
    ax.grid(True, linestyle="--", alpha=0.45)
    ax.set_facecolor("#fafafa")
    fig.tight_layout()
    out_path = os.path.join(out_dir, "ppo_learning_curve.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _compute_score_from_logs(log_dir: str) -> float | None:
    """Compute a scalar score from Monitor logs in ``log_dir``.

    Here we use the last EMA reward value as the score.
    """

    if not os.path.isdir(log_dir):
        return None

    files = [
        os.path.join(log_dir, f)
        for f in os.listdir(log_dir)
        if f.endswith(".monitor.csv")
    ]
    if not files:
        return None

    dfs = []
    for path in files:
        try:
            df = pd.read_csv(path, comment="#")
            dfs.append(df)
        except Exception:
            continue
    if not dfs:
        return None

    df_all = pd.concat(dfs, ignore_index=True)
    if "r" not in df_all.columns:
        return None

    df_all = df_all.sort_index().reset_index(drop=True)
    df_all["reward_ema"] = df_all["r"].ewm(alpha=0.1).mean()
    # use the last EMA reward as score
    try:
        score = float(df_all["reward_ema"].iloc[-1])
    except Exception:
        return None
    return score


