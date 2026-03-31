from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, 
                             QPushButton, QFrame, QLabel, QSplitter)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Optional
from ..core.analyzer import GroupSummary

class PlotWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.group_summaries: List[GroupSummary] = []
        self.posthoc_results = {}
        self.test_type = "GTT"
        self.colors = ['#0072B2', '#D55E00', '#009E73', '#CC79A7'] # Colorblind friendly
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        
        # Left side: Controls
        self.controls_panel = QFrame()
        self.controls_panel.setFixedWidth(200)
        self.controls_layout = QVBoxLayout(self.controls_panel)
        
        self.controls_layout.addWidget(QLabel("Plot Settings"))
        
        self.error_bars_cb = QCheckBox("Error Bars")
        self.error_bars_cb.setChecked(True)
        self.error_bars_cb.stateChanged.connect(self.update_plot)
        self.controls_layout.addWidget(self.error_bars_cb)
        
        self.shaded_sem_cb = QCheckBox("Shaded SEM")
        self.shaded_sem_cb.stateChanged.connect(self.update_plot)
        self.controls_layout.addWidget(self.shaded_sem_cb)
        
        self.phase_ann_cb = QCheckBox("Phase Annotations")
        self.phase_ann_cb.stateChanged.connect(self.update_plot)
        self.controls_layout.addWidget(self.phase_ann_cb)
        
        self.copy_plot_btn = QPushButton("Copy Plot")
        self.copy_plot_btn.clicked.connect(self.copy_to_clipboard)
        self.controls_layout.addWidget(self.copy_plot_btn)
        
        self.controls_layout.addStretch()
        layout.addWidget(self.controls_panel)

        # Right side: Plot
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)
        layout.addWidget(plot_container)

        self.setLayout(layout)

    def update_data(self, group_summaries, test_type="GTT", unit="mM", is_itt=False):
        self.group_summaries = group_summaries
        self.test_type = test_type
        self.unit = unit
        self.is_itt = is_itt  # store it so update_plot can access it
        self.update_plot()

    def update_plot(self):
        self.ax.clear()
        if not self.group_summaries:
            self.canvas.draw()
            return

        is_itt = getattr(self, 'is_itt', False)

        # ITT-aware labels
        if is_itt:
            extreme_label = "Nadir"
            roc_first_label = "ROC Fall"   # baseline → nadir
            roc_second_label = "ROC Recovery"  # nadir → end
            extreme_marker = '^'  # pointing down for nadir
        else:
            extreme_label = "Peak"
            roc_first_label = "ROC Up"
            roc_second_label = "ROC Down"
            extreme_marker = 'v'  # pointing up for peak

        for i, gs in enumerate(self.group_summaries):
            color = self.colors[i % len(self.colors)]
            x = gs.time_points
            y = gs.values_mean
            yerr = gs.values_sem

            # Filter NaNs
            mask = ~np.isnan(y)
            x_plot = x[mask]
            y_plot = y[mask]
            yerr_plot = yerr[mask]

            if len(x_plot) == 0:
                continue

            # Main curve
            if self.error_bars_cb.isChecked():
                self.ax.errorbar(x_plot, y_plot, yerr=yerr_plot, label=gs.name,
                                color=color, fmt='-o', capsize=3)
            else:
                self.ax.plot(x_plot, y_plot, label=gs.name, color=color, marker='o')

            if self.shaded_sem_cb.isChecked():
                self.ax.fill_between(x_plot, y_plot - yerr_plot, y_plot + yerr_plot,
                                    color=color, alpha=0.2)

            # Phase annotations
            if self.phase_ann_cb.isChecked():
                if is_itt:
                    extreme_idx = np.argmin(y_plot)
                else:
                    extreme_idx = np.argmax(y_plot)

                x_extreme = x_plot[extreme_idx]
                y_extreme = y_plot[extreme_idx]
                x_start = x_plot[0]
                y_start = y_plot[0]
                x_end = x_plot[-1]
                y_end = y_plot[-1]

                # Mark the extreme point (peak or nadir)
                self.ax.plot(x_extreme, y_extreme, color=color,
                            marker=extreme_marker, markersize=10, zorder=5,
                            label=f"{gs.name} {extreme_label}")

                # ROC first phase: baseline → extreme
                # Draw as a dashed line with slope annotation
                if extreme_idx > 0:
                    self.ax.annotate(
                        "",
                        xy=(x_extreme, y_extreme),
                        xytext=(x_start, y_start),
                        arrowprops=dict(
                            arrowstyle="->",
                            color=color,
                            lw=1.5,
                            linestyle="dashed"
                        )
                    )
                    # Label the ROC first phase midpoint
                    mid_x = (x_start + x_extreme) / 2
                    mid_y = (y_start + y_extreme) / 2
                    self.ax.text(mid_x, mid_y, roc_first_label,
                                color=color, fontsize=7, ha='center',
                                bbox=dict(boxstyle='round,pad=0.2', 
                                        facecolor='white', alpha=0.6, edgecolor='none'))

                # ROC second phase: extreme → end
                if extreme_idx < len(x_plot) - 1:
                    self.ax.annotate(
                        "",
                        xy=(x_end, y_end),
                        xytext=(x_extreme, y_extreme),
                        arrowprops=dict(
                            arrowstyle="->",
                            color=color,
                            lw=1.5,
                            linestyle="dashed"
                        )
                    )
                    mid_x = (x_extreme + x_end) / 2
                    mid_y = (y_extreme + y_end) / 2
                    self.ax.text(mid_x, mid_y, roc_second_label,
                                color=color, fontsize=7, ha='center',
                                bbox=dict(boxstyle='round,pad=0.2',
                                        facecolor='white', alpha=0.6, edgecolor='none'))

                # Vertical dashed line dropping from extreme to x-axis for visual reference
                self.ax.axvline(x=x_extreme, color=color, linestyle=':', 
                                alpha=0.4, lw=1)

        # Axis labels
        if self.test_type == "ITT":
            ylabel = "Glucose (% baseline)"
        else:
            ylabel = f"Glucose ({self.unit})"

        self.ax.set_xlabel("Time (min)")
        self.ax.set_ylabel(ylabel)
        self.ax.legend(fontsize=8)
        self.ax.grid(True, linestyle='--', alpha=0.7)

        self.figure.tight_layout()
        self.canvas.draw()

    def copy_to_clipboard(self):
        from PyQt6.QtGui import QGuiApplication
        import io
        buf = io.BytesIO()
        self.figure.savefig(buf, format='png')
        from PyQt6.QtGui import QImage, QPixmap
        image = QImage.fromData(buf.getvalue())
        QGuiApplication.clipboard().setImage(image)
