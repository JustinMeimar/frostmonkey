#!/home/justin/tools/fossil/figures/.venv/bin/python
import sys
from fossil_figures import apply_style, load_stdin, comparison_hbar

apply_style(column="single")
data = load_stdin()
fig = comparison_hbar(
    data,
    metrics=["score"],
    xlabel="Score",
    legend=False,
)
fig.savefig(sys.argv[1])
