import os
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase, messenger
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
import sys
from direct.stdpy.file import open, isdir, isfile

#TODO
# Different Scenes
# Load Models
# render2d

game = ShowBase()

names = {"Vertex": ".vert", "Fragment": '.frag', "Geometry": ".geom", "Tess Hull": ".hull", "Tess Domain": ".dom"}


class ShaderEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.name = None
        self.setGeometry(500, 100, 500, 500)
        self.shaders: dict[str, QPlainTextEdit] = {}
        self.h = QHBoxLayout()
        self.setLayout(self.h)
        self.tb = QTabWidget(self)
        self.h.addWidget(self.tb)

        for x, y in {"Vertex": """#version 150

// Uniform inputs
uniform mat4 p3d_ModelViewProjectionMatrix;

// Vertex inputs
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;

// Output to fragment shader
out vec2 texcoord;

void main() {
  gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
  texcoord = p3d_MultiTexCoord0;
}""", "Fragment": """#version 150

uniform sampler2D p3d_Texture0;

// Input from vertex shader
in vec2 texcoord;

// Output to the screen
out vec4 p3d_FragColor;

void main() {
  vec4 color = texture(p3d_Texture0, texcoord);
  p3d_FragColor = color.bgra;
}""",
                     "Geometry": "",
                     "Tess Hull": "",
                     "Tess Domain": "",}.items():
            self.add_tab(x, y)
        base.cam.set_y(-10)
        base.loader.load_model("environment").reparent_to(render)
        self.apply_shaders()

        timer = QTimer(self)
        self.connect(timer, SIGNAL("timeout()"), game.task_mgr.step)
        timer.start(0)

        newAct = QAction('Save', self)
        newAct.triggered.connect(self.save)
        newAct.setShortcut(QKeySequence("Ctrl+S"))
        self.addAction(newAct)

    def open(self):
        if not isdir("shaders"):
            os.mkdir("shaders")

        value, ok = QInputDialog().getText(self, "Shader Name", "Shader Name:")
        self.name = value
        messenger.send("name", sentArgs=[value])

        for x in ["Vertex", "Fragment", "Geometry", "Tess Hull", "Tess Domain"]:
            _x = names[x]
            if isfile(f"shaders/{self.name}{_x}"):
                with open(f"shaders/{self.name}{_x}", "r") as f:
                    try:
                        text = f.read()
                        self.shaders[x].setPlainText(text)
                    except:
                        pass
            else:
                self.save()
                return

    def save(self):
        if self.name:
            if not isdir("shaders"):
                os.mkdir("shaders")
            for x in ["Vertex", "Fragment", "Geometry", "Tess Hull", "Tess Domain"]:
                _x = names[x]
                text = self.shaders[x].toPlainText()
                if text.strip():
                    with open(f"shaders/{self.name}{_x}", "w") as f:
                        try:
                            f.write(text)
                        except:
                            pass

    def add_tab(self, name, default):
        t = QPlainTextEdit(self)
        t.setPlainText(default)
        self.shaders[name] = t
        t.textChanged.connect(self.apply_shaders)
        t.textChanged.connect(self.save)
        self.tb.addTab(t, name)

    def apply_shaders(self):
        try:
            shaders = {"vertex": self.shaders["Vertex"].toPlainText(),
                       "fragment": self.shaders["Fragment"].toPlainText(),
                       "geometry": self.shaders["Geometry"].toPlainText(),
                       "tess_control": self.shaders["Tess Hull"].toPlainText(),
                       "tess_evaluation": self.shaders["Tess Domain"].toPlainText()}
            kwargs = {}
            for key, value in shaders.items():
                if value != "":
                    kwargs[key] = value
            render.set_shader(Shader.make(Shader.SL_GLSL, **kwargs))
        except:
            pass


App = QApplication(sys.argv)
window = ShaderEditor()
m = QMainWindow()
game.accept("name", lambda x: m.setWindowTitle(f"Shader {x}"))
m.setCentralWidget(window)
m.setGeometry(500, 100, 500, 500)

menu = m.menuBar()
fileMenu = menu.addMenu('File')
newAct = QAction('New', m)
newAct.triggered.connect(window.open)
fileMenu.addAction(newAct)
m.show()
window.open()

sys.exit(App.exec())
