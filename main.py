import ast
import operator as op
from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle

OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}

def safe_calculate(expression):
    """Evaluate only numbers and basic arithmetic operators."""
    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            return OPS[type(node.op)](walk(node.left), walk(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
            return OPS[type(node.op)](walk(node.operand))
        raise ValueError("Unsupported expression")
    return walk(ast.parse(expression, mode="eval"))

class CalcButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.color = (0.96, 0.97, 1, 1)
        self.font_size = "23sp"
        self.bold = True

class CalculatorRoot(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(18), spacing=dp(12), **kwargs)
        self.expression = ""
        self.just_calculated = False
        with self.canvas.before:
            Color(0.055, 0.075, 0.12, 1)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[0])
        self.bind(pos=self._update_bg, size=self._update_bg)

        header = BoxLayout(size_hint_y=None, height=dp(48), padding=(dp(4), 0))
        title = Label(text="[b]CALCULATOR[/b]", markup=True, font_size="18sp",
                      color=(0.45, 0.83, 1, 1), halign="left", valign="middle")
        title.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        header.add_widget(title)
        self.add_widget(header)

        self.history = Label(text="Ready", size_hint_y=None, height=dp(28),
                             font_size="15sp", color=(0.55, 0.63, 0.75, 1),
                             halign="right", valign="middle")
        self.history.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.add_widget(self.history)

        self.display = Label(text="0", font_size="42sp", bold=True,
                             color=(1, 1, 1, 1), halign="right", valign="middle",
                             size_hint_y=0.32)
        self.display.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.add_widget(self.display)

        keys = [
            ("AC", "clear"), ("⌫", "back"), ("%", "percent"), ("÷", "/"),
            ("7", "7"), ("8", "8"), ("9", "9"), ("×", "*"),
            ("4", "4"), ("5", "5"), ("6", "6"), ("−", "-"),
            ("1", "1"), ("2", "2"), ("3", "3"), ("+", "+"),
            ("±", "sign"), ("0", "0"), (".", "."), ("=", "equals"),
        ]
        grid = GridLayout(cols=4, rows=5, spacing=dp(9), size_hint_y=0.95)
        for label, value in keys:
            if value in ("clear", "back", "percent"):
                color = (0.17, 0.23, 0.34, 1)
            elif value in ("/", "*", "-", "+"):
                color = (0.10, 0.42, 0.63, 1)
            elif value == "equals":
                color = (0.10, 0.68, 0.58, 1)
            else:
                color = (0.12, 0.16, 0.24, 1)
            btn = CalcButton(text=label, background_color=color)
            btn.bind(on_release=lambda instance, v=value: self.press(v))
            grid.add_widget(btn)
        self.add_widget(grid)

        footer = Label(text="Simple • Fast • Offline", size_hint_y=None, height=dp(24),
                       font_size="12sp", color=(0.40, 0.49, 0.62, 1))
        self.add_widget(footer)

    def _update_bg(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def _refresh(self):
        self.display.text = self.expression if self.expression else "0"

    def press(self, value):
        if value == "clear":
            self.expression = ""
            self.history.text = "Ready"
            self.just_calculated = False
            self._refresh()
            return
        if value == "back":
            self.expression = self.expression[:-1]
            self.just_calculated = False
            self._refresh()
            return
        if value == "sign":
            # Toggle the sign of the last number in the expression.
            import re
            match = re.search(r'(\d*\.?\d+)$', self.expression)
            if match:
                start, end = match.span()
                number = match.group(1)
                prefix = self.expression[:start]
                if prefix.endswith("-") and (len(prefix) == 1 or prefix[-2] in "+-*/"):
                    prefix = prefix[:-1]
                else:
                    prefix += "-"
                self.expression = prefix + number + self.expression[end:]
            elif not self.expression:
                self.expression = "-"
            self.just_calculated = False
            self._refresh()
            return
        if value == "percent":
            import re
            match = re.search(r'(\d*\.?\d+)$', self.expression)
            if match:
                number = float(match.group(1)) / 100
                self.expression = self.expression[:match.start()] + str(number)
            self.just_calculated = False
            self._refresh()
            return
        if value == "equals":
            if not self.expression:
                return
            try:
                result = safe_calculate(self.expression)
                shown = f"{result:.10g}"
                self.history.text = self.expression.replace("*", "×").replace("/", "÷").replace("-", "−") + " ="
                self.expression = shown
                self.just_calculated = True
            except ZeroDivisionError:
                self.history.text = "Cannot divide by zero"
                self.expression = ""
            except Exception:
                self.history.text = "Check your expression"
                self.expression = ""
            self._refresh()
            return

        if value in ("+", "-", "*", "/"):
            if not self.expression:
                if value == "-":
                    self.expression = "-"
                else:
                    return
            elif self.expression[-1] in "+-*/":
                self.expression = self.expression[:-1] + value
            else:
                self.expression += value
            self.just_calculated = False
            self._refresh()
            return

        if value == ".":
            import re
            last = re.search(r'(\d*\.?\d*)$', self.expression)
            chunk = last.group(1) if last else ""
            if "." in chunk:
                return
            if not chunk:
                self.expression += "0"
            self.expression += "."
        else:
            if self.just_calculated:
                self.expression = ""
                self.history.text = "Ready"
                self.just_calculated = False
            if len(self.expression) < 32:
                self.expression += value
        self._refresh()

class RafiqCalculatorApp(App):
    title = "Rafiq Calculator"

    def build(self):
        Window.clearcolor = (0.055, 0.075, 0.12, 1)
        return CalculatorRoot()

if __name__ == "__main__":
    RafiqCalculatorApp().run()
