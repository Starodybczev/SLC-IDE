import os
import re

class GFXParser:
    def __init__(self, code: str, filename: str = None):
        self.code = code.strip()
        self.objects = []
        self.filename = os.path.splitext(os.path.basename(filename))[0] if filename else None
        self.used_shape_names = set()

    def parse(self):
        """Парсит код SLC и проверяет все имена"""
        self.objects.clear()
        
        if not self.code:
            print("📄 Пустой файл — ничего не парсим.")
            return []

        # === Проверка блока Create List ===
        list_match = re.search(r"Create\s+List\s+([A-Za-z_]\w*)\s*\(\)\s*{", self.code)
        if not list_match:
            raise SyntaxError("❌ Ожидалось объявление 'Create List <Name>() {'")

        list_name = list_match.group(1)

        # 1️⃣ List должен быть с заглавной буквы
        if not list_name[0].isupper():
            raise SyntaxError(f"❌ Имя списка '{list_name}' должно начинаться с большой буквы")

        # 2️⃣ List должен совпадать с именем файла
        if self.filename and list_name != self.filename:
            raise SyntaxError(
                f"❌ Имя списка '{list_name}' должно совпадать с именем файла '{self.filename}'"
            )

        # === Проверка фигур ===
        shape_pattern = r"Create\s+([A-Z]\w*)\s+([A-Z]\w*)\s*\((.*?)\)\s*{"
        shapes = list(re.finditer(shape_pattern, self.code))

        if not shapes:
            raise SyntaxError(
                "❌ Не найдено фигур. Каждая фигура должна быть вида: 'Create ShapeType ShapeName(x:..., y:...) {'"
            )

        for match in shapes:
            shape_type = match.group(1)
            shape_name = match.group(2)
            params_str = match.group(3)

            # 1️⃣ Имя фигуры обязательно
            if not shape_name:
                line = self._find_line(match.start())
                raise SyntaxError(f"❌ У фигуры '{shape_type}' отсутствует имя (строка {line})")

            # 2️⃣ Имя фигуры не 'List'
            if shape_name.lower() == "list":
                line = self._find_line(match.start())
                raise SyntaxError(f"❌ Имя фигуры не может быть 'List' (строка {line})")

            # 3️⃣ Имя с большой буквы
            if not shape_name[0].isupper():
                line = self._find_line(match.start())
                raise SyntaxError(f"❌ Имя фигуры '{shape_name}' должно начинаться с большой буквы (строка {line})")

            # 4️⃣ Имя уникально
            if shape_name in self.used_shape_names:
                line = self._find_line(match.start())
                raise SyntaxError(f"❌ Повторяющееся имя фигуры '{shape_name}' (строка {line})")

            self.used_shape_names.add(shape_name)

            # 5️⃣ Парсим параметры (без краша)
            try:
                params = self._parse_params(params_str)
            except SyntaxError as e:
                raise e
            except Exception:
                params = {}

            # 6️⃣ Проверяем наличие блока Style
            code_after = self.code[match.end():]
            style = {}
            style_match = re.search(r"Style\s*{([^}]*)}", code_after)
            if not style_match:
                line = self._find_line(match.end())
                raise SyntaxError(f"❌ Отсутствует блок 'Style {{ ... }}' после {shape_name} (строка {line})")

            try:
                style = self._extract_style(code_after)
            except Exception:
                style = {}

            # ✅ Добавляем объект в структуру (ключ 'type' обязателен!)
            self.objects.append({
                "type": shape_type,   # для gfx_canvas.py
                "name": shape_name,
                "params": params,
                "style": style
            })

        return self.objects

    # === Вспомогательные методы ===
    def _find_line(self, index: int) -> int:
        return self.code.count("\n", 0, index) + 1

    def _parse_params(self, param_str: str):
        params = {}
        if not param_str.strip():
            return params

        for p in param_str.split(","):
            p = p.strip()
            if not p:
                continue
            if ":" not in p:
                raise SyntaxError(f"❌ Неверный параметр: '{p}', ожидалось 'ключ:значение'")
            k, v = [x.strip() for x in p.split(":", 1)]

            # тип значения
            if re.match(r"^-?\d+(\.\d+)?$", v):
                val = float(v) if "." in v else int(v)
            elif re.match(r"^['\"].*['\"]$", v):
                val = v.strip("'\"")
            else:
                raise SyntaxError(f"❌ Некорректное значение параметра '{k}': '{v}'")
            params[k] = val

        return params

    def _extract_style(self, text: str):
        styles = {}
        match = re.search(r"Style\s*{([^}]*)}", text)
        if not match:
            return styles
        for line in match.group(1).split(";"):
            if ":" in line:
                k, v = [x.strip() for x in line.split(":", 1)]
                if k and v:
                    styles[k] = v
        return styles
