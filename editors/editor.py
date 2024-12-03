from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
import sys
from copy import copy
from panda3d.core import *
from panda3d.bullet import *
from direct.particles.Particles import Particles
from direct.gui.DirectGui import *
from direct.motiontrail.MotionTrail import *
from panda3d.physics import *
from direct.actor.Actor import *
import inspect
import ast
import os
import uuid
import base64
import json
from direct.distributed.DistributedNode import DistributedNode
from direct.distributed.DistributedSmoothNode import DistributedSmoothNode

loadPrcFileData("", "window-type none")

from panda3d.core import WindowProperties
from direct.showbase.ShowBase import ShowBase
from typing import Annotated, get_type_hints

game = ShowBase()
game.disable_mouse()
game.enable_particles()
game.accept("w", lambda: base.camera.set_y(base.camera, 1))
game.accept("d", lambda: base.camera.set_x(base.camera, 1))
game.accept("s", lambda: base.camera.set_y(base.camera, -1))
game.accept("a", lambda: base.camera.set_x(base.camera, -1))
game.accept("q", lambda: base.camera.set_z(base.camera, 1))
game.accept("e", lambda: base.camera.set_z(base.camera, -1))
game.accept("w-repeat", lambda: base.camera.set_y(base.camera, 7 * game.clock.dt))
game.accept("d-repeat", lambda: base.camera.set_x(base.camera, 7 * game.clock.dt))
game.accept("s-repeat", lambda: base.camera.set_y(base.camera, -7 * game.clock.dt))
game.accept("a-repeat", lambda: base.camera.set_x(base.camera, -7 * game.clock.dt))
game.accept("q-repeat", lambda: base.camera.set_z(base.camera, 7 * game.clock.dt))
game.accept("e-repeat", lambda: base.camera.set_z(base.camera, -7 * game.clock.dt))

p = game.loader.load_model("panda")
p.reparent_to(render)
p.set_y(50)
from direct.showbase.DirectObject import DirectObject, messenger

emit = messenger.send
load_model = lambda model: game.loader.load_model(model)
load_texture = lambda texture: game.loader.load_texture(texture)
load_music = lambda music: game.loader.load_music(music)
load_sfx = lambda sfx: game.loader.load_sfx(sfx)
load_sound = lambda sound: game.loader.load_sound(sound)
load_font = lambda font: game.loader.load_font(font)

v3f = (float, float, float)
v4f = (float, float, float, float)
level = None


class NodeSave:
    def __init__(self, name):
        self.id = base64.b64encode(os.urandom(32))[:8]
        self.name = name
        self.vars = {}

    def save(self, level):
        with open(f"levels/{level}/{self.name}#{self.id}.json", "w") as f:
            json.dump(self.vars, f)


class QTPandaWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        #self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        #self.setGeometry(0,0,P3D_WIN_WIDTH, P3D_WIN_WIDTH)
        self.id = self.winId()

    def resizeEvent(self, evt):
        s = evt.size()
        wp = WindowProperties()
        print(s.width(), s.height(), self.x(), self.y())
        wp.setSize(s.width(), s.height())
        wp.setOrigin(int(self.x() + s.width() * 0.12), self.y())
        wp.setParentWindow(self.id)
        base.win.requestProperties(wp)

    def bindToWindow(self, windowHandle, win):
        wp = WindowProperties().getDefault()
        wp.setOrigin(0, 0)
        wp.setSize(self.width(), self.height())
        wp.setParentWindow(self.id)
        #self.id = windowHandle
        base.openDefaultWindow(props=wp)

        timer = QTimer(win)
        self.connect(timer, SIGNAL("timeout()"), self.step)
        timer.start(0)

    def step(self):
        taskMgr.step()

    def dragEnterEvent(self, event):
        event.accept()


class TimeLine(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.v = QVBoxLayout(self)
        self.setLayout(self.v)
        self.tl = QTimeLine(1000, parent=self)
        self.tl.setFrameRange(0, 100)
        self.setWindowTitle("Timeline")

        progressBar = QProgressBar(self)
        progressBar.setRange(0, 100)
        # Construct a 1-second timeline with a frame range of 0 - 100
        self.tl.frameChanged.connect(progressBar.setValue)
        # Clicking the push button will start the progress bar animation
        pushButton = QPushButton("Start animation", self)

        pushButton.clicked.connect(self.tl.start)
        #self.v.addWidget(self.tl)
        self.v.addWidget(pushButton)
        self.v.addWidget(progressBar)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setGeometry(0, 0, 300, 300)
        #self.connect()


class Vector2Widget(QWidget):
    def __init__(self, parent=None, is_int=False):
        super().__init__(parent)
        if not is_int:
            self.x = QDoubleSpinBox(self)
            self.y = QDoubleSpinBox(self)
        else:
            self.x = QSpinBox(self)
            self.y = QSpinBox(self)

        self.h = QHBoxLayout()
        self.h.addWidget(self.x)
        self.h.addWidget(self.y)
        self.setLayout(self.h)

        for x in (self.x, self.y):
            x.setRange(-1000000, 1000000)

    def get_vec(self):
        return self.x.value(), self.y.value()

    def on_changed(self, func):
        for x in (self.x, self.y):
            x.valueChanged.connect(func)


class Vector3Widget(QWidget):
    def __init__(self, parent=None, is_int=False):
        super().__init__(parent)
        if not is_int:
            self.x = QDoubleSpinBox(self)
            self.y = QDoubleSpinBox(self)
            self.z = QDoubleSpinBox(self)
        else:
            self.x = QSpinBox(self)
            self.y = QSpinBox(self)
            self.z = QSpinBox(self)

        self.h = QHBoxLayout()
        self.h.addWidget(self.x)
        self.h.addWidget(self.y)
        self.h.addWidget(self.z)
        self.setLayout(self.h)

        for x in (self.x, self.y, self.z):
            x.setRange(-1000000, 1000000)

    def get_vec(self):
        return self.x.value(), self.y.value(), self.z.value()

    def on_changed(self, func):
        for x in (self.x, self.y, self.z):
            x.valueChanged.connect(func)


class Vector4Widget(QWidget):
    def __init__(self, parent=None, is_int=False):
        super().__init__(parent)
        if not is_int:
            self.x = QDoubleSpinBox(self)
            self.y = QDoubleSpinBox(self)
            self.z = QDoubleSpinBox(self)
            self.w = QDoubleSpinBox(self)
        else:
            self.x = QSpinBox(self)
            self.y = QSpinBox(self)
            self.z = QSpinBox(self)
            self.w = QSpinBox(self)
        self.h = QHBoxLayout()
        self.h.addWidget(self.x)
        self.h.addWidget(self.y)
        self.h.addWidget(self.z)
        self.h.addWidget(self.w)
        self.setLayout(self.h)

        for x in (self.x, self.y, self.z, self.w):
            x.setRange(-1000000, 1000000)

    def get_vec(self):
        return self.x.value(), self.y.value(), self.z.value(), self.w.value()

    def on_changed(self, func):
        for x in (self.x, self.y, self.z, self.w):
            x.valueChanged.connect(func)


class InspectorWidget(QWidget):
    def __init__(self, name, widget, parent=None):
        super().__init__(parent)
        self.name = name
        self.setMaximumHeight(100)
        self.hl = QHBoxLayout()
        self.name_widget = QLabel(name)
        self.name_widget.setMaximumWidth(20)
        self.name_widget.setMaximumHeight(20)

        self.hl.addWidget(self.name_widget)
        print(widget)
        self.editor_widget = widget(self)
        self.editor_widget.setMaximumWidth(250)
        self.editor_widget.setMaximumHeight(50)
        if widget is Vector4Widget:
            self.editor_widget.setMaximumWidth(250)

        self.setup_widget()
        self.hl.addWidget(self.editor_widget)
        self.setLayout(self.hl)
        self.value = None
        self.callback = None

    def setup_widget(self):
        t = type(self.editor_widget)
        if t is QLineEdit:
            self.editor_widget.textEdited.connect(self.set_value)
        elif t is QCheckBox:
            self.editor_widget.stateChanged.connect(self.set_value)
        elif t is QDoubleSpinBox or t is QSpinBox:
            self.editor_widget.valueChanged.connect(self.set_value)
        elif t is QEnum:
            ...
        elif t in (Vector2Widget, Vector3Widget, Vector4Widget):
            self.editor_widget.on_changed(self.set_value)

    def set_value(self, value):
        self.value = value
        if self.callback:
            self.callback(value, self.name)

    def remove(self):
        self.hl.removeWidget(self.editor_widget)
        self.hl.removeWidget(self.name_widget)
        self.editor_widget.setParent(None)
        self.editor_widget = None
        self.name_widget.setParent(None)
        self.name_widget = None
        self.setParent(None)


class InspectorArrayWidget(QWidget):
    def __init__(self, name, widget, parent=None):
        super().__init__(parent)
        self.widget = widget
        self.name_widget = QLabel(name)
        self.name_widget.setMaximumWidth(20)
        self.name_widget.setMaximumHeight(20)

        self.vl = QVBoxLayout()
        self.setLayout(self.vl)

        self.b = QPushButton(self)
        self.r = QPushButton(self)

        self.sc = QScrollArea(self)

        self.vl.addWidget(self.sc)
        self.vl.addWidget(self.sc)

        self.widgets = QWidget()

        self.widgets.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.widgets.setLayout(QVBoxLayout(self.widgets))
        self.sc.setWidget(self.widgets)

    def add(self):
        self.widget()


class Inspector(QWidget):
    def __init__(self, parent=None, scene=None, scene_2=None):
        super().__init__(parent)

        self.scene: SceneGraph = scene
        self.scene_2: SceneGraph = scene_2

        self.groupbox = QGroupBox(self)
        self.groupbox.setMinimumWidth(300)
        self.groupbox.setTitle('Inspector')

        self.groupbox_layout = QVBoxLayout()
        self.groupbox.setLayout(self.groupbox_layout)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.layout.addWidget(self.groupbox)
        self.setLayout(self.layout)
        self.setGeometry(0, 0, 500, 500)

        self.list = QListView()
        self.groupbox_layout.addWidget(self.list)

        self.scroll = QScrollArea()
        self.scroll.setWidget(self.groupbox)
        self.scroll.setWidgetResizable(True)
        #self.scroll.setFixedHeight(200)
        self.layout.addWidget(self.scroll)

    def generate(self, current, previous):

        for i in reversed(range(self.groupbox_layout.count())):
            w = self.groupbox_layout.itemAt(i).widget()
            if w != self.scroll:
                w.setParent(None)

        if type(current) is QListWidgetItem:
            t = QLabel(current.text())
            t.setMaximumWidth(100)
            t.setMaximumHeight(25)

            self.groupbox_layout.addWidget(t)

            e = self.add_line()
            e.setMaximumHeight(25)

            b = QPushButton(self, text="Add")
            b.setMaximumWidth(100)
            b.setMaximumHeight(25)

            b.clicked.connect(lambda: self.add_field(e.text(), current))
            self.groupbox_layout.addWidget(b)

            print(current.data(Qt.UserRole))
            data = current.data(Qt.UserRole)
            if data:
                for key, value in data.items():
                    self.add_field(key, current, value)
            return

        node = None
        _class = None
        if current in self.scene.scene:
            node = self.scene.scene[current]
            _class = self.scene.scene_classes[current]
        elif current in self.scene_2.scene:
            node = self.scene_2.scene[current]
            _class = self.scene_2.scene_classes[current]

        if not node:
            return
        print("GET TAG", node.has_python_tag("vars#editor"), _class is not None)
        if node.has_python_tag("vars#editor"):
            _vars = node.get_python_tag("vars#editor")
            if _class is not None:
                print(_vars, "VARS")
                for key, value in _vars.items():
                    print(key, value)
                    p = value.get("property")
                    g = value.get("get")
                    s = value.get("set")
                    t = value.get("type")
                    r = value.get("range")
                    if p:
                        self.add_prop(_class, key, p, p, t, r)
                    elif g and s:
                        self.add_prop(_class, key, g, s, t, r)

            else:
                for key, value in _vars.items():
                    print(key, value)
                    w = self.add_property(key, value["type"], value["value"], parent=self)
                    self.groupbox_layout.addWidget(w)
                    def c(v, name, n=node):
                        tag = n.get_python_tag("vars#editor")
                        tag[name]["value"] = v
                        n.set_python_tag("vars#editor", tag)
                    w.callback = c

        pos = node.get_pos()

        self.add_text("X", pos[0], node.set_x, float)
        self.add_text("Y", pos[1], node.set_y, float)
        self.add_text("Z", pos[2], node.set_z, float)

        h, p, r = node.get_hpr()
        self.add_text("Heading", h, node.set_h, float)
        self.add_text("Pitch", p, node.set_p, float)
        self.add_text("Roll", r, node.set_r, float)

        x, y, z = node.get_scale()
        self.add_text("Scale X", x, node.set_sx, float)
        self.add_text("Scale Y", y, node.set_sy, float)
        self.add_text("Scale Z", z, node.set_sz, float)

        x, y, z = node.get_shear()
        self.add_text("Shear X", x, node.set_shxy, float)
        self.add_text("Shear Y", y, node.set_shyz, float)
        self.add_text("Shear Z", z, node.set_shxz, float)

        self.add_text("Tags")
        tags = node.get_tags()

        i = QTableWidget(len(tags), 2)
        self.groupbox_layout.addWidget(i)
        r = 0
        for t in tags:
            if "#editor" not in t:
                #print(tags, t, node.get_tag(t), len(tags))
                i.setItem(r, 0, QTableWidgetItem(t))
                i.setItem(r, 1, QTableWidgetItem(node.get_tag(t)))
                r += 1

        self.add_text("Python Tags")
        tags = node.get_python_tags()

        i = QTableWidget(len(tags), 2)
        self.groupbox_layout.addWidget(i)
        r = 0
        for t in tags:
            if "#editor" not in t:
                #print(tags, t, node.get_python_tag(t), len(tags))
                i.setItem(r, 0, QTableWidgetItem(t))
                i.setItem(r, 1, QTableWidgetItem(node.get_python_tag(t)))
                r += 1

    def add_field(self, name, obj, _type="str"):
        if type(obj) is not dict:
            data = obj.data(Qt.UserRole)
        else:
            data = obj
        if name not in data:
            data[name] = {}
            data[name]["type"] = _type
            data[name]["array"] = False
            data[name]["value"] = ""
        lp = QLabel(f"{name}:")
        lp.setMaximumWidth(100)
        lp.setMaximumHeight(10)
        self.groupbox_layout.addWidget(lp)
        types = QComboBox()
        types.setMaximumWidth(100)
        types.addItem("str")
        types.addItem("vec2")
        types.addItem("vec3")
        types.addItem("vec4")
        types.addItem("int")
        types.addItem("float")
        types.addItem("enum")
        self.groupbox_layout.addWidget(types)
        array = QCheckBox()
        #array.connect()
        array.setText("Is Array")
        self.groupbox_layout.addWidget(array)

        value = data[name]["value"]
        w = self.add_property(name, _type, value, parent=self)
        self.groupbox_layout.addWidget(w)

        class Update:
            def __init__(self, name, p, _obj):
                self.w = None
                self.name = name
                self.p = p
                self.obj = _obj

            def update(self, text):
                print("swap", text, self.w)
                w = self.p.add_property(self.name, text)
                self.p.groupbox_layout.replaceWidget(self.w, w)
                self.p.groupbox_layout.removeWidget(self.w)
                self.w.setParent(None)
                self.w = w
                data = obj.data(Qt.UserRole)
                data["type"] = text
                obj.setData(Qt.UserRole, data)

            def value(self, v):
                data = obj.data(Qt.UserRole)
                data["value"] = v
                obj.setData(Qt.UserRole, data)

        u = Update(name, self, obj)
        u.w = w
        types.currentTextChanged.connect(lambda text, _u=u: _u.update(text))

        obj.setData(Qt.UserRole, data)

    def add_line(self, text="", layout=None):
        if text is None:
            text = ""
        p = QLineEdit(text)
        p.setMaximumWidth(100)
        p.setAlignment(Qt.AlignmentFlag.AlignCenter)
        p.setFocus()
        #p.textEdited.connect(set)
        if layout is None:
            layout = self.groupbox_layout
        layout.addWidget(p)
        return p

    def add_prop(self, _class, name, get, set, type, range=None):
        lp = QLabel(f"{name}:")

        """if not callable(get):
            get = lambda: get
        if not callable(set):
            def _set(*args):
                _set.set = args
            _set.set = set
            set = _set """
        try:
            self.groupbox_layout.addWidget(lp)
            get = getattr(_class, get)
            if callable(get):
                value = get()
                set = getattr(_class, set)
            else:
                _set = set
                value = get
                set = lambda v: setattr(_class, _set, v)
            if type == "int":
                self.add_int(value)

            elif type == "float":
                self.add_float(value)

            elif type == "bool":
                self.add_bool(value)

            elif type == "dict":
                p = QComboBox()
                p.addItems(value.keys())
                p.currentIndexChanged.connect(set)
                self.groupbox_layout.addWidget(p)

            elif type == "str":
                if value is None:
                    value = "Empty"
                p = QLineEdit(f"{value}")
                p.setMaximumWidth(150)
                p.setAlignment(Qt.AlignmentFlag.AlignCenter)
                p.setFocus()
                p.textEdited.connect(set)
                self.groupbox_layout.addWidget(p)

            elif type == "vec4":
                self.add_vec4(value)

            elif type == "vec3":
                self.add_vec3(value)
            else:
                print(value, "VALUE")
                p = QLineEdit(f"{value}")
                p.setMaximumWidth(150)
                p.setAlignment(Qt.AlignmentFlag.AlignCenter)
                p.setFocus()
                p.textEdited.connect(set)
                self.groupbox_layout.addWidget(p)
        except Exception as e:
            print(e)

    def add_text(self, name, value=None, callback=None, type=None, widget=None, _range=None, **kwargs):
        lp = QLabel(f"{name}:")
        self.groupbox_layout.addWidget(lp)
        try:

            #lp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if widget is None:
                def t(x):
                    try:
                        print("HI")
                        return callback(type(x), **kwargs)
                    except Exception as E:
                        print(E)

                if type is int:
                    p = QSpinBox()
                    p.setMaximumWidth(150)
                    if _range is not None:
                        p.setRange(_range[0], _range[1])
                    else:
                        p.setMaximum(100000000)
                        p.setMinimum(-100000000)
                    p.setValue(value)

                    p.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    if callback is not None:
                        p.valueChanged.connect(t)
                elif type is float:
                    p = QDoubleSpinBox()
                    p.setMaximumWidth(150)
                    if _range is not None:
                        p.setRange(_range[0], _range[1])
                    else:
                        p.setMaximum(10000000000)
                        p.setMinimum(-10000000000)
                    p.setValue(value)

                    p.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    if callback is not None:
                        p.valueChanged.connect(t)
                elif type is bool:
                    print(value)
                    p = QCheckBox()
                    if value:
                        p.setChecked(value)
                    if callback is not None:
                        p.stateChanged.connect(t)
                elif type is dict:
                    p = QComboBox()
                    p.addItems(value.keys())
                    if callback is not None:
                        p.currentIndexChanged.connect(t)
                elif type is str:
                    if value is None:
                        value = "Empty"
                    p = QLineEdit(f"{value}")
                    p.setMaximumWidth(150)
                    p.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    p.setFocus()
                    if callback is not None:
                        p.textEdited.connect(t)
                else:
                    print(value, "VALUE")
                    p = QLineEdit(f"{value}")
                    p.setMaximumWidth(150)
                    p.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    p.setFocus()
                    if callback is not None:
                        p.textEdited.connect(t)

                self.groupbox_layout.addWidget(p)

            elif widget == "button":
                p = QPushButton(f"{value}")
                #p.setMaximumWidth(150)
                #p.setAlignment(Qt.AlignmentFlag.AlignCenter)
                #p.setFocus()
                self.groupbox_layout.addWidget(p)

                def t(x):
                    try:
                        return callback(type(x), **kwargs)
                    except:
                        pass

                if callback is not None:
                    if type is not None:
                        p.clicked.connect(t)
                    else:
                        p.clicked.connect(callback)
        except Exception as e:
            print(e)

    def add_property(self, name, _type, value=None, parent=None):
        match _type:
            case "vec2":
                w = Vector2Widget
            case "vec3":
                w = Vector3Widget
            case "vec4":
                w = Vector4Widget
                ...
            case "int":
                w = QSpinBox
                ...
            case "float":
                w = QDoubleSpinBox
                ...
            case "enum":
                w = self.add_enum(value, setter=None)
                ...
            case "bool":
                w = QCheckBox
                ...
            case "str" | _:
                w = QLineEdit
        w = InspectorWidget(name, w)
        return w


class Level(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.m = QMenu()
        self.m.addAction("New Level").triggered.connect(self.add_level)
        self.add_level()
        self.m.show()
        self.itemDoubleClicked.connect(self.open)

    def open(self, item: QTreeWidgetItem, column):
        global level
        print(item, column)
        level = item.text(column)

    def contextMenuEvent(self, event):
        #print(self.indexAt(event.globalPos()))
        #print(self.itemAt(self.mapToGlobal(event.globalPos())))

        self.m.exec(event.globalPos())

    def add_level(self):
        widget = self.currentItem()
        if widget is None:
            widget = self

        w = QTreeWidgetItem(widget, ["Level"], 0)
        w.setFlags(w.flags() | Qt.ItemIsEditable)

        path = ""

        def all_parents(widget: QTreeWidgetItem):
            nonlocal path
            path += "/" + widget.text(0)
            p = widget.parent()
            if p:
                all_parents(p)

        all_parents(w)
        print(path)
        dir = QDir("")
        dir.mkdir(f"levels{path}")


class SceneGraph(QTreeWidget):
    def __init__(self, parent=None, node=None):
        super().__init__(parent)
        self.o = DirectObject()
        self.o.accept("save", self.save)
        self.scene_classes = {}
        self.headerItem().setText(0, "Scene Graph 3D")
        self.c = None
        self.menu()
        self.n: NodePath = None
        self.w: QTreeWidgetItem = None
        #self.setContextMenuPolicy(Qt.CustomContextMenu)
        #self.customContextMenuRequested.connect(self.move)
        self.scene: dict[QTreeWidgetItem, NodePath] = {}
        self.nodes = {}

        self.setMinimumSize(200, 600)
        self.currentItemChanged.connect(
            self.item_changed)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.dragEnterEvent = self._dragEnterEvent
        self.dragMoveEvent = self._dragMoveEvent

        self.gen = DirectObject()
        self.gen.accept("scene-gen", self.generate)

        #self.t = node_lib.node_classes["Hero3"](NodePath("Hero3"))
        #self.t.node.reparent_to(render)

        #self.nodes[self.t.node.node()] = self.t

        self.node = node
        if node:
            self.add_node(self.node, self, True)

    def generate(self):
        self.clear()
        self.scene = {}
        self.add_node(self.node, self, True)

    def add_node(self, node, widget, first=False, _class=None, _vars=None):
        try:
            name = node.get_name()
        except:

            name = node.getNode().getName()
        node.set_tag("id#editor", str(uuid.uuid4())[:10])
        w = QTreeWidgetItem(widget, [name], 0)
        w.setFlags(w.flags() | Qt.ItemIsEditable)
        #w.setDisabled(first)

        if _vars:
            node.set_python_tag("vars#editor", _vars)

        #w.setFlags(widget.flags() & ~Qt.ItemIsDropEnabled)
        self.scene[w] = node
        self.scene_classes[w] = _class

        for c in node.get_children():
            self.add_node(c, w, _class=_class)

        if first:
            self.w = w

    def item_changed(self, current: QTreeWidgetItem, previous: QTreeWidgetItem):
        if current:
            print(current, previous, )
            self.current = current
            w = self.scene[current]
            w.set_name(current.text(0))

    def minimumSizeHint(self):
        return QSize(50, 400)

    def _dragEnterEvent(self, ev: QDragEnterEvent):
        ev.accept()
        print(ev.source(), "Source", ev.type(), type(ev.source().currentIndex()))
        a: QListWidget = ev.source()
        if type(a) is QListWidget:
            print(a.currentIndex().data(Qt.UserRole))
            print(a.currentIndex().data(), "DATA")
            n = NodePath(a.currentIndex().data())
            n.set_python_tag("vars#editor", a.currentIndex().data(Qt.UserRole))
            print("TAG", n.get_python_tag("vars#editor"))
            print(n, self.currentItem())
            n.reparent_to(self.scene[self.current])
            render.ls()
            self.add_node(n, self.current)

            print(self.scene)

    def _dragMoveEvent(self, ev):
        ev.accept()
        """item = ev.source()
        if item.isAncestorOf(self):
            ev.ignore()"""

    def dragLeaveEvent(self, event):
        help(event)
        event.accept()

    def add_action(self, m, x):
        print(x, )
        try:
            c = globals()[x["class"]]
            v = x["vars"]
        except Exception as e:
            print(e)
        m.addAction(x["name"]).triggered.connect(lambda: self.spawn(c, v))

    def menu(self):
        self.m = QMenu()

        print(os.listdir())
        objs = os.listdir("objects")
        enums = os.listdir("enums")
        objects = {}

        for o in objs:
            with open(f"objects/{o}") as f:
                print(o)
                objects[o] = json.load(f)
        print(objects)
        for key, item in objects.items():
            m = self.m.addMenu(key.strip(".json"))
            for key in item.keys():
                print(key, "KEY")
                stuff = item[key]
                for x in stuff:
                    if type(x) is dict:
                        hidden = x.get("hidden")
                        if hidden is not None:
                            if hidden:
                                continue
                        pr = x.get("parent")
                        if pr is not None:
                            print(pr)
                            for p in pr:
                                for s in stuff:
                                    if s["name"] == p:
                                        #print(s["vars"], x["vars"], "S")
                                        if "vars" not in x:
                                            x["vars"] = {}
                                        x["vars"].update(s["vars"])
                        self.add_action(m, x)
        #m.move(point)
        self.mm = self.m.addMenu("Meshes")
        self.mm.addAction("Panda").triggered.connect(
            lambda: (game.loader.load_model("panda").reparent_to(render), render.ls()))
        self.ml = self.m.addMenu("Lighting")
        ("Attenuation", "Attenuation", (float, float, float))

        e = self.ml.addAction("DirectionalLight").triggered.connect(lambda: self.spawn(DirectionalLight,
                                                                                       [
                                                                                           ("Color", "Color", (
                                                                                               float, float, float,
                                                                                               float),
                                                                                            (0, 1), 0.1),
                                                                                           ("Color Temperature",
                                                                                            "ColorTemperature", float,
                                                                                            (1000, 9000)),

                                                                                       ]))
        e = self.ml.addAction("PointLight").triggered.connect(lambda: self.spawn(PointLight,
                                                                                 [
                                                                                     ("Color", "Color",
                                                                                      (float, float, float, float),
                                                                                      (0, 1), 0.1),
                                                                                     ("Color Temperature",
                                                                                      "ColorTemperature", float,
                                                                                      (1000, 9000)),
                                                                                     ("Attenuation", "Attenuation",
                                                                                      (float, float, float))

                                                                                 ])
                                                              )
        e = self.ml.addAction("AmbientLight").triggered.connect(lambda: self.spawn(AmbientLight,
                                                                                   [
                                                                                       ("Color", "Color",
                                                                                        (float, float, float, float),
                                                                                        (0, 1), 0.1),
                                                                                       ("Color Temperature",
                                                                                        "ColorTemperature", float,
                                                                                        (1000, 9000)),
                                                                                   ]))
        e = self.ml.addAction("Spotlight").triggered.connect(lambda: self.spawn(Spotlight, [
            ("Color", "Color", (float, float, float, float), (0, 1), 0.1),
            ("Color Temperature", "ColorTemperature", float, (1000, 9000)),
            ("Attenuation", "Attenuation", (float, float, float))
        ]))
        e = self.ml.addAction("PolylightNode").triggered.connect(lambda: self.spawn(PolylightNode, [
            ("Color", "Color", (float, float, float))
        ]))

        geo = [("geom", "geom", bool),
               ("geom_pos", "geom_pos", v3f),
               ("geom_hpr", "geom_hpr", v3f),
               ("geom_scale", "geom_scale", v3f), ]
        text = [("Text", "text", str),
                ("text_bg", "text_bg", v4f),
                ("text_fg", "text_fg", v4f),
                ("text_pos", "text_pos", (float, float)),

                ]

        a = [("Frame Color", "frameColor", (float, float, float, float)),
             ("frameSize", "frameSize", v4f),
             ("frameVisibleScale", "frameVisibleScale", (float, float)),
             ("relief", "relief", int),
             ("invertedFrames", "invertedFrames", bool),
             ("borderWidth", "borderWidth", (float, float)),
             ("image", "image", str),
             ("image_pos", "image_pos", v3f),
             ("image_hpr", "image_hpr", v3f),
             ("image_scale", "image_scale", v3f),

             ("pad", "pad", (float, float)),
             ("frameTexture", "frameTexture", str),
             ("sortOrder", "sortOrder", int),

             ]
        ("state", "state", bool)

        self.mdg = self.m.addMenu("Gui")

        e = self.mdg.addAction("OnscreenGeom").triggered.connect(lambda: self.spawn(OnscreenGeom, ))
        e = self.mdg.addAction("OnscreenImage").triggered.connect(lambda: self.spawn(OnscreenImage))
        e = self.mdg.addAction("OnscreenText").triggered.connect(lambda: self.spawn(OnscreenText, [
            *text
        ]))

        self.mbp = self.m.addMenu("Physics")
        e = self.mbp.addAction("CollisionNode").triggered.connect(lambda: self.spawn(CollisionNode))
        e = self.mbp.addAction("PhysicalNode").triggered.connect(lambda: self.spawn(PhysicalNode))
        #e = self.mbp.addAction("BulletPersistentManifold").triggered.connect(
        #    lambda: self.spawn(BulletPersistentManifold))
        #e = self.mbp.addAction("BulletWheel").triggered.connect(lambda: self.spawn(BulletWheel))
        #e = self.mbp.addAction("BulletSoftBodyNode").triggered.connect(lambda: self.spawn(BulletSoftBodyNode))
        e = self.mbp.addAction("BulletDebugNode").triggered.connect(lambda: self.spawn(BulletDebugNode))

        self.mn = self.m.addMenu("Add")
        e = self.mn.addAction("Empty")
        e.triggered.connect(self.empty_node)
        e = self.mn.addAction("Actor").triggered.connect(lambda: self.spawn(Actor))
        e = self.mn.addAction("GeomNode").triggered.connect(lambda: self.spawn(GeomNode))
        e = self.mn.addAction("AnimBundleNode").triggered.connect(lambda: self.spawn(AnimBundleNode))
        e = self.mn.addAction("CallbackNode").triggered.connect(lambda: self.spawn(CallbackNode))
        e = self.mn.addAction("LensNode").triggered.connect(lambda: self.spawn(LensNode))
        e = self.mn.addAction("Camera").triggered.connect(lambda: self.spawn(Camera))
        e = self.mn.addAction("ModelNode").triggered.connect(lambda: self.spawn(ModelNode))
        e = self.mn.addAction("PandaNode").triggered.connect(lambda: self.spawn(PandaNode))

        e = self.mn.addAction("PlaneNode").triggered.connect(lambda: self.spawn(PlaneNode))
        e = self.mn.addAction("WeakNodePath").triggered.connect(lambda: self.spawn(WeakNodePath))

        self.on = self.m.addMenu("Other")
        e = self.on.addAction("AnalogNode").triggered.connect(lambda: self.spawn(AnalogNode))
        e = self.on.addAction("InputDeviceNode").triggered.connect(lambda: self.spawn(InputDeviceNode))
        e = self.on.addAction("TrackerNode").triggered.connect(lambda: self.spawn(TrackerNode))
        e = self.on.addAction("MouseInterfaceNode").triggered.connect(lambda: self.spawn(MouseInterfaceNode))

        e = self.on.addAction("DataNode").triggered.connect(lambda: self.spawn(DataNode))
        e = self.on.addAction("DialNode").triggered.connect(lambda: self.spawn(DialNode))
        e = self.on.addAction("DistancePhasedNode").triggered.connect(lambda: self.spawn(Particles))

        self.nn = self.m.addMenu("Networking")
        e = self.nn.addAction("Distributed Smooth Node").triggered.connect(lambda: self.spawn(DistributedSmoothNode))
        e = self.nn.addAction("Distributed Node").triggered.connect(lambda: self.spawn(DistributedNode))

        e = self.m.addAction("Copy").triggered.connect(self.copy)
        e = self.m.addAction("Paste").triggered.connect(self.paste)
        #e = self.m.addAction("Cut").triggered.connect(self.cut)
        e = self.m.addAction("Delete").triggered.connect(self.delete)

        #m.exec(point.globalPos())
        self.m.show()

    def delete(self):
        if self.n:
            self.n.remove_node()

            def remove_children(widget: QTreeWidgetItem):
                del self.scene[widget]

            self.all_children(self.w, remove_children)
            for i in range(self.w.childCount()):
                self.w.removeChild(self.w.child(0))
            self.w.parent().removeChild(self.w)

            self.w = self
            self.n = None

    def copy(self):
        self.c = self.scene[self.w]
        print(self.c)

    def paste(self):
        if self.c:
            node = self.c
            node = copy(node)
            p = self.currentItem().parent()
            if p is None:
                p = self.currentItem()
            node.reparent_to(self.scene[p])
            render.ls()

            self.add_node(node, p)

    def cut(self):
        self.copy()
        self.delete()

    def all_children(self, widget, function):
        for i in range(widget.childCount()):
            w = widget.child(i)
            self.all_children(w, function)
        function(widget)

    def empty_node(self):
        n = NodePath("Node")
        if self.n:
            n.reparent_to(self.n)
        self.add_node(n, self.w)

    def spawn(self, _class, vars=None):
        print(_class, "CLASS")
        if self.n:

            try:
                nc = _class(name=_class.__name__)
            except:
                try:
                    nc = _class()
                except:
                    nc = _class(self.n)
            try:
                nc.reparent_to(self.n)
                n = nc
            except:
                try:
                    n = self.n.attach_new_node(nc.getNode())
                except:
                    try:
                        n = self.n.attach_new_node(nc.getNode(0))
                    except:
                        try:
                            n = self.n.attach_new_node(nc)
                        except:
                            try:
                                n = nc.get_root()
                                n.reparent_to(self.n)
                            except:
                                try:
                                    n = nc.generate()
                                except:
                                    try:
                                        n = nc.getNodePath()
                                    except:
                                        try:
                                            n = nc.parent
                                        except Exception as e:
                                            print(e)
                                            return
            if _class in (DirectionalLight, PointLight, Spotlight, AmbientLight):
                render.set_light(n)
                print("SET")
            print(vars, "VARS")
            self.add_node(n, self.w, _class=nc, _vars=vars)

    def contextMenuEvent(self, event):
        #print(self.indexAt(event.globalPos()))
        #print(self.itemAt(self.mapToGlobal(event.globalPos())))
        print(self.selectedItems())
        items = self.selectedItems()
        if len(items) == 1:
            self.n = self.scene[items[0]]
            self.w = items[0]
            print(self.n)

        self.m.exec(event.globalPos())

    def save(self):
        global level
        for n in self.scene.values():
            vars = {
                "pos": list(n.get_pos()),
                "scale": list(n.get_scale()),
                "hpr": list(n.get_hpr()),
                "tags":{},
                "type": None,

            }
            for t in n.get_tags():
                vars["tags"][t] = n.get_tag(t)
            if n.has_python_tag("vars#editor"):
                vars.update(n.get_python_tag("vars#editor"))
            with open(f"levels/{level}/{n.name}#{n.get_tag('id#editor')}.json", "w") as f:
                json.dump(vars, f, indent=2)

    def load(self):
        game.camera.detach()
        render.removeAllChildren()
        game.camera.reparent_to(render)
        game.camera2d.detach()
        game.pixel2d.detach()
        game.aspect2d.detach()
        game.render2d.removeAllChildren()
        game.camera2d.reparent_to(render2d)
        game.pixel2d.reparent_to()
        game.aspect2d.reparent_to()

        def remove_children(widget: QTreeWidgetItem):
            del self.scene[widget]

        self.all_children(self.w, remove_children)

        x = os.listdir("levels/ltest")
        for y in x:
            with open(f"levels/ltest/{y}.json", "w") as f:
                vars = json.load(f)


class SceneTabs(QWidget):
    def __init__(self):
        super().__init__()
        #self.setMinimumSize(200, 600)
        self.tabs = QTabWidget(self)
        self.tabs.setMinimumSize(200, 600)
        self.render = SceneGraph(self, node=render)
        self.render2d = SceneGraph(self, node=render2d)
        self.tabs.addTab(self.render, "Render")
        self.tabs.addTab(self.render2d, "Render2D")


class Nodes(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.do = DirectObject()
        self.do.accept("save", self.save)
        self.h = QHBoxLayout()

        self.v = QVBoxLayout()
        #self.v.addWidget(self.h)
        self.setLayout(self.v)
        self.l = QListWidget(self)
        self.l.setDragDropMode(QAbstractItemView.InternalMove)
        self.e = QLineEdit(self)
        self.b = QPushButton(self, text="Add")
        self.b.clicked.connect(lambda: self.add_entity())

        self.v.addWidget(self.l)
        self.v.addWidget(self.e)
        self.v.addWidget(self.b)

        n = os.listdir("nodes")
        for path in n:
            with open(f"nodes/{path}") as f:
                data = json.load(f)
                print(data)
                self.add_entity(path.strip(".json"), data)

    def add_entity(self, text=None, data=None):
        if text is None:
            text = self.e.text()
        print(text, "ENTITY")
        o = QListWidgetItem(text)
        if data is None:
            data = {}
        o.setData(Qt.UserRole, data)
        self.l.addItem(o)
        self.e.clear()

    def sizeHint(self):
        return QSize(.2 * self.width(), .3 * self.height())

    def save(self):
        nodes = [self.l.item(x) for x in range(self.l.count())]
        for node in nodes:
            data = node.data(Qt.UserRole)
            with open(f"nodes/{node.text()}.json", "w") as f:
                json.dump(data, f, indent=2)


class FileExplorer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_folder = ''
        self.fileModel = QFileSystemModel()
        self.fileModel.setRootPath(sys.argv[0])

        self.v = QVBoxLayout(self)
        self.setLayout(self.v)

        self.up = QPushButton(text="UP")
        self.up.clicked.connect(self.go_up)

        self.listview = QListView()
        self.listview.setModel(self.fileModel)
        self.listview.setDragDropMode(QAbstractItemView.InternalMove)

        self.v.addWidget(self.up)
        self.v.addWidget(self.listview)

        path = QDir().path()
        self.listview.setRootIndex(self.fileModel.index(path))
        self.listview.clicked[QModelIndex].connect(self.on_clicked)

    def sizeHint(self):
        return QSize(.6 * self.width(), .3 * self.height())

    def on_clicked(self, index):
        print(index)
        item = self.fileModel.itemData(index)
        print(item, item[0].split("."))
        print(item[1].name())
        if item[1].name() != "folder":
            ...
        else:
            print(self.fileModel.filePath(index))
            self.fileModel.setRootPath(self.fileModel.filePath(index))
            self.listview.setRootIndex(self.fileModel.index(self.fileModel.filePath(index)))
            print(self.listview.rootIndex())

    @Slot()
    def go_up(self):
        path = QDir(self.fileModel.rootPath())
        path.cdUp()
        path.rootPath()
        print(path.path())
        self.fileModel.setRootPath(path.path())
        self.listview.setRootIndex(self.fileModel.index(path.path()))


class Music(QWidget):
    def __init__(self, music):
        super().__init__()
        self.current = None
        self.music = music
        self.v = QVBoxLayout(self)
        self.setLayout(self.v)

        self.b = QPushButton(self, text="Play")
        self.b.clicked.connect(self.play)
        self.bl = QPushButton(self, text="Loop")
        self.bl.clicked.connect(self.loop)
        self.bp = QPushButton(self, text="Pause")
        self.bp.clicked.connect(self.pause)

        self.l = QListWidget(self)

        self.v.addWidget(self.b)
        self.v.addWidget(self.bp)
        self.v.addWidget(self.bl)
        self.v.addWidget(self.l)

    def show(self):
        QWidget.show(self)
        self.l.clear()
        for i in self.music.keys():
            self.l.addItem(QListWidgetItem(i))

    def play(self):
        self.current = self.l.currentItem()
        if self.current:
            self.current = self.current.text()
            self.music[self.current].stop()
            self.music[self.current].setLoop(False)
            self.music[self.current].play()

    def loop(self):
        self.current = self.l.currentItem()
        if self.current:
            self.current = self.current.text()
            self.music[self.current].stop()
            self.music[self.current].setLoop(True)
            self.music[self.current].play()

    def pause(self):
        if self.current:
            self.music[self.current].stop()


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.musics = {}
        self.sounds = {}
        self.sfx = {}
        self.path = None
        self.shader = None
        self.code = None
        self.tl = None
        self.setGeometry(200, 200, 800, 800)
        self.UiComponents()
        self.show()
        self.add_menus()

    def save(self):
        print("SAVING")
        #self.shader.save(self.path)
        emit("save")

    def load(self):
        print("loading")
        emit("load")

    def add_menus(self):
        menubar = self.menuBar()

        fileMenu = menubar.addMenu('File')
        newAct = QAction('New', self)
        newAct.triggered.connect(self.new_project)
        fileMenu.addAction(newAct)

        newAct = QAction('Save', self)
        newAct.triggered.connect(self.save)
        newAct.setShortcut(QKeySequence("Ctrl+S"))

        fileMenu.addAction(newAct)

        newAct = QAction('Load', self)
        newAct.triggered.connect(self.load)

        fileMenu.addAction(newAct)

        load_menu = menubar.addMenu('Import')
        impAct = QAction('Import Model', self)
        impAct.triggered.connect(self.load_model)
        load_menu.addAction(impAct)

        impAct = QAction('Import SFX', self)
        impAct.triggered.connect(load_sfx)
        load_menu.addAction(impAct)

        impAct = QAction('Import Sound', self)
        impAct.triggered.connect(load_sfx)
        load_menu.addAction(impAct)

        impAct = QAction('Import Music', self)
        impAct.triggered.connect(self.load_music)
        load_menu.addAction(impAct)

        impAct = QAction('Import Texture', self)
        impAct.triggered.connect(load_texture)
        load_menu.addAction(impAct)

        impAct = QAction('Import Font', self)
        impAct.triggered.connect(load_font)
        load_menu.addAction(impAct)

        code_menu = menubar.addMenu("Editors")
        code_act = QAction("Code", self)
        code_act.triggered.connect(self.code.show)
        code_menu.addAction(code_act)

        part_act = QAction("Particle", self)
        part_act.triggered.connect(self.code.show)
        code_menu.addAction(part_act)

        sheet_act = QAction("Spread Sheet", self)
        sheet_act.triggered.connect(self.code.show)
        code_menu.addAction(sheet_act)

        #sheet_act = QAction("Shader Editor", self)
        #sheet_act.triggered.connect(self.shader.show)
        code_menu.addAction(sheet_act)

        #sheet_act = QAction("Scene Graph", self)
        #sheet_act.triggered.connect(self.scene.show)
        #code_menu.addAction(sheet_act)

        sheet_act = QAction("TimeLine", self)
        sheet_act.triggered.connect(self.tl.show)
        code_menu.addAction(sheet_act)

        code_menu = menubar.addMenu("Music")
        code_act = QAction("Play", self)
        code_act.triggered.connect(self.music.show)
        code_menu.addAction(code_act)

    def new_project(self):
        path = QFileDialog.getExistingDirectory(self, "Project Location")
        if path:
            self.path = path
            for x in ["audio", "components", "effects", "events", "levels", "nodes", "networked", "shaders", "sheets",
                      "models", "sequences"]:
                QDir(path).mkdir(x)

    def load_model(self):
        model = QFileDialog.getOpenFileName(self, "Import Model", "",
                                            "Models (*.bam *.egg *.blend *.gltf *.glb);; BAM (*.bam);; EGG (*.egg);; BLEND (*.blend);; GLTF (*.gltf *.glb)")
        if model != ('', ''):
            m = load_model(Filename.from_os_specific(model[0]))
            m.reparent_to(render)
            emit("scene-gen")

    def load_music(self):
        music = QFileDialog.getOpenFileName(self, "Import Music", "",
                                            "Sounds (*.ogg *.wav *.mp3)")
        if music != ('', ''):
            m = load_music(Filename.from_os_specific(music[0]))
            self.musics[music[0]] = m

    def UiComponents(self):
        self.code = CodeEditor()
        self.tl = TimeLine()

        dock1 = QDockWidget("Scene Graph", self)
        dock2 = QDockWidget("File Explorer", self)
        dock3 = QDockWidget("ViewPort", self)
        dock4 = QDockWidget("Objects", self)
        dock5 = QDockWidget("Inspector", self)

        dock1.setAllowedAreas(Qt.LeftDockWidgetArea)
        dock2.setAllowedAreas(Qt.LeftDockWidgetArea)
        dock3.setAllowedAreas(Qt.RightDockWidgetArea)
        dock4.setAllowedAreas(Qt.RightDockWidgetArea)
        dock5.setAllowedAreas(Qt.RightDockWidgetArea)

        w_3 = QTPandaWidget()
        w_3.bindToWindow(dock3.winId(), self)
        w_1 = SceneTabs()

        w_2 = Level()
        w_4 = Nodes()
        w_5 = Inspector(scene=w_1.render, scene_2=w_1.render2d)
        w_1.render.currentItemChanged.connect(
            w_5.generate)
        w_1.render2d.currentItemChanged.connect(
            w_5.generate)
        w_4.l.currentItemChanged.connect(w_5.generate)
        dock1.setWidget(w_1)
        dock2.setWidget(w_2)
        dock3.setWidget(w_3)
        dock4.setWidget(w_4)
        dock5.setWidget(w_5)

        self.addDockWidget(Qt.LeftDockWidgetArea, dock1)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock2)
        self.addDockWidget(Qt.RightDockWidgetArea, dock3)
        self.addDockWidget(Qt.RightDockWidgetArea, dock4)
        self.addDockWidget(Qt.RightDockWidgetArea, dock5)

        self.splitDockWidget(dock1, dock2, Qt.Vertical)
        self.splitDockWidget(dock3, dock5, Qt.Horizontal)
        self.splitDockWidget(dock3, dock4, Qt.Vertical)

        self.docks = dock1, dock2, dock3, dock4, dock5

        #self.shader = ShaderEditor(self)
        self.music = Music(self.musics)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        side = self.width() // 5  # 2 / 10
        center = side * 3  # 6 / 10
        widths = side, side, center, center, side
        self.resizeDocks(self.docks, widths, Qt.Horizontal)
        vUnit = self.height() // 10
        top = vUnit * 7
        bottom = vUnit * 3
        heights = top, bottom, top, bottom, top + bottom
        self.resizeDocks(self.docks, heights, Qt.Vertical)


App = QApplication(sys.argv)
#print(QStyleFactory.keys() )
#App.setStyle(QStyleFactory.create('windowsvista'))

# create the instance of our Window
window = Window()
window.show()
# start the app
sys.exit(App.exec())
