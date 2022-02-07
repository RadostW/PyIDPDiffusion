#!/usr/bin/python

import sys, re, os
from PyQt5 import QtGui
from PyQt5.QtWidgets import (
    QWidget,
    QApplication,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QTextEdit,
    QSpinBox,
    QProgressBar,
    QLineEdit,
    QShortcut,
)
from PyQt5.QtGui import (
    QPainter,
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QPen,
    QDoubleValidator,
    QKeySequence,
)
from PyQt5.QtCore import Qt

from qt_material import apply_stylesheet

import chain_description_parser
import generator_interface
import ensemble_diffusion

import numpy as np


class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._mapping = {}

    def add_mapping(self, pattern, pattern_format):
        self._mapping[pattern] = pattern_format

    def highlightBlock(self, text_block):
        for pattern, fmt in self._mapping.items():
            for match in re.finditer(pattern, text_block):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)


class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def on_larger(self):
        self.density_scale = self.density_scale + 1
        self.on_resize()

    def on_smaller(self):
        self.density_scale = self.density_scale - 1
        self.on_resize()
        
    def on_resize(self):
        extra = {"density_scale": f"{self.density_scale}"}
        apply_stylesheet(self.global_app, theme="dark_amber.xml", extra=extra)    

    def initUI(self):

        # Window layout
        outer_layout = QHBoxLayout()
        self.setLayout(outer_layout)
        self.setWindowTitle("Disordered protein diffusion")
        
        self.shortcut_larger = QShortcut(QKeySequence("Ctrl++"), self)
        self.shortcut_larger.activated.connect(self.on_larger)
        
        self.shortcut_larger = QShortcut(QKeySequence("Ctrl+-"), self)
        self.shortcut_larger.activated.connect(self.on_smaller)

        # Outer layout
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        outer_layout.addLayout(left_layout)
        outer_layout.addLayout(right_layout)

        #
        # Left column
        #
        left_layout.addWidget(QLabel("Edit sequence (indicate ordered regions with square braces)"))

        highlighter = Highlighter()
        self.highlighter = highlighter  # App needs to own the object

        brace_format = QTextCharFormat()
        brace_format.setBackground(QColor(os.environ.get("QTMATERIAL_PRIMARYCOLOR")))
        brace_format.setForeground(QColor(os.environ.get("QTMATERIAL_SECONDARYCOLOR")))
        brace_pattern = r"\[[A-Z]*\]"
        highlighter.add_mapping(brace_pattern, brace_format)

        illegal_char_format = QTextCharFormat()
        illegal_char_format.setBackground(QColor("#600"))
        illegal_char_pattern = r"[^A-Z\s[\]]"
        highlighter.add_mapping(illegal_char_pattern, illegal_char_format)

        sequence_editor = QTextEdit(
            "DISORDEREDFRAGMENT[ORDEREDFRAGMENT]DISORDEREDFRAGMENT[ORDERED]"
        )
        highlighter.setDocument(sequence_editor.document())
        self.sequence_editor = sequence_editor
        sequence_editor.textChanged.connect(self.userChangedText)
        left_layout.addWidget(sequence_editor)

        left_layout.addWidget(QLabel("Environment settings"))

        self.onlyDouble = QDoubleValidator()

        constants_layout = QHBoxLayout()

        temperature_layout = QVBoxLayout()
        temperature_layout.addWidget(QLabel("Temperature [K]"))
        temperature_edit = QLineEdit("300.0")
        self.temperature_edit = temperature_edit
        temperature_edit.setValidator(self.onlyDouble)
        temperature_layout.addWidget(temperature_edit)
        constants_layout.addLayout(temperature_layout)

        viscosity_layout = QVBoxLayout()
        viscosity_layout.addWidget(QLabel("Viscosity [cP]"))
        viscosity_edit = QLineEdit("1.0")
        self.viscosity_edit = viscosity_edit
        viscosity_edit.setValidator(self.onlyDouble)
        viscosity_layout.addWidget(viscosity_edit)
        constants_layout.addLayout(viscosity_layout)

        left_layout.addLayout(constants_layout)

        left_layout.addWidget(QLabel("Ensemble size"))

        left_ensemble_size = QSpinBox()
        self.left_ensemble_size = left_ensemble_size
        left_ensemble_size.setMaximum(5000)
        left_ensemble_size.setMinimum(1)
        left_ensemble_size.setValue(30)
        left_layout.addWidget(left_ensemble_size)

        compute_button = QPushButton("Compute diffusion")
        self.compute_button = compute_button
        compute_button.clicked.connect(self.userClickedCompute)
        left_layout.addWidget(compute_button)

        progress_bar = QProgressBar()
        left_layout.addWidget(progress_bar)
        self.progress_bar = progress_bar

        #
        # Right column
        #
        right_layout.addWidget(QLabel("Parsed sequence preview"))
        right_canvas = QLabel("_")
        screen = QApplication.primaryScreen()
        right_pixmap = QtGui.QPixmap(
            screen.size().width() // 2, screen.size().height() // 3
        )
        right_canvas.setPixmap(right_pixmap)
        right_layout.addWidget(right_canvas)
        self.right_canvas = right_canvas

        right_text_display = QPlainTextEdit("... waiting for engine ...")
        self.right_text_display = right_text_display
        right_text_display.setReadOnly(True)
        right_layout.addWidget(QLabel("Computation results"))
        right_layout.addWidget(right_text_display)

        painter = QtGui.QPainter(right_canvas.pixmap())
        p = painter.pen()
        p.setWidth(10)
        p.setColor(QtGui.QColor("#666666"))
        painter.setPen(p)
        w = right_canvas.pixmap().width()
        h = right_canvas.pixmap().height()
        painter.fillRect(
            0, 0, w, h, QColor(os.environ.get("QTMATERIAL_SECONDARYCOLOR"))
        )
        painter.drawEllipse(10, 10, 800, 600)
        painter.end()
        right_canvas.update()

    def userClickedCompute(self):
        current_text = self.sequence_editor.toPlainText()
        right_text_display = self.right_text_display

        parsed = chain_description_parser.parse(current_text)
        (bead_steric_sizes, bead_hydrodynamic_sizes, bead_types, total_mass) = (
            parsed["bead_steric_sizes"],
            parsed["bead_hydrodynamic_sizes"],
            parsed["bead_types"],
            parsed["total_mass"],
        )

        ensemble_size = self.left_ensemble_size.value()

        right_text_display.setPlainText("")  # reset contents
        right_text_display.appendPlainText(
            f"Generating ensemble of size {ensemble_size} with {len(bead_steric_sizes)} beads in each chain."
        )
        right_text_display.appendPlainText("")

        def getChain():
            return np.array(
                [
                    float(x)
                    for x in generator_interface.getChainPython(
                        str(bead_steric_sizes)
                    ).split()
                ]
            ).reshape(-1, 3)

        ensemble = list()
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(2 * ensemble_size)
        for x in range(ensemble_size):
            ensemble.append(getChain())
            self.progress_bar.setValue(x)

        ensemble = np.array(ensemble)

        rh = ensemble_diffusion.rh(ensemble, bead_hydrodynamic_sizes)

        self.progress_bar.setValue(int(ensemble_size))

        rh_dist = list()
        batches = max(min(ensemble_size // 2, 20), 1)
        for i in range(batches):
            rh_dist.append(
                ensemble_diffusion.rh(ensemble[i::batches], bead_hydrodynamic_sizes)
            )
            self.progress_bar.setValue(int(ensemble_size + ensemble_size * i / batches))

        sigma_rh = np.std(rh_dist)
        if len(rh_dist) < 3:
            sigma_rh = float("nan")

        right_text_display.appendPlainText(f"Computed effective, diffusive hydrodynamic radius is:")
        right_text_display.appendPlainText(f"R_h = {rh:.4e} [Ang]")
        right_text_display.appendPlainText(f"(sampling error about {sigma_rh/rh:.4%}).")
        right_text_display.appendPlainText("")

        kb = 1.38e-23

        diffusion_coefficient = (
            kb
            * float(self.temperature_edit.text())
            / (1e-10 * rh * 6 * np.pi * 0.01 * float(self.viscosity_edit.text()))
        )

        right_text_display.appendPlainText(f"Computed diffusion coefficient is:")
        right_text_display.appendPlainText(f"D = {diffusion_coefficient:.4e} [m^2/s]")
        right_text_display.appendPlainText("")
        right_text_display.appendPlainText(f"Total mass is:") 
        right_text_display.appendPlainText(f"M = {total_mass:.4e} [Da]")

        self.progress_bar.setValue(int(2 * ensemble_size))

    def userChangedText(self):
        current_text = self.sequence_editor.toPlainText()

        parsed = chain_description_parser.parse(current_text)
        (bead_sizes, bead_types) = (parsed["bead_steric_sizes"], parsed["bead_types"])
        self.paintParsedSequence(bead_sizes, bead_types)

        # right_canvas = self.right_canvas
        # self.paintParsedSequence(np.array([1,1,1,3,1,1,1]),np.array([1,1,1,2,1,1,1]))

        # w = right_canvas.pixmap().width()
        # h = right_canvas.pixmap().height()
        # painter = QtGui.QPainter(right_canvas.pixmap())
        # painter.fillRect(0,0,w,h,QColor(current_text))
        # painter.end()
        # right_canvas.update()
        # qp.setPen(QColor(168, 34, 3))
        # qp.setFont(QFont('Decorative', 10))
        # qp.drawText(event.rect(), Qt.AlignCenter, self.text)

    def paintParsedSequence(self, bead_sizes, bead_types):

        right_canvas = self.right_canvas
        w = right_canvas.pixmap().width()
        h = right_canvas.pixmap().height()
        painter = QtGui.QPainter(right_canvas.pixmap())
        painter.fillRect(
            0, 0, w, h, QColor(os.environ.get("QTMATERIAL_SECONDARYCOLOR"))
        )

        locations = np.cumsum(2 * bead_sizes) - bead_sizes
        scale = np.sum(2 * bead_sizes)
        margin = 0.05  # percent
        scale = scale * (1.0 + 2.0 * margin)
        bead_colors = {
            1: QColor(os.environ.get("QTMATERIAL_SECONDARYCOLOR")),
            2: QColor(os.environ.get("QTMATERIAL_PRIMARYCOLOR")),
        }
        bead_borders = {
            1: QColor(os.environ.get("QTMATERIAL_PRIMARYCOLOR")),
            2: QColor(os.environ.get("QTMATERIAL_SECONDARYCOLOR")),
        }
        for location, size, bead_type in zip(locations, bead_sizes, bead_types):
            painter.setBrush(bead_colors[bead_type])
            pen = QPen(bead_borders[bead_type])
            pen.setWidth(5)
            painter.setPen(pen)
            x_cent = w * (location / scale + margin)
            y_cent = h / 2
            x_size = w * size / scale
            y_size = w * size / scale
            painter.drawEllipse(
                int(x_cent - x_size),
                int(y_cent - y_size),
                int(2 * x_size),
                int(2 * y_size),
            )

        painter.end()
        right_canvas.update()

density_scale = 20

def main():
    app = QApplication(sys.argv)

    extra = {"density_scale": f"{density_scale}"}
    apply_stylesheet(app, theme="dark_amber.xml", extra=extra)

    window = MyApp()
    window.density_scale = density_scale
    window.global_app = app
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
