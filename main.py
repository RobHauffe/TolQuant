import sys
import numpy as np
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QSplitter, QMenuBar, QMenu, QMessageBox, 
                             QFileDialog, QTableWidgetItem)
from PyQt6.QtCore import Qt
from app.ui.input_panel import InputPanel
from app.ui.plot_widget import PlotWidget
from app.ui.results_widget import ResultsWidget
from app.core.analyzer import (SampleData, calculate_sample_metrics, 
                               calculate_group_summary, GroupSummary)
from app.core.stats import (perform_two_way_rm_anova, perform_metric_comparison)
from app.export.exporter import export_to_excel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TolQuant — Tolerance Test Analyzer")
        self.setMinimumSize(1200, 800)
        
        self.init_ui()
        self.create_menu()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left Panel: Data Input
        self.input_panel = InputPanel()
        self.input_panel.run_requested.connect(self.run_analysis)
        self.splitter.addWidget(self.input_panel)
        
        # Right Panel: Results & Plot
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        self.plot_widget = PlotWidget()
        self.right_splitter.addWidget(self.plot_widget)
        
        self.results_widget = ResultsWidget()
        self.right_splitter.addWidget(self.results_widget)
        
        self.splitter.addWidget(self.right_splitter)
        # Increase left panel width by 25% (was 1:2 ratio, now roughly 5:7)
        self.splitter.setStretchFactor(0, 5)
        self.splitter.setStretchFactor(1, 7)
        
        main_layout.addWidget(self.splitter)

    def create_menu(self):
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        
        load_example_action = file_menu.addAction("Load Example Data")
        load_example_action.triggered.connect(self.load_example_data)
        
        export_action = file_menu.addAction("Export to Excel")
        export_action.triggered.connect(self.export_data)
        
        file_menu.addSeparator()
        
        clear_action = file_menu.addAction("Clear All")
        clear_action.triggered.connect(self.clear_all)
        
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        # Help Menu
        help_menu = menubar.addMenu("&Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about)

    def run_analysis(self):
        raw_input = self.input_panel.get_all_data()
        test_type = raw_input['test_type']
        time_points = raw_input['time_points']
        groups_raw = raw_input['groups']
        is_itt = (test_type == "ITT")        
        use_baseline_norm = (test_type == "ITT") # Simple toggle based on test type
        
        all_group_summaries = []
        all_sample_results = {}
        processed_data = {} # For stats
        
        for g_name, samples_raw in groups_raw.items():
            samples_data = []
            results_list = []
            for s in samples_raw:
                sample_obj = SampleData(
                    name=g_name,
                    time_points=time_points,
                    values=s['values'],
                    excluded_cells=s['excluded'],
                    is_active=s['is_active']
                )
                samples_data.append(sample_obj)
                
                res = calculate_sample_metrics(sample_obj, use_baseline_norm)
                results_list.append(res)
            
            # Active results for summary
            active_results = [r for r in results_list if r is not None]
            gs = calculate_group_summary(g_name, samples_data, active_results)
            
            if gs:
                all_group_summaries.append(gs)
                all_sample_results[g_name] = results_list
                processed_data[g_name] = samples_data
        
        if not all_group_summaries:
            QMessageBox.warning(self, "No Data", "No valid data to analyze.")
            return

        # Statistics
        group_names = list(processed_data.keys())
        anova_res = perform_two_way_rm_anova(group_names, time_points.tolist(), processed_data, use_baseline_norm)
        
        metrics = ['auc', 'peak_above_baseline', 'time_to_peak', 'roc_up', 'roc_down']
        if is_itt:
            metrics.extend(['early_drop', 'roc_to_early'])
            
        metric_stats = {}
        for m in metrics:
            group_res_dict = {g: [r for r in all_sample_results[g] if r is not None] for g in group_names}
            metric_stats[m] = perform_metric_comparison(group_names, m, group_res_dict)

        # Update UI
        self.plot_widget.update_data(all_group_summaries, test_type=test_type, 
                                     unit=raw_input['unit'], is_itt=is_itt)
        self.results_widget.update_summary(all_group_summaries, metric_stats, is_itt=is_itt)
        self.results_widget.update_detailed(processed_data, all_sample_results)
        self.results_widget.update_anova(anova_res)
        
        # Store last analysis results for export
        self._last_export_data = {
            'group_summaries': all_group_summaries,
            'sample_results': all_sample_results,
            'processed_data': processed_data,
            'metric_stats': metric_stats,
            'anova_res': anova_res,
            'time_points': time_points,
            'test_type': test_type,
            'unit': raw_input['unit'],
            'is_itt': is_itt
        }

    def load_example_data(self):
        # Pre-fill with realistic GTT data
        self.clear_all()
        self.input_panel.time_points_edit.setText("0, 15, 30, 60, 120")
        self.input_panel.add_group("Control")
        self.input_panel.add_group("Treatment")
        
        # Add some data for Control
        ctrl = self.input_panel.groups[0]
        data_ctrl = [
            [100, 250, 200, 150, 110],
            [95, 240, 190, 145, 105],
            [105, 260, 210, 155, 115],
            [102, 255, 205, 152, 112],
            [98, 245, 195, 148, 108]
        ]
        for i in range(5):
            ctrl.add_row()
            for j, val in enumerate(data_ctrl[i]):
                ctrl.table.setItem(i, j + 1, QTableWidgetItem(str(val)))

        # Add some data for Treatment
        treat = self.input_panel.groups[1]
        data_treat = [
            [105, 350, 320, 280, 200],
            [110, 360, 330, 290, 210],
            [100, 340, 310, 270, 190],
            [108, 355, 325, 285, 205],
            [102, 345, 315, 275, 195]
        ]
        for i in range(5):
            treat.add_row()
            for j, val in enumerate(data_treat[i]):
                treat.table.setItem(i, j + 1, QTableWidgetItem(str(val)))
        
        self.run_analysis()

    def export_data(self):
        if not hasattr(self, '_last_export_data') or not self._last_export_data:
            QMessageBox.warning(self, "No Data", "Please run an analysis before exporting.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Export to Excel", "", "Excel Files (*.xlsx)")
        if not file_path:
            return

        try:
            d = self._last_export_data
            time_points = d['time_points']
            group_summaries = d['group_summaries']
            processed_data = d['processed_data']
            all_sample_results = d['sample_results']
            metric_stats = d['metric_stats']
            anova_res = d['anova_res']

            # --- Sheet 1: Curve Data ---
            curve_rows = []
            for gs in group_summaries:
                for i, tp in enumerate(time_points):
                    curve_rows.append({
                        'Group': gs.name,
                        'Time': tp,
                        'Mean': gs.values_mean[i],
                        'SEM': gs.values_sem[i]
                    })
            curve_df = pd.DataFrame(curve_rows)

            # --- Sheet 2: Summary Statistics ---
            if d['is_itt']:
                metrics = ['auc', 'peak_above_baseline', 'time_to_peak', 'roc_up', 'roc_down', 'early_drop', 'roc_to_early']
                metric_labels = ['AUC (inverted)', 'Nadir Below Baseline', 'Time to Nadir',
                               'ROC Fall (→Nadir)', 'ROC Recovery (Nadir→End)',
                               'Drop at t=15 (vs Baseline)', 'ROC to t=15']
            else:
                metrics = ['auc', 'peak_above_baseline', 'time_to_peak', 'roc_up', 'roc_down']
                metric_labels = ['AUC', 'Peak Above Baseline', 'Time to Peak',
                               'ROC Up (→Peak)', 'ROC Down (Peak→End)']
            
            summary_rows = []
            for m, label in zip(metrics, metric_labels):
                row = {'Metric': label}
                for gs in group_summaries:
                    mean = gs.metrics_mean.get(m, np.nan)
                    sem = gs.metrics_sem.get(m, np.nan)
                    row[f'{gs.name} Mean'] = round(mean, 3) if not np.isnan(mean) else np.nan
                    row[f'{gs.name} SEM'] = round(sem, 3) if not np.isnan(sem) else np.nan
                stat = metric_stats.get(m, {})
                p_val = stat.get('p_value', np.nan)
                row['p-value'] = round(p_val, 4) if not np.isnan(p_val) else np.nan
                row['Significance'] = stat.get('stars', 'ns')
                summary_rows.append(row)
            summary_df = pd.DataFrame(summary_rows)

            # --- Sheet 3: Sample Details ---
            detail_rows = []
            for g_name, samples in processed_data.items():
                results = all_sample_results.get(g_name, [])
                for s_idx, sample in enumerate(samples):
                    res = results[s_idx] if s_idx < len(results) else None
                    row = {
                        'Group': g_name,
                        'Sample ID': f'S{s_idx + 1}',
                        'Active': 'Yes' if sample.is_active else 'No',
                        'Baseline': round(res.baseline, 3) if res and not np.isnan(res.baseline) else np.nan,
                    }
                    
                    # Use ITT-specific labels
                    if d['is_itt']:
                        row['Nadir'] = round(res.peak_value, 3) if res and not np.isnan(res.peak_value) else np.nan
                        row['Nadir Below Base'] = round(res.peak_above_baseline, 3) if res and not np.isnan(res.peak_above_baseline) else np.nan
                        row['Time to Nadir'] = round(res.time_to_peak, 3) if res and not np.isnan(res.time_to_peak) else np.nan
                        row['AUC (inverted)'] = round(res.auc, 3) if res and not np.isnan(res.auc) else np.nan
                        row['ROC Fall'] = round(res.roc_up, 3) if res and not np.isnan(res.roc_up) else np.nan
                        row['ROC Recovery'] = round(res.roc_down, 3) if res and not np.isnan(res.roc_down) else np.nan
                        row['Drop at t=15'] = round(res.early_drop, 3) if res and res.early_drop is not None and not np.isnan(res.early_drop) else np.nan
                        row['ROC to t=15'] = round(res.roc_to_early, 3) if res and res.roc_to_early is not None and not np.isnan(res.roc_to_early) else np.nan
                    else:
                        row['Peak'] = round(res.peak_value, 3) if res and not np.isnan(res.peak_value) else np.nan
                        row['Peak Above Base'] = round(res.peak_above_baseline, 3) if res and not np.isnan(res.peak_above_baseline) else np.nan
                        row['Time to Peak'] = round(res.time_to_peak, 3) if res and not np.isnan(res.time_to_peak) else np.nan
                        row['AUC'] = round(res.auc, 3) if res and not np.isnan(res.auc) else np.nan
                        row['ROC Up'] = round(res.roc_up, 3) if res and not np.isnan(res.roc_up) else np.nan
                        row['ROC Down'] = round(res.roc_down, 3) if res and not np.isnan(res.roc_down) else np.nan
                    
                    detail_rows.append(row)
            detail_df = pd.DataFrame(detail_rows)

            # --- Sheet 4: Raw Data + exclusion mask ---
            raw_rows = []
            mask_rows = []
            for g_name, samples in processed_data.items():
                for s_idx, sample in enumerate(samples):
                    row = {'Group': g_name, 'Sample ID': f'S{s_idx + 1}'}
                    mask_row = []
                    for i, tp in enumerate(time_points):
                        row[f't={int(tp)}'] = sample.values[i]
                        mask_row.append(i in sample.excluded_cells)
                    raw_rows.append(row)
                    mask_rows.append(mask_row)
            raw_df = pd.DataFrame(raw_rows)
            mask_df = pd.DataFrame(mask_rows)

            # --- Sheet 5: Statistical Tests ---
            stats_tests = {}
            if anova_res is not None:
                stats_tests['Two-Way RM ANOVA'] = anova_res
            for m, label in zip(metrics, metric_labels):
                stat = metric_stats.get(m, {})
                if 'full_table' in stat and isinstance(stat['full_table'], pd.DataFrame):
                    stats_tests[label] = stat['full_table']
                elif stat:
                    stats_tests[label] = pd.DataFrame([{
                        'Test': stat.get('test', ''),
                        'p-value': stat.get('p_value', np.nan),
                        'Significance': stat.get('stars', 'ns')
                    }])

            export_to_excel(file_path, data={
                'curve_data': curve_df,
                'summary_stats': summary_df,
                'sample_details': detail_df,
                'raw_data': raw_df,
                'raw_data_mask': mask_df,
                'stats_tests': stats_tests
            }, is_itt=d.get('is_itt', False))

            QMessageBox.information(self, "Export Successful", f"Results saved to:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"An error occurred during export:\n{str(e)}")

    def clear_all(self):
        while self.input_panel.groups:
            self.input_panel.remove_group(self.input_panel.groups[0])
        self.plot_widget.ax.clear()
        self.plot_widget.canvas.draw()
        self.results_widget.summary_table.setRowCount(0)
        self.results_widget.detailed_table.setRowCount(0)
        self.results_widget.anova_text.clear()

    def show_about(self):
        QMessageBox.about(self, "About TolQuant", 
                          "TolQuant — Tolerance Test Analyzer\n\n"
                          "Built for analyzing GTT/ITT data with scientific rigor.\n"
                          "Uses Two-way RM ANOVA and post-hoc tests.\n\n"
                          "Version: 1.0.0\n"
                          "Author: Dr. Robert Hauffe\n"
                          "Created: March 31, 2026")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
