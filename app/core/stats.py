import numpy as np
import pandas as pd
import pingouin as pg
from scipy import stats
import scikit_posthocs as sp
from typing import List, Dict, Optional, Tuple
import warnings
from .analyzer import SampleData, SampleResults, GroupSummary

# Suppress SciPy warnings about precision loss in moment calculations
warnings.filterwarnings('ignore', message='.*Precision loss occurred in moment calculation.*')

def get_p_stars(p: float) -> str:
    if p < 0.0001: return "****"
    if p < 0.001: return "***"
    if p < 0.01: return "**"
    if p < 0.05: return "*"
    return "ns"

def _safe_get_metric(r: SampleResults, metric_name: str) -> Optional[float]:
    """
    Safely retrieve a metric value from a SampleResults object.
    Returns None if the attribute doesn't exist, is None, or is NaN.
    Handles Optional[float] fields (e.g. early_drop, roc_to_early) that
    are None when not applicable (GTT mode) — previously np.isnan(None)
    raised a TypeError that silently caused p_value to fall through to 1.0.
    """
    v = getattr(r, metric_name, None)
    if v is None:
        return None
    try:
        if np.isnan(float(v)):
            return None
        return float(v)
    except (TypeError, ValueError):
        return None

def perform_two_way_rm_anova(
    groups: List[str],
    time_points: List[float],
    all_data: Dict[str, List[SampleData]],
    use_baseline_norm: bool = False
) -> Optional[pd.DataFrame]:
    """
    Two-way repeated measures ANOVA (Time x Group).
    Expects data in long format for pingouin.
    """
    rows = []
    for group_name in groups:
        samples = all_data.get(group_name, [])
        for s_idx, sample in enumerate(samples):
            if not sample.is_active:
                continue

            vals = sample.values.copy()
            if use_baseline_norm:
                baseline = vals[0]
                if baseline != 0:
                    vals = (vals / baseline) * 100
                else:
                    continue

            for t_idx, val in enumerate(vals):
                if t_idx in sample.excluded_cells:
                    continue
                rows.append({
                    'Subject': f"{group_name}_{s_idx}",
                    'Group': group_name,
                    'Time': time_points[t_idx],
                    'Value': val
                })

    if not rows:
        return None

    df = pd.DataFrame(rows)

    if df['Group'].nunique() < 2 or df['Time'].nunique() < 2:
        return None

    try:
        res = pg.mixed_anova(
            data=df, dv='Value', between='Group',
            within='Time', subject='Subject'
        )
        return res
    except Exception as e:
        print(f"ANOVA Error: {e}")
        return None


def perform_metric_comparison(
    groups: List[str],
    metric_name: str,
    group_results: Dict[str, List[SampleResults]],
    use_parametric: bool = True
) -> Dict:
    """
    Perform statistical comparison for a single metric across groups.
    Uses _safe_get_metric to handle Optional[float] fields (e.g. early_drop,
    roc_to_early) which are None for GTT samples — previously caused silent
    TypeError in np.isnan(None), returning a spurious p=1.0.
    """
    data_by_group = {}
    for g in groups:
        vals = []
        for r in group_results.get(g, []):
            if r is None:
                continue
            v = _safe_get_metric(r, metric_name)
            if v is not None:
                vals.append(v)
        if len(vals) >= 1:
            data_by_group[g] = vals

    valid_groups = list(data_by_group.keys())
    if len(valid_groups) < 2:
        return {"p_value": np.nan, "stars": "ns", "test_name": "N/A", "posthoc": None, "mixed_sign": False}

    group_list = [data_by_group[g] for g in valid_groups]

    # Remove mixed-sign logic that used absolute values, as directionality
    # is biologically relevant in tolerance tests.
    p_value = np.nan
    test_name = ""
    posthoc = None

    if len(valid_groups) == 2:
        g1, g2 = group_list[0], group_list[1]
        # Check for zero variance in either group
        var_g1 = np.var(g1) if len(g1) > 1 else 0
        var_g2 = np.var(g2) if len(g2) > 1 else 0
        
        if use_parametric:
            test_name = "Independent t-test"
            if len(g1) > 1 and len(g2) > 1 and (var_g1 > 0 or var_g2 > 0):
                try:
                    _, p_value = stats.ttest_ind(g1, g2)
                except Exception:
                    p_value = np.nan
            else:
                p_value = np.nan  # Cannot test with N=1 or zero variance
        else:
            test_name = "Mann-Whitney U"
            if len(g1) >= 1 and len(g2) >= 1:
                try:
                    _, p_value = stats.mannwhitneyu(g1, g2, alternative='two-sided')
                except Exception:
                    p_value = np.nan
            else:
                p_value = np.nan

    elif len(valid_groups) >= 3:
        if use_parametric:
            test_name = "One-way ANOVA"
            try:
                _, p_value = stats.f_oneway(*group_list)
                if p_value < 0.05:
                    flat_data, flat_groups = [], []
                    for g_name in valid_groups:
                        flat_data.extend(group_list[valid_groups.index(g_name)])
                        flat_groups.extend([g_name] * len(group_list[valid_groups.index(g_name)]))
                    df_tukey = pd.DataFrame({'val': flat_data, 'group': flat_groups})
                    posthoc = pg.pairwise_tukey(data=df_tukey, dv='val', between='group')
            except Exception:
                p_value = np.nan
        else:
            test_name = "Kruskal-Wallis"
            try:
                _, p_value = stats.kruskal(*group_list)
                if p_value < 0.05:
                    flat_data, flat_groups = [], []
                    for g_name in valid_groups:
                        flat_data.extend(group_list[valid_groups.index(g_name)])
                        flat_groups.extend([g_name] * len(group_list[valid_groups.index(g_name)]))
                    df_dunn = pd.DataFrame({'val': flat_data, 'group': flat_groups})
                    posthoc = sp.posthoc_dunn(
                        df_dunn, val_col='val', group_col='group', p_adjust='bonferroni'
                    )
            except Exception:
                p_value = np.nan

    return {
        "p_value": p_value,
        "stars": get_p_stars(p_value) if not np.isnan(p_value) else "ns",
        "test_name": test_name,
        "posthoc": posthoc
    }


def perform_posthoc_per_time(
    groups: List[str],
    time_points: List[float],
    all_data: Dict[str, List[SampleData]],
    use_baseline_norm: bool = False
) -> Dict[float, pd.DataFrame]:
    """
    Pairwise comparisons per time point (Bonferroni-corrected).
    """
    posthocs = {}
    for t_idx, t in enumerate(time_points):
        data_at_t = []
        group_at_t = []
        for g_name in groups:
            samples = all_data.get(g_name, [])
            for s in samples:
                if not s.is_active or t_idx in s.excluded_cells:
                    continue
                val = s.values[t_idx]
                if use_baseline_norm:
                    baseline = s.values[0]
                    if baseline != 0:
                        val = (val / baseline) * 100
                    else:
                        continue
                data_at_t.append(val)
                group_at_t.append(g_name)

        if len(set(group_at_t)) >= 2:
            df = pd.DataFrame({'val': data_at_t, 'group': group_at_t})
            ph = pg.pairwise_tests(
                data=df, dv='val', between='group', padjust='bonferroni'
            )
            posthocs[t] = ph

    return posthocs
