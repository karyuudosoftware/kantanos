"""mpv inside a Qt window: a small ctypes binding to libmpv's render API and a QOpenGLWidget
that draws the video, so the guide and info bar can sit on top of the picture."""
import ctypes
import ctypes.util
import locale

from PySide6.QtCore import Signal
from PySide6.QtGui import QOpenGLContext
from PySide6.QtOpenGLWidgets import QOpenGLWidget

_lib = None


def lib():
    global _lib
    if _lib is None:
        name = ctypes.util.find_library("mpv") or "libmpv.so.2"
        _lib = ctypes.CDLL(name)
        _lib.mpv_create.restype = ctypes.c_void_p
        _lib.mpv_initialize.argtypes = [ctypes.c_void_p]
        _lib.mpv_set_option_string.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
        _lib.mpv_set_property_string.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
        _lib.mpv_get_property_string.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        _lib.mpv_get_property_string.restype = ctypes.c_void_p
        _lib.mpv_free.argtypes = [ctypes.c_void_p]
        _lib.mpv_command.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_char_p)]
        _lib.mpv_command_async.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_char_p)]
        _lib.mpv_observe_property.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.c_char_p, ctypes.c_int]
        _lib.mpv_wait_event.argtypes = [ctypes.c_void_p, ctypes.c_double]
        _lib.mpv_wait_event.restype = ctypes.POINTER(MpvEvent)
        _lib.mpv_set_wakeup_callback.argtypes = [ctypes.c_void_p, WAKEUP, ctypes.c_void_p]
        _lib.mpv_terminate_destroy.argtypes = [ctypes.c_void_p]
        _lib.mpv_render_context_create.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p,
                                                   ctypes.POINTER(RenderParam)]
        _lib.mpv_render_context_render.argtypes = [ctypes.c_void_p, ctypes.POINTER(RenderParam)]
        _lib.mpv_render_context_set_update_callback.argtypes = [ctypes.c_void_p, UPDATE, ctypes.c_void_p]
        _lib.mpv_render_context_report_swap.argtypes = [ctypes.c_void_p]
        _lib.mpv_render_context_free.argtypes = [ctypes.c_void_p]
        _lib.mpv_error_string.argtypes = [ctypes.c_int]
        _lib.mpv_error_string.restype = ctypes.c_char_p
    return _lib


class MpvEvent(ctypes.Structure):
    _fields_ = [("event_id", ctypes.c_int), ("error", ctypes.c_int), ("reply_userdata", ctypes.c_uint64),
                ("data", ctypes.c_void_p)]


class EventProperty(ctypes.Structure):
    _fields_ = [("name", ctypes.c_char_p), ("format", ctypes.c_int), ("data", ctypes.c_void_p)]


class EventEndFile(ctypes.Structure):
    _fields_ = [("reason", ctypes.c_int), ("error", ctypes.c_int)]


class RenderParam(ctypes.Structure):
    _fields_ = [("type", ctypes.c_int), ("data", ctypes.c_void_p)]


GET_PROC = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p)


class GLInitParams(ctypes.Structure):
    _fields_ = [("get_proc_address", GET_PROC), ("get_proc_address_ctx", ctypes.c_void_p)]


class GLFbo(ctypes.Structure):
    _fields_ = [("fbo", ctypes.c_int), ("w", ctypes.c_int), ("h", ctypes.c_int), ("internal_format", ctypes.c_int)]


WAKEUP = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
UPDATE = ctypes.CFUNCTYPE(None, ctypes.c_void_p)

# libmpv constants
FMT_STRING, FMT_FLAG, FMT_INT64, FMT_DOUBLE = 1, 3, 4, 5
EV_SHUTDOWN, EV_END_FILE, EV_FILE_LOADED, EV_PLAYBACK_RESTART, EV_PROPERTY_CHANGE = 1, 7, 8, 21, 22
END_EOF, END_ERROR = 0, 4
R_API_TYPE, R_GL_INIT, R_GL_FBO, R_FLIP_Y = 1, 2, 3, 4


_egl = None


def _proc_address(_ctx, name):
    """OpenGL function addresses for mpv: from Qt, else straight from EGL/GLX."""
    global _egl
    ctx = QOpenGLContext.currentContext()
    if ctx is not None:
        try:
            addr = ctx.getProcAddress(name)
            if addr:
                return int(addr)
        except (TypeError, ValueError):
            pass
    if _egl is None:
        _egl = []
        for libname, fn in (("EGL", "eglGetProcAddress"), ("GL", "glXGetProcAddressARB")):
            path = ctypes.util.find_library(libname)
            if path:
                f = getattr(ctypes.CDLL(path), fn)
                f.restype, f.argtypes = ctypes.c_void_p, [ctypes.c_char_p]
                _egl.append(f)
    for f in _egl:
        addr = f(name)
        if addr:
            return addr
    return 0


_get_proc = GET_PROC(_proc_address)


class MpvWidget(QOpenGLWidget):
    """Plays one stream at a time. Signals arrive on the Qt thread."""
    wakeup = Signal()
    redraw = Signal()
    playing = Signal()                  # first picture/sound of a stream
    ended = Signal(bool)                # True when it ended because of an error
    changed = Signal(str, object)       # an observed property changed

    def __init__(self, parent=None, options=None):
        super().__init__(parent)
        locale.setlocale(locale.LC_NUMERIC, "C")       # libmpv insists on it
        self.m = lib()
        self.h = self.m.mpv_create()
        if not self.h:
            raise RuntimeError("libmpv could not start")
        opts = {"vo": "libmpv", "hwdec": "auto-copy-safe", "keep-open": "no", "idle": "yes",
                "input-default-bindings": "no", "osc": "no", "terminal": "no", "cache": "yes",
                "demuxer-max-bytes": "64MiB", "network-timeout": "15", "deinterlace": "auto",
                "audio-client-name": "KantanOS TV", "ytdl": "no"}
        opts.update(options or {})
        for k, v in opts.items():
            self.m.mpv_set_option_string(self.h, k.encode(), str(v).encode())
        if self.m.mpv_initialize(self.h) < 0:
            raise RuntimeError("libmpv could not start")
        self.ctx = None
        self._observed = {}
        self._wake_cb = WAKEUP(lambda _d: self.wakeup.emit())
        self._update_cb = UPDATE(lambda _d: self.redraw.emit())
        self.wakeup.connect(self._events)
        self.redraw.connect(self.update)
        self.m.mpv_set_wakeup_callback(self.h, self._wake_cb, None)

    # ---- OpenGL -----------------------------------------------------------------------------
    def initializeGL(self):
        init = GLInitParams(_get_proc, None)
        api = ctypes.c_char_p(b"opengl")
        params = (RenderParam * 3)(RenderParam(R_API_TYPE, ctypes.cast(api, ctypes.c_void_p)),
                                    RenderParam(R_GL_INIT, ctypes.cast(ctypes.pointer(init), ctypes.c_void_p)),
                                    RenderParam(0, None))
        ctx = ctypes.c_void_p()
        err = self.m.mpv_render_context_create(ctypes.byref(ctx), self.h, params)
        if err < 0:
            raise RuntimeError("video drawing failed: " + self.m.mpv_error_string(err).decode())
        self.ctx = ctx
        self.m.mpv_render_context_set_update_callback(self.ctx, self._update_cb, None)

    def paintGL(self):
        if not self.ctx:
            return
        r = self.devicePixelRatioF()
        fbo = GLFbo(int(self.defaultFramebufferObject()), int(self.width() * r), int(self.height() * r), 0)
        flip = ctypes.c_int(1)
        params = (RenderParam * 3)(RenderParam(R_GL_FBO, ctypes.cast(ctypes.pointer(fbo), ctypes.c_void_p)),
                                    RenderParam(R_FLIP_Y, ctypes.cast(ctypes.pointer(flip), ctypes.c_void_p)),
                                    RenderParam(0, None))
        self.m.mpv_render_context_render(self.ctx, params)

    # ---- commands ---------------------------------------------------------------------------
    def command(self, *args):
        arr = (ctypes.c_char_p * (len(args) + 1))(*[str(a).encode() for a in args], None)
        return self.m.mpv_command(self.h, arr)

    def set(self, name, value):
        if isinstance(value, bool):
            value = "yes" if value else "no"
        return self.m.mpv_set_property_string(self.h, name.encode(), str(value).encode())

    def get(self, name):
        p = self.m.mpv_get_property_string(self.h, name.encode())
        if not p:
            return None
        try:
            return ctypes.string_at(p).decode("utf-8", "replace")
        finally:
            self.m.mpv_free(p)

    def observe(self, name, fmt=FMT_STRING):
        uid = len(self._observed) + 1
        self._observed[uid] = (name, fmt)
        self.m.mpv_observe_property(self.h, uid, name.encode(), fmt)

    def play(self, url, user_agent=None, referrer=None, start=None):
        self.set("user-agent", user_agent or "Mozilla/5.0 (X11; Linux x86_64) KantanOS-TV")
        self.set("referrer", referrer or "")
        opts = f"start={start}" if start else ""
        if opts:
            return self.command("loadfile", url, "replace", "-1", opts)
        return self.command("loadfile", url, "replace")

    def stop(self):
        self.command("stop")

    # ---- events -----------------------------------------------------------------------------
    def _events(self):
        while self.h:
            ev = self.m.mpv_wait_event(self.h, 0).contents
            if ev.event_id == 0:
                return
            if ev.event_id == EV_SHUTDOWN:
                return
            if ev.event_id == EV_PLAYBACK_RESTART:
                self.playing.emit()
            elif ev.event_id == EV_END_FILE and ev.data:
                end = ctypes.cast(ev.data, ctypes.POINTER(EventEndFile)).contents
                if end.reason in (END_EOF, END_ERROR):
                    self.ended.emit(end.reason == END_ERROR)
            elif ev.event_id == EV_PROPERTY_CHANGE and ev.data:
                p = ctypes.cast(ev.data, ctypes.POINTER(EventProperty)).contents
                val = None
                if p.data:
                    if p.format == FMT_STRING:
                        val = ctypes.cast(p.data, ctypes.POINTER(ctypes.c_char_p)).contents.value
                        val = val.decode("utf-8", "replace") if val else None
                    elif p.format == FMT_FLAG:
                        val = bool(ctypes.cast(p.data, ctypes.POINTER(ctypes.c_int)).contents.value)
                    elif p.format == FMT_DOUBLE:
                        val = ctypes.cast(p.data, ctypes.POINTER(ctypes.c_double)).contents.value
                    elif p.format == FMT_INT64:
                        val = ctypes.cast(p.data, ctypes.POINTER(ctypes.c_int64)).contents.value
                self.changed.emit(p.name.decode(), val)

    def close_player(self):
        if self.ctx:
            self.makeCurrent()
            self.m.mpv_render_context_free(self.ctx)
            self.ctx = None
            self.doneCurrent()
        if self.h:
            h, self.h = self.h, None
            self.m.mpv_terminate_destroy(h)
