"""Utilities for rendering Seaborn charts for Chainlit messages."""

from __future__ import annotations

import io
from collections.abc import Sequence

import matplotlib
import seaborn as sns

import chainlit as cl

matplotlib.use("Agg")


def histogram_from_values(
    values: Sequence[float],
    *,
    title: str = "Value distribution",
    name: str = "seaborn_hist.png",
) -> cl.Image:
    """
    Build a histogram (with KDE) for the provided values and return it as a Chainlit image.

    Parameters
    ----------
    values:
        Numeric sequence to plot. Must contain at least one element.
    title:
        Title to render above the plot.
    name:
        Attachment name presented in the Chainlit UI.
    """
    if not values:
        raise ValueError("values must not be empty")

    from matplotlib import pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 4), tight_layout=True)
    sns.histplot(values, kde=True, ax=ax, color="#2563eb", edgecolor="white")
    ax.set_title(title)
    ax.set_xlabel("Value")
    ax.set_ylabel("Frequency")

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150)
    plt.close(fig)
    buffer.seek(0)

    return cl.Image(content=buffer.getvalue(), mime="image/png", name=name)

