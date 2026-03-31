from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QTabWidget, QTextEdit, 
                             QLabel, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal
import numpy as np   # ← add this line
import pandas as pd
from typing import List, Dict
from ..core.analyzer import GroupSummary, SampleResults, SampleData

class ResultsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        self.tabs = QTabWidget()
        
        # Tab 1: Summary
        self.summary_tab = QWidget()
        summary_layout = QVBoxLayout(self.summary_tab)
        
        self.anova_text = QTextEdit()
        self.anova_text.setReadOnly(True)
        self.anova_text.setMaximumHeight(100)
        summary_layout.addWidget(QLabel("Two-way ANOVA Results:"))
        summary_layout.addWidget(self.anova_text)
        
        self.summary_table = QTableWidget(0, 0)
        self.summary_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        summary_layout.addWidget(self.summary_table)
        
        self.tabs.addTab(self.summary_tab, "Summary Table")
        
        # Tab 2: Detailed Samples
        self.detailed_tab = QWidget()
        detailed_layout = QVBoxLayout(self.detailed_tab)
        
        self.detailed_table = QTableWidget(0, 0)
        self.detailed_table.setSortingEnabled(True)
        detailed_layout.addWidget(self.detailed_table)
        
        self.tabs.addTab(self.detailed_tab, "Detailed Sample Table")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def update_summary(self, group_summaries, metric_stats, is_itt=False):
        if is_itt:
            metrics = ['auc', 'peak_above_baseline', 'time_to_peak', 
                    'roc_up', 'roc_down', 'early_drop', 'roc_to_early']
            metric_labels = ['AUC (inverted)', 'Nadir Below Baseline', 'Time to Nadir',
                         'ROC Fall (→Nadir)', 'ROC Recovery (Nadir→End)',
                         'Drop at t=15 (vs Baseline)', 'ROC to t=15']
        else:
            metrics = ['auc', 'peak_above_baseline', 'time_to_peak', 'roc_up', 'roc_down']
            metric_labels = ['AUC', 'Peak Above Baseline', 'Time to Peak',
                         'ROC Up (→Peak)', 'ROC Down (Peak→End)']
        
        self.summary_table.setRowCount(len(metrics))
        headers = ["Metric"]
        for gs in group_summaries:
            headers.append(f"{gs.name} (Mean ± SEM)")
        headers.extend(["p-value", "Significance"])
        
        self.summary_table.setColumnCount(len(headers))
        self.summary_table.setHorizontalHeaderLabels(headers)
        
        for i, (m, label) in enumerate(zip(metrics, metric_labels)):
            self.summary_table.setItem(i, 0, QTableWidgetItem(label))
            
            col = 1
            for gs in group_summaries:
                mean = gs.metrics_mean.get(m, 0)
                sem = gs.metrics_sem.get(m, 0)
                self.summary_table.setItem(i, col, QTableWidgetItem(f"{mean:.2f} ± {sem:.2f}"))
                col += 1
            
            stat = metric_stats.get(m, {})
            self.summary_table.setItem(i, col, QTableWidgetItem(f"{stat.get('p_value', 1.0):.4f}"))
            self.summary_table.setItem(i, col + 1, QTableWidgetItem(stat.get('stars', 'ns')))
            
        self.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def update_detailed(self, all_groups_data: Dict[str, List[SampleData]], all_results: Dict[str, List[SampleResults]]):
        # Rows: Sample | Group | Baseline | Peak | ...
        rows = []
        for g_name, samples in all_groups_data.items():
            results = all_results.get(g_name, [])
            for s_idx, sample in enumerate(samples):
                res = results[s_idx] if s_idx < len(results) else None
                row_data = {
                    'Group': g_name,
                    'Sample ID': f"S{s_idx+1}",
                    'Baseline': res.baseline if res else "N/A",
                    'Peak': res.peak_value if res else "N/A",
                    'Peak Above Base': res.peak_above_baseline if res else "N/A",
                    'Time to Peak': res.time_to_peak if res else "N/A",
                    'AUC': res.auc if res else "N/A",
                    'ROC Up': res.roc_up if res else "N/A",
                    'ROC Down': res.roc_down if res else "N/A",
                    'Active': "Yes" if sample.is_active else "No"
                }
                rows.append(row_data)
        
        self.detailed_table.setRowCount(len(rows))
        if rows:
            headers = list(rows[0].keys())
            self.detailed_table.setColumnCount(len(headers))
            self.detailed_table.setHorizontalHeaderLabels(headers)
            
            for i, r in enumerate(rows):
                for j, (key, val) in enumerate(r.items()):
                    item = QTableWidgetItem(str(val) if not isinstance(val, float) else f"{val:.2f}")
                    if r['Active'] == "No":
                        item.setForeground(Qt.GlobalColor.gray)
                        font = item.font()
                        font.setItalic(True)
                        item.setFont(font)
                    self.detailed_table.setItem(i, j, item)
        
        self.detailed_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def update_anova(self, anova_res: pd.DataFrame):
        if anova_res is not None:
            # mixed_anova returns a dataframe with columns like 'Source', 'SS', 'DF1', 'DF2', 'MS', 'F', 'p-unc', 'np2'
            # Note: newer versions of pingouin use 'p-val' instead of 'p-unc'
            text = ""
            for _, row in anova_res.iterrows():
                source = row.get('Source', 'Unknown')
                f_val = row.get('F', np.nan)
                # Try both common column names for p-value
                p_val = row.get('p-unc', row.get('p-val', np.nan))
                
                if not np.isnan(f_val):
                    text += f"{source}: F={f_val:.2f}, p={p_val:.4f}\n"
                else:
                    text += f"{source}: statistical data unavailable\n"
            self.anova_text.setText(text)
        else:
            self.anova_text.setText("ANOVA could not be performed (insufficient data).")
