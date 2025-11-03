import re

class GFXParser:
    def __init__(self, code: str):
        self.code = code
        self.objects = []

    def parse(self):
        """Парсит код .gfx в список объектов"""
        pattern = r"Create\s+(\w+)\s*\((.*?)\)\s*{"
        for match in re.finditer(pattern, self.code):
            obj_type = match.group(1)
            params = self._parse_params(match.group(2))
            style = self._extract_style(self.code[match.end():])
            self.objects.append({"type": obj_type, "params": params, "style": style})
        return self.objects

    def _parse_params(self, param_str: str):
        params = {}
        for p in param_str.split(","):
            if ":" in p:
                k, v = p.split(":")
                params[k.strip()] = int(v.strip())
        return params

    def _extract_style(self, code_part: str):
        style_match = re.search(r"Style\s*{([^}]*)}", code_part)
        if not style_match:
            return {}
        style_str = style_match.group(1)
        style = {}
        for s in style_str.split(";"):
            if ":" in s:
                k, v = s.split(":")
                style[k.strip()] = v.strip()
        return style
