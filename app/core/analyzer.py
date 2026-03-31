import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class SampleData:
    name: str
    time_points: np.ndarray
    values: np.ndarray
    excluded_cells: List[int]  # Indices of values to exclude
    is_active: bool = True

@dataclass
class SampleResults:
    baseline: float
    peak_value: float
    peak_above_baseline: float
    time_to_peak: float
    auc: float
    roc_up: float
    roc_down: float
    normalized_values: Optional[np.ndarray] = None
    early_drop: Optional[float] = None        # value at t=15 minus baseline (ITT only)
    roc_to_early: Optional[float] = None      # ROC from baseline to t=15 (ITT only)

@dataclass
class GroupSummary:
    name: str
    time_points: np.ndarray
    metrics_mean: Dict[str, float]
    metrics_sem: Dict[str, float]
    values_mean: np.ndarray
    values_sem: np.ndarray

def calculate_sample_metrics(sample: SampleData, use_baseline_norm: bool = False) -> Optional[SampleResults]:
    if not sample.is_active:
        return None

    mask = np.ones(len(sample.values), dtype=bool)
    mask[sample.excluded_cells] = False

    if not any(mask):
        return None

    early_drop = None
    roc_to_early = None

    baseline = sample.values[0] if 0 not in sample.excluded_cells else np.nan


    calc_values = sample.values.copy()
    if use_baseline_norm:
        if np.isnan(baseline) or baseline == 0:
            return None
        calc_values = (calc_values / baseline) * 100
        baseline = 100.0

    masked_values = calc_values[mask]
    masked_times = sample.time_points[mask]

    if len(masked_values) == 0:
        return None

    if use_baseline_norm:
        # --- ITT mode: find the nadir (glucose minimum) ---
        # The physiological event of interest is the maximum glucose suppression
        extreme_value = np.min(masked_values)
        extreme_idx = np.argmin(masked_values)
        time_to_extreme = masked_times[extreme_idx]
        
        # "Peak above baseline" becomes "Nadir below baseline" (positive = drop)
        extreme_above_baseline = baseline - extreme_value if not np.isnan(baseline) else np.nan

                # Early clearance metrics: value at t=15 relative to baseline
        # Find the index of the 15-minute time point if it exists
        early_time = 15.0

        early_tp_matches = np.where(sample.time_points == early_time)[0]

        if len(early_tp_matches) > 0:
            early_idx = early_tp_matches[0]
            # Only calculate if that time point is not excluded
            if early_idx not in sample.excluded_cells:
                early_val = calc_values[early_idx]  # already normalized if ITT
                # Drop is positive when glucose falls (baseline - value)
                # Can be negative if glucose rises above baseline at t=15
                early_drop = float(baseline - early_val)
                # ROC to early: rate of change to t=15
                # Positive = falling glucose, Negative = rising glucose
                if early_time > 0:
                    roc_to_early = float(early_drop / early_time)

        # AUC: baseline-corrected, but inverted so larger drop = larger AUC
        # We subtract values from baseline so the area is positive when glucose falls
        if not np.isnan(baseline):
            try:
                auc = np.trapezoid(baseline - masked_values, masked_times)
            except AttributeError:
                auc = np.trapz(baseline - masked_values, masked_times)
        else:
            auc = np.nan

        # ROC down (baseline → nadir): rate of glucose fall, reported as positive value
        # Larger = faster insulin-driven clearance
        if time_to_extreme > 0 and not np.isnan(baseline):
            roc_up = (baseline - extreme_value) / time_to_extreme  # stored in roc_up field
        else:
            roc_up = 0.0

        # ROC up (nadir → end): rate of counter-regulatory recovery
        final_time = masked_times[-1]
        final_value = masked_values[-1]
        if final_time > time_to_extreme:
            roc_down = (final_value - extreme_value) / (final_time - time_to_extreme)
        else:
            roc_down = 0.0

    else:
        # --- GTT mode: find the peak (glucose maximum) ---
        extreme_value = np.max(masked_values)
        extreme_idx = np.argmax(masked_values)
        time_to_extreme = masked_times[extreme_idx]

        extreme_above_baseline = extreme_value - baseline if not np.isnan(baseline) else np.nan

        if not np.isnan(baseline):
            try:
                auc = np.trapezoid(masked_values - baseline, masked_times)
            except AttributeError:
                auc = np.trapz(masked_values - baseline, masked_times)
        else:
            auc = np.nan

        if time_to_extreme > 0 and not np.isnan(baseline):
            roc_up = (extreme_value - baseline) / time_to_extreme
        else:
            roc_up = 0.0

        final_time = masked_times[-1]
        final_value = masked_values[-1]
        if final_time > time_to_extreme:
            roc_down = (extreme_value - final_value) / (final_time - time_to_extreme)
        else:
            roc_down = 0.0

    return SampleResults(
        baseline=baseline,
        peak_value=extreme_value,
        peak_above_baseline=extreme_above_baseline,
        time_to_peak=time_to_extreme,
        auc=auc,
        roc_up=roc_up,
        roc_down=roc_down,
        normalized_values=calc_values if use_baseline_norm else None,
        early_drop=early_drop,
        roc_to_early=roc_to_early
    )
def calculate_group_summary(group_name: str, samples: List[SampleData], results: List[SampleResults]) -> GroupSummary:
    # results only contains active samples' results
    if not results:
        return None
    
    metrics = ['baseline', 'peak_value', 'peak_above_baseline', 'time_to_peak', 
           'auc', 'roc_up', 'roc_down', 'early_drop', 'roc_to_early']
    means = {}
    sems = {}
    
    for metric in metrics:
        vals = []
        for r in results:
            v = getattr(r, metric, None)
            if v is not None and not np.isnan(v):
                vals.append(v)
        if vals:
            means[metric] = np.mean(vals)
            sems[metric] = np.std(vals, ddof=1) / np.sqrt(len(vals)) if len(vals) > 1 else 0.0
        else:
            means[metric] = np.nan
            sems[metric] = np.nan
        
    # Calculate mean/SEM per time point for plotting
    # Use normalized values if ITT toggle was on (determined by results[0].normalized_values)
    use_norm = results[0].normalized_values is not None
    
    time_points_data = []
    num_tp = len(samples[0].time_points)
    
    tp_means = []
    tp_sems = []
    
    for i in range(num_tp):
        vals_at_tp = []
        for s_idx, s in enumerate(samples):
            if not s.is_active or i in s.excluded_cells:
                continue
            
            # Find matching result for this sample to get normalized value if needed
            # This is a bit inefficient but safe
            s_res = next((r for r in results if r is not None and (r.normalized_values is not None if use_norm else True)), None)
            # Actually, just use the sample values and normalize here if needed
            val = s.values[i]
            if use_norm:
                s_baseline = s.values[0]
                if s_baseline != 0:
                    val = (val / s_baseline) * 100
            vals_at_tp.append(val)
            
        if vals_at_tp:
            tp_means.append(np.mean(vals_at_tp))
            tp_sems.append(np.std(vals_at_tp, ddof=1) / np.sqrt(len(vals_at_tp)) if len(vals_at_tp) > 1 else 0.0)
        else:
            tp_means.append(np.nan)
            tp_sems.append(np.nan)
            
    return GroupSummary(
        name=group_name,
        time_points=samples[0].time_points,
        metrics_mean=means,
        metrics_sem=sems,
        values_mean=np.array(tp_means),
        values_sem=np.array(tp_sems)
    )
