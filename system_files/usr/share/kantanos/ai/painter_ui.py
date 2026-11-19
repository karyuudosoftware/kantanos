"""The Picture helper's "Make a picture" and "Fix a photo" tabs (engine and models: painter.py)."""
import glob
import os
import random
import tempfile
import threading

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QFont, QIcon, QImageReader, QPixmap
from PySide6.QtWidgets import (QComboBox, QFileDialog, QHBoxLayout, QInputDialog, QLabel, QMessageBox,
                               QPlainTextEdit, QProgressBar, QPushButton, QSizePolicy, QVBoxLayout, QWidget)

import painter

TITLE = "Picture helper"
MADE = os.path.join(os.path.expanduser("~/Pictures"), "Made with AI")
NOT_FAMILY = "Let's keep pictures family-friendly: try describing something else."


class Bridge(QObject):
    step = Signal(str, int, int)        # what, step, steps
    done = Signal(str, object, str)      # job, result, error


def has_gpu():
    return bool(glob.glob("/dev/dri/renderD*")) and not os.environ.get("KANTAN_SD_CPU")


def big_button(text, icon, slot):
    b = QPushButton(QIcon.fromTheme(icon), text)
    b.setMinimumHeight(48)
    b.setAccessibleName(text)
    b.clicked.connect(slot)
    return b


class Studio(QWidget):
    """What both tabs share: getting the engine ready, running it, showing progress."""

    def __init__(self, say):
        super().__init__()
        self.say = say
        self.bridge = Bridge(self)
        self.bridge.step.connect(self.on_step)
        self.bridge.done.connect(self.on_done)
        self.stop = threading.Event()
        self.busy = False
        self.seed = random.randint(1, 2**31)
        self.bar = QProgressBar()
        self.bar.hide()
        self.stop_b = big_button("Stop", "process-stop", lambda: self.stop.set())
        self.stop_b.hide()

    # -- readiness --
    def ready(self):
        if not painter.engine_ready():
            self.say("The picture engine isn't installed on this PC.")
            return False
        if painter.models_ready():
            return True
        need = painter.TOTAL_GB + 1
        if painter.free_disk_gb() < need:
            self.say(f"Making pictures needs {need:.0f} GB of free space for its one-time download; there isn't "
                     "enough. Free some space (Files can show what's big) and try again.")
            return False
        ok = QMessageBox.question(
            self, TITLE, f"Making and fixing pictures runs on this PC and needs a one-time download of about "
            f"{painter.TOTAL_GB} GB (the FLUX.2 klein picture model, free to use). Your words and photos are never "
            f"sent anywhere.\n\nDownload it now?")
        if ok != QMessageBox.StandardButton.Yes:
            return False
        self.start("download", painter.download, lambda got, total: self.bridge.step.emit(
            f"Downloading the picture model: {got / 1e9:.1f} of {total / 1e9:.1f} GB", int(got >> 20),
            int(total >> 20)), self.stop)
        return False

    def start(self, job, fn, *args):
        self.busy = True
        self.stop.clear()
        self.set_busy(True)
        self.bar.show()
        self.bar.setRange(0, 0)
        self.stop_b.show()

        def work():
            try:
                self.bridge.done.emit(job, fn(*args), "")
            except InterruptedError:
                self.bridge.done.emit(job, None, "stopped")
            except Exception as e:
                self.bridge.done.emit(job, None, str(e) or e.__class__.__name__)
        threading.Thread(target=work, daemon=True).start()

    def draw(self, job, prompt, out, size, reference=None):
        cmd = painter.command(prompt, out, size, self.seed, reference=reference, cpu=not has_gpu())

        def work():
            if has_gpu():
                painter.free_video_memory()
            steps = int(cmd[cmd.index("--steps") + 1])

            def progress(i, n):
                if n == steps:
                    self.bridge.step.emit(f"Drawing: step {i} of {n}…", i, n)
                else:
                    self.bridge.step.emit("Getting ready (the first picture takes longest)…", 0, 0)
            return painter.run(cmd, progress, self.stop)
        self.say("Getting ready…" if has_gpu() else
                 "This PC has no graphics card the picture engine can use, so this takes several minutes…")
        self.start(job, work)

    def on_step(self, text, i, n):
        self.say(text)
        if n:
            self.bar.setRange(0, n)
            self.bar.setValue(i)
        else:
            self.bar.setRange(0, 0)

    def on_done(self, job, value, error):
        self.busy = False
        self.set_busy(False)
        self.bar.hide()
        self.stop_b.hide()
        if job == "download":
            return self.say("Stopped. It carries on from where it was next time." if error == "stopped" else
                            f"The download didn't finish ({error})." if error else
                            "The picture model is ready. Press the button again.")
        if error == "stopped":
            return self.say("Stopped.")
        if error:
            return self.say(f"That didn't work: {error}")
        self.finished(job, value)

    def set_busy(self, on):
        pass

    def finished(self, job, value):
        pass


def show_image(label, path):
    r = QImageReader(path)
    r.setAutoTransform(True)
    img = r.read()
    if img.isNull():
        return
    label.full = QPixmap.fromImage(img)
    label.setPixmap(label.full.scaled(label.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation))


def picture_label(text):
    lab = QLabel(text)
    lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lab.setWordWrap(True)
    lab.setMinimumSize(420, 360)
    lab.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    lab.full = None
    lab.resizeEvent = lambda ev: lab.full and lab.setPixmap(lab.full.scaled(
        lab.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
    return lab


class MakeTab(Studio):
    def __init__(self, say):
        super().__init__(say)
        lay = QVBoxLayout(self)
        self.words = QPlainTextEdit()
        self.words.setPlaceholderText("Describe the picture you'd like, e.g. “a lighthouse on a cliff at sunset, "
                                      "with seagulls”")
        self.words.setMaximumHeight(110)
        self.words.setAccessibleName("Describe the picture")
        lay.addWidget(self.words)
        row = QHBoxLayout()
        self.style = QComboBox()
        for k, name in (("", "Any style"), ("photo", "Photo"), ("watercolour", "Watercolour"), ("cartoon", "Cartoon"),
                        ("oil", "Oil painting"), ("pencil", "Pencil sketch"), ("storybook", "Storybook"),
                        ("3d", "3D"), ("anime", "Anime")):
            self.style.addItem(name, k)
        self.shape = QComboBox()
        for k, name in (("square", "Square"), ("wide", "Wide"), ("tall", "Tall")):
            self.shape.addItem(name, k)
        for c, n in ((self.style, "Style"), (self.shape, "Shape")):
            c.setMinimumHeight(48)
            c.setAccessibleName(n)
        self.make_b = big_button("Make it", "draw-brush", lambda: self.make(new_seed=False))
        self.make_b.setDefault(True)
        row.addWidget(QLabel("Style"))
        row.addWidget(self.style)
        row.addWidget(QLabel("Shape"))
        row.addWidget(self.shape)
        row.addStretch(1)
        row.addWidget(self.make_b)
        lay.addLayout(row)
        self.pic = picture_label("Your picture appears here. Each one is kept in Pictures › Made with AI.")
        lay.addWidget(self.pic, 1)
        lay.addWidget(self.bar)
        after = QHBoxLayout()
        self.again_b = big_button("Another one", "view-refresh", lambda: self.make(new_seed=True))
        self.open_b = big_button("Show in Files", "folder-pictures", self.show_folder)
        for b in (self.again_b, self.open_b):
            b.setEnabled(False)
            after.addWidget(b)
        after.addStretch(1)
        after.addWidget(self.stop_b)
        lay.addLayout(after)
        self.last = None

    def make(self, new_seed):
        words = self.words.toPlainText().strip()
        if not words:
            return self.say("Type what the picture should show first.")
        if not painter.family_friendly(words):
            return self.say(NOT_FAMILY)
        if not self.ready():
            return
        if new_seed:
            self.seed = random.randint(1, 2**31)
        style = painter.STYLES[self.style.currentData()]
        prompt = words + (f", {style}" if style else "")
        os.makedirs(MADE, exist_ok=True)
        self.words_used = words
        self.draw("make", prompt, painter.picture_name(MADE, words), painter.SIZES[self.shape.currentData()])

    def set_busy(self, on):
        for b in (self.make_b, self.again_b, self.style, self.shape):
            b.setEnabled(not on)
        self.again_b.setEnabled(not on and self.last is not None)

    def finished(self, job, path):
        painter.mark_made_with_ai(path, self.words_used)
        self.last = path
        show_image(self.pic, path)
        self.again_b.setEnabled(True)
        self.open_b.setEnabled(True)
        self.say(f"Kept in Pictures › Made with AI as “{os.path.basename(path)}”. "
                 "“Another one” draws a different version.")

    def show_folder(self):
        import subprocess
        subprocess.Popen(["dolphin", "--select", self.last or MADE], start_new_session=True)


class FixTab(Studio):
    def __init__(self, say):
        super().__init__(say)
        lay = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(big_button("Open a photo…", "document-open", self.choose))
        top.addStretch(1)
        note = QLabel("Your photo itself is never changed: the fixed one is saved beside it.")
        note.setStyleSheet("color: gray")
        top.addWidget(note)
        lay.addLayout(top)
        pics = QHBoxLayout()
        self.before = picture_label("Open a photo to fix: an old, scratched or faded one, or one with something "
                                    "in it you'd rather wasn't there.")
        self.after = picture_label("")
        pics.addWidget(self.before, 1)
        pics.addWidget(self.after, 1)
        lay.addLayout(pics, 1)
        lay.addWidget(self.bar)
        acts = QHBoxLayout()
        self.acts = [big_button("Tidy an old photo", "edit-clear", lambda: self.fix("tidy")),
                     big_button("Add colour", "color-management", lambda: self.fix("colour")),
                     big_button("Remove something…", "edit-delete", lambda: self.fix("remove")),
                     big_button("Change it…", "document-edit", lambda: self.fix("change"))]
        for b in self.acts:
            b.setEnabled(False)
            acts.addWidget(b)
        acts.addStretch(1)
        acts.addWidget(self.stop_b)
        lay.addLayout(acts)
        keep = QHBoxLayout()
        self.again_b = big_button("Try again", "view-refresh", lambda: self.fix(self.last_job, again=True))
        self.keep_b = big_button("Keep this", "document-save", self.keep)
        self.again_b.setEnabled(False)
        self.keep_b.setEnabled(False)
        keep.addStretch(1)
        keep.addWidget(self.again_b)
        keep.addWidget(self.keep_b)
        lay.addLayout(keep)
        self.photo = self.result = self.last_job = self.last_prompt = None

    def choose(self):
        p, _ = QFileDialog.getOpenFileName(self, "Open a photo", os.path.expanduser("~/Pictures"),
                                           "Photos (*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff);;All files (*)")
        if p:
            self.open(p)

    def open(self, p):
        self.photo, self.result = p, None
        show_image(self.before, p)
        self.after.clear()
        self.after.full = None
        self.after.setText("")
        for b in self.acts:
            b.setEnabled(True)
        self.keep_b.setEnabled(False)
        self.again_b.setEnabled(False)

    def fix(self, job, again=False):
        if not self.photo or not job:
            return
        if again:
            self.seed = random.randint(1, 2**31)
            prompt = self.last_prompt
        elif job == "remove":
            what, ok = QInputDialog.getText(self, "Remove something", "What should be taken out of the photo?\n"
                                            "(e.g. “the man on the left”, “the lamp post”, “the date in the corner”)")
            if not ok or not what.strip():
                return
            prompt = painter.FIXES["remove"].format(what=what.strip())
        elif job == "change":
            what, ok = QInputDialog.getText(self, "Change it", "How should the photo change?\n"
                                            "(e.g. “make it look like a snowy winter day”, “make the sky blue”)")
            if not ok or not what.strip():
                return
            prompt = what.strip() + ". Keep everything else exactly the same."
        else:
            prompt = painter.FIXES[job]
        if not painter.family_friendly(prompt):
            return self.say(NOT_FAMILY)
        if not self.ready():
            return
        self.last_job, self.last_prompt = job, prompt
        r = QImageReader(self.photo)
        r.setAutoTransform(True)
        ref = os.path.join(tempfile.gettempdir(), f"kantanos-fix-{os.getuid()}.png")
        img = r.read()
        if img.isNull():
            return self.say("This photo can't be opened.")
        img.save(ref)                       # turned the right way up, so the result is too
        size = painter.edit_size(img.width(), img.height())
        out = os.path.join(tempfile.gettempdir(), f"kantanos-fixed-{os.getuid()}-{random.randint(0, 1 << 30)}.png")
        self.draw(job, prompt, out, size, reference=ref)

    def set_busy(self, on):
        for b in self.acts + [self.again_b, self.keep_b]:
            b.setEnabled(not on and (b not in (self.again_b, self.keep_b) or self.result is not None))

    def finished(self, job, path):
        self.result = path
        show_image(self.after, path)
        self.keep_b.setEnabled(True)
        self.again_b.setEnabled(True)
        self.say("Here it is, on the right. “Keep this” saves it beside the original; “Try again” makes another "
                 "version.")

    def keep(self):
        if not self.result:
            return
        folder = os.path.dirname(self.photo)
        if not os.access(folder, os.W_OK):
            folder = MADE
            os.makedirs(folder, exist_ok=True)
        base = os.path.splitext(os.path.basename(self.photo))[0] + " (fixed)"
        dest = painter.picture_name(folder, base)
        from PySide6.QtGui import QImage
        img = QImage(self.result)
        img.setText("Description", f"Changed with AI on KantanOS (FLUX.2 klein): {self.last_prompt}")
        img.save(dest)
        where = folder.replace(os.path.expanduser("~"), "Home").strip("/").replace("/", " › ")
        self.say(f"Kept as “{os.path.basename(dest)}” in {where}.")


def self_test():
    assert painter.self_test()
    from PySide6.QtWidgets import QApplication
    import sys
    _a = QApplication.instance() or QApplication(sys.argv)
    said = []
    m = MakeTab(said.append)
    m.words.setPlainText("a naked man")
    m.make(False)
    assert said[-1] == NOT_FAMILY, said
    f = FixTab(said.append)
    assert not f.acts[0].isEnabled()
    return True
