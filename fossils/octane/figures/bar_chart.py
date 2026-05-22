#!/home/justin/tools/fossil/figures/.venv/bin/python
import sys
from fossil_figures import apply_style, load_stdin, comparison_bar

apply_style(column="double")
data = load_stdin()
baseline = data.column_names[0]
fig = comparison_bar(
    data,
    normalize_to=baseline,
    ylabel=f"Relative to {baseline}",
)
fig.savefig(sys.argv[1])
