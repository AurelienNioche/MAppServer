import numpy as np
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator
from scipy.special import logit
import pandas as pd
import seaborn as sns


def plot_step_transformations(step_events, transformed_all_steps, untransformed_all_steps):

    fig, axes = plt.subplots(ncols=4, figsize=(10, 5))
    fig.set_tight_layout(True)

    ax = axes[0]
    ax.set_title(f"All steps")
    ax.hist(np.concatenate(step_events), bins=30, color="C0", alpha=0.5)

    ax = axes[1]
    ax.set_title("Logit representation")
    ax.hist(logit(np.concatenate(step_events)), bins=30, color="C0", alpha=0.5)

    ax = axes[2]
    ax.set_title("BoxCox + Logit representation")
    ax.hist(np.concatenate(transformed_all_steps), bins=30, color="C0", alpha=0.5)

    ax = axes[3]
    ax.set_title("inverse-transformed")
    ax.hist(np.concatenate(untransformed_all_steps), bins=30, color="C0", alpha=0.5)


def plot_bic_score(n_components_range, cmp_score, n_days):

    fig, axes = plt.subplots(nrows=n_days, figsize=(5, 20), sharex=True)
    for day in range(n_days):
        ax = axes[day]
        ax.plot(n_components_range, cmp_score[day], marker='o')
        if day == n_days-1:
            ax.set_xlabel('Number of components')
        # have only integer ticks
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_ylabel('BIC')


def plot_deriv_cum_steps(timestep, deriv_cum_steps):

    fig, axes = plt.subplots(deriv_cum_steps.shape[0], figsize=(3, 10), sharex=True)
    for ax, activity in zip(axes, deriv_cum_steps):
        ax.plot(timestep, activity, color="C0")
        ax.set_ylim(-70, np.max(deriv_cum_steps))
        ax.grid(False)


def plot_samples(n_model_types, n_days, timestep, deriv_cum_steps, gen_deriv_cum_steps, n_components_range):

    n_model_plot = min(n_model_types, 4)

    fig, axes = plt.subplots(
        ncols=n_model_plot+1,
        nrows=n_days,
        figsize=(6, 10), sharex=True, sharey=True)

    fig.set_tight_layout(True)

    for day in range(n_days):
        ax = axes[day, 0]
        ax.plot(timestep, deriv_cum_steps[day], color="C0")
        if day == 0:
            ax.set_title("Data")
        for model in range(n_model_plot):
            ax = axes[day, model+1]
            ax.plot(timestep, gen_deriv_cum_steps[model, day], color="C0")
            ax.grid(False)
            if day == 0:
                ax.set_title(f"{n_components_range[model]} comp.")
            elif day == n_days-1:
                ax.set_xlabel("Time")

    fig.supxlabel("Number of components")
    fig.supylabel("Days")


def runs(*args, figsize=(4, 3)):
    fig, axes = plt.subplots(nrows=2, figsize=figsize)
    for i, r in enumerate(args):
        policy = r["policy"]
        hist_pos = r["position"]
        hist_vel = r["velocity"]

        if len(hist_pos.shape) == 3:
            hist_pos = hist_pos[:, -1, :].copy()  # Take the last learning episode only
            hist_vel = hist_vel[:, -1, :].copy()  # Take the last learning episode only

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
        axes[0].plot(
            x, pos, color=f"C{i}", label=label, linestyle=linestyle, linewidth=linewidth
        )
        axes[0].fill_between(
            x, pos - pos_disp, pos + pos_disp, alpha=0.1, color=f"C{i}"
        )
        axes[1].plot(x, vel, color=f"C{i}", linestyle=linestyle, linewidth=linewidth)
        axes[1].fill_between(
            x, vel - vel_disp, vel + vel_disp, alpha=0.1, color=f"C{i}"
        )
        axes[0].set_ylabel("position")
        axes[1].set_ylabel("velocity")
        axes[1].set_xlabel("time")

    fig.legend(loc=[0.05, 0.05], fontsize=5)
    fig.tight_layout()

    plt.show()


def error(*args, fig=None, ax=None, ylabel="error", var="error"):
    if fig is None and ax is None:
        fig, ax = plt.subplots(figsize=(3, 3))
    for i, r in enumerate(args):
        policy = r["policy"]
        hist_err = r[var]
        label = policy.replace("-", " ").capitalize()
        hist_err_mean = hist_err.mean(axis=0)
        x = np.arange(len(hist_err_mean))
        hist_err_std = hist_err.std(axis=0)

        if label.startswith("Af"):
            label = label.replace("Af", "Active inference -")
            linestyle, linewidth = "-", 2
        else:
            linestyle, linewidth = "-", 1
        ax.plot(
            x,
            hist_err_mean,
            color=f"C{i}",
            label=label,
            linestyle=linestyle,
            linewidth=linewidth,
        )
        ax.fill_between(
            x,
            hist_err_mean - hist_err_std,
            hist_err_mean + hist_err_std,
            alpha=0.1,
            color=f"C{i}",
        )
        ax.set_ylabel(ylabel=ylabel)
        ax.set_xlabel("epoch")

        ax.legend(loc="center")
    fig.tight_layout()


def error_like(variable="error", *args):
    fig, ax = plt.subplots(figsize=(3, 3))
    for i, r in enumerate(args):
        policy = r["policy"]
        hist_err = r[variable]
        label = policy.replace("-", " ").capitalize()
        hist_err_mean = hist_err.mean(axis=0)
        x = np.arange(len(hist_err_mean))
        hist_err_std = hist_err.std(axis=0)

        if label.startswith("Af"):
            label = label.replace("Af", "Active inference -")
            linestyle, linewidth = "-", 2
        else:
            linestyle, linewidth = "-", 1
        ax.plot(
            x,
            hist_err_mean,
            color=f"C{i}",
            label=label,
            linestyle=linestyle,
            linewidth=linewidth,
        )
        ax.fill_between(
            x,
            hist_err_mean - hist_err_std,
            hist_err_mean + hist_err_std,
            alpha=0.1,
            color=f"C{i}",
        )
        ax.set_ylabel(variable)
        ax.set_xlabel("epoch")

    fig.legend(loc="center")
    plt.tight_layout()
    plt.show()


def q(alpha, title=r"$\alpha$", figsize=(6, 2), cmap="viridis", between_0_and_1=False):
    plt.rcParams.update({"text.usetex": True})

    if len(alpha.shape) == 4:
        n_action, n_timestep, n_velocity, _ = alpha.shape
        fig, axes = plt.subplots(ncols=n_timestep, nrows=n_action, figsize=figsize)
        fig.suptitle(title)
        for a_idx in range(n_action):
            for t_idx in range(n_timestep):
                ax = axes[a_idx, t_idx]
                img = alpha[a_idx, t_idx, :, :]
                if between_0_and_1:
                    ax.imshow(img, aspect="auto", cmap=cmap, vmin=0, vmax=1)
                else:
                    ax.imshow(img, aspect="auto", cmap=cmap)
                ax.get_xaxis().set_ticks([])
                ax.axes.get_yaxis().set_ticks([])
        plt.tight_layout()

    elif len(alpha.shape) == 3:
        n_position, n_velocity, n_position = alpha.shape
        fig, axes = plt.subplots(ncols=n_velocity, nrows=1, figsize=figsize)
        fig.suptitle(title)

        for i, ax in enumerate(axes):
            img = alpha[:, i, :]
            if between_0_and_1:
                ax.imshow(img, aspect="auto", cmap=cmap, vmin=0, vmax=1)
            else:
                ax.imshow(img, aspect="auto", cmap=cmap)
            ax.get_xaxis().set_ticks([])
            ax.axes.get_yaxis().set_ticks([])
        plt.tight_layout()

    else:
        raise ValueError


def plot_af(run):
    # Get the data
    epistemic = run["epistemic"]
    pragmatic = run["pragmatic"]
    n_sample, n_episode, n_timestep = epistemic.shape
    # Get the samples and episodes to plot
    samples = list(range(n_sample))[:min(n_sample, 3)]
    all_ep = list(range(n_episode))
    episodes = all_ep[:min(n_episode, 4)] + all_ep[-4:]
    episodes = np.unique(episodes)  # To avoid duplicates
    # Create the figure
    fig, axes = plt.subplots(figsize=(4*len(samples), 3*len(episodes)),
                             nrows=len(episodes),
                             ncols=len(samples),
                             sharex=True, sharey=True)
    fig.set_tight_layout(True)
    # Plot the data
    for sample in samples:
        for row_idx, ep_idx in enumerate(episodes):
            # Get the axes
            if isinstance(axes, np.ndarray) and axes.ndim > 1:
                ax = axes[row_idx, sample]
            elif isinstance(axes, np.ndarray):
                if len(episodes) > 1:
                    ax = axes[row_idx]
                else:
                    ax = axes[sample]
            else:
                ax = axes
            # Plot the epistemic value
            line1, = ax.plot(np.arange(n_timestep), epistemic[sample, ep_idx], label="epistemic", color="C0")
            ax.set_ylabel("epistemic value")
            # Create a second y-axis
            ax = ax.twinx()
            # Plot the pragmatic value
            line2, = ax.plot(np.arange(n_timestep), pragmatic[sample, ep_idx], label="pragmatic", color="C1")
            ax.set_ylabel("pragmatic value")
            # Add a legend
            ax.legend([line1, line2], ["epistemic", "pragmatic"])
            # Add a label to the x-axis
            ax.set_xlabel("action plan")
    plt.show()


def plot_day(day_activity, figsize=(4, 3), linewidth=2):
    fig, ax = plt.subplots(nrows=1, figsize=figsize)

    x = np.linspace(0, 1, len(day_activity))
    ax.plot(
        x, day_activity, color=f"C0", linewidth=linewidth
    )
    ax.set_ylabel("position")
    ax.set_xlabel("time")

    fig.tight_layout()
    plt.show()


def plot_day_progression(af_run):
    """Plot the progression of the day"""
    x = af_run["position"]
    # Create a MultiIndex
    if len(x.shape) == 2:
        index = pd.MultiIndex.from_product(
            [range(i) for i in x.shape],
            names=['episode', 'timestep'])
        df = pd.DataFrame({'position': x.flatten()}, index=index)
        # fig, ax = plt.subplots(figsize=(10, 6))
        sns.relplot(
            data=df,
            x='timestep',
            y='position',
            hue='episode',
            kind='line')
        plt.show()
    elif len(x.shape) == 3:
        index = pd.MultiIndex.from_product(
            [range(i) for i in x.shape],
            names=['restart', 'episode', 'timestep'])
         # Flatten the 3D numpy array to a 1D array and create the DataFrame
        df = pd.DataFrame({'position': x.flatten()}, index=index)
        # fig, ax = plt.subplots(figsize=(10, 6))
        sns.relplot(
            data=df.query("restart == 0"),
            x='timestep',
            y='position',
            hue='episode',
            kind='line')
        plt.show()
    else:
        raise ValueError(f"Expected a 2D or 3D array, got {x.shape}")

