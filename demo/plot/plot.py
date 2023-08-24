import matplotlib.pyplot as plt
import numpy as np


def plot_runs(runs):
    fig, axes = plt.subplots(nrows=2, figsize=(4, 3))
    for i, r in enumerate(runs):
        policy = r["policy"]
        hist_pos = r["position"]
        hist_vel = r["velocity"]

        label = policy.replace("-", " ").capitalize()
        pos = hist_pos.mean(axis=0)
        pos_disp = hist_pos.std(axis=0)
        vel = hist_vel.mean(axis=0)
        vel_disp = hist_vel.std(axis=0)
        x = np.linspace(0, 1, len(pos))
        if label.startswith("Af"):
            label = label.replace("Af", "Active inference -")
            linewidth = 2
            if label.endswith("epistemic"):
                linestyle = ":"
                linewidth = 4
            elif label.endswith("pragmatic"):
                linestyle = "-."
            else:
                label = label.replace(" -", "")
                linestyle = "--"
        else:
            linestyle, linewidth = "-", 1
        axes[0].plot(x, pos, color=f"C{i}", label=label, linestyle=linestyle, linewidth=linewidth)
        axes[0].fill_between(x, pos - pos_disp, pos + pos_disp, alpha=0.1, color=f"C{i}")
        axes[1].plot(x, vel, color=f"C{i}", linestyle=linestyle, linewidth=linewidth)
        axes[1].fill_between(x, vel - vel_disp, vel + vel_disp, alpha=0.1, color=f"C{i}")
        axes[0].set_ylabel("position")
        axes[1].set_ylabel("velocity")
        axes[1].set_xlabel("time")

    fig.legend(loc=[0.05, 0.05], fontsize=5)
    fig.tight_layout()

    plt.show()


def plot_error(runs):

    fig, ax = plt.subplots(figsize=(3, 3))
    for i, r in enumerate(runs):
        policy = r["policy"]
        hist_err = r["error"]
        label = policy.replace("-", " ").capitalize()
        hist_err_mean = hist_err.mean(axis=0)
        x = np.arange(len(hist_err_mean))
        hist_err_std = hist_err.std(axis=0)

        if label.startswith("Af"):
            label = label.replace("Af", "Active inference -")
            linestyle, linewidth = "-", 2
        else:
            linestyle, linewidth = "-", 1
        ax.plot(x, hist_err_mean, color=f"C{i}", label=label, linestyle=linestyle, linewidth=linewidth)
        ax.fill_between(x, hist_err_mean - hist_err_std, hist_err_mean + hist_err_std, alpha=0.1, color=f"C{i}")
        ax.set_ylabel("error")
        ax.set_xlabel("epoch")

    fig.legend(loc="center")
    plt.tight_layout()
    plt.show()
