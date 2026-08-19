#!/usr/bin/env python3
"""Собирает trainer/build/памятки.js из markdown-памяток проекта-источника.

Каждой теме тренажёра соответствует один файл разбор/памятки/NN-*.md,
где NN — номер темы начиная с 01. Markdown переводится в HTML своим
минимальным конвертером: внешних зависимостей у проекта нет и не будет.

Запуск: python3 trainer/собрать-памятки.py
"""

import html
import json
import re
from pathlib import Path

КОРЕНЬ = Path(__file__).resolve().parent.parent
ИСТОЧНИК = Path.home() / "Documents" / "Экзамен-английский" / "разбор" / "памятки"
ВЫХОД = КОРЕНЬ / "trainer" / "build" / "памятки.js"


def строчное(текст):
    """**жирный**, *курсив* и `код` внутри строки."""
    т = html.escape(текст)
    т = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", т)
    т = re.sub(r"(?<![\w*])\*([^*]+?)\*(?![\w*])", r"<i>\1</i>", т)
    т = re.sub(r"`(.+?)`", r"<code>\1</code>", т)
    return т


def ячейки(строка):
    return [к.strip() for к in строка.strip().strip("|").split("|")]


def разделитель(строка):
    return bool(re.fullmatch(r"\|[\s:|-]+\|", строка.strip()))


def в_html(текст):
    строки = текст.splitlines()
    out, i = [], 0
    абзац = []

    def сбросить():
        if абзац:
            out.append("<p>" + строчное(" ".join(абзац)) + "</p>")
            абзац.clear()

    while i < len(строки):
        s = строки[i]
        голая = s.strip()

        if not голая:
            сбросить()
            i += 1
            continue

        з = re.match(r"^(#{1,4})\s+(.*)$", голая)
        if з:
            сбросить()
            ур = min(len(з.group(1)) + 1, 5)  # # → h2, чтобы не спорить с h1 страницы
            имя = з.group(2)
            # {программа} в конце заголовка — раздел дописан по программе вуза,
            # а не выведен из вопросов банка; в тренажёре он другого цвета
            из_программы = имя.endswith("{программа}")
            if из_программы:
                имя = имя[: -len("{программа}")].rstrip()
            класс = ' class="prog"' if из_программы else ""
            out.append("<h%d%s>%s</h%d>" % (ур, класс, строчное(имя), ур))
            i += 1
            continue

        # таблица: строка с | и следующая — разделитель
        if голая.startswith("|") and i + 1 < len(строки) and разделитель(строки[i + 1]):
            сбросить()
            шапка = ячейки(голая)
            i += 2
            тело = []
            while i < len(строки) and строки[i].strip().startswith("|"):
                тело.append(ячейки(строки[i]))
                i += 1
            t = ["<table><thead><tr>"]
            t += ["<th>%s</th>" % строчное(к) for к in шапка]
            t.append("</tr></thead><tbody>")
            for р in тело:
                t.append("<tr>" + "".join("<td>%s</td>" % строчное(к) for к in р) + "</tr>")
            t.append("</tbody></table>")
            out.append("".join(t))
            continue

        сп = re.match(r"^[-*]\s+(.*)$", голая)
        ном = re.match(r"^\d+\.\s+(.*)$", голая)
        if сп or ном:
            сбросить()
            тег = "ul" if сп else "ol"
            пункты = []
            while i < len(строки):
                г = строки[i].strip()
                м = re.match(r"^[-*]\s+(.*)$" if сп else r"^\d+\.\s+(.*)$", г)
                if not м:
                    break
                пункты.append("<li>%s</li>" % строчное(м.group(1)))
                i += 1
            out.append("<%s>%s</%s>" % (тег, "".join(пункты), тег))
            continue

        абзац.append(голая)
        i += 1

    сбросить()
    return "".join(out)


def main():
    файлы = sorted(п for п in ИСТОЧНИК.glob("*.md") if not п.name.startswith("_"))
    if not файлы:
        raise SystemExit("нет памяток в " + str(ИСТОЧНИК))

    памятки = {}
    for п in файлы:
        з = re.match(r"^(\d+)-", п.name)
        if not з:
            raise SystemExit("имя без номера темы: " + п.name)
        тема = int(з.group(1)) - 1
        памятки[str(тема)] = в_html(п.read_text(encoding="utf-8"))

    строка = json.dumps(памятки, ensure_ascii=False)
    if "</script" in строка.lower():
        raise SystemExit("в памятках встретился '</script'")
    ВЫХОД.write_text(
        "// Файл собран скриптом trainer/собрать-памятки.py — правки вносите в источники.\n"
        "window.ПАМЯТКИ = " + строка + ";\n",
        encoding="utf-8",
    )
    print("Памяток: %d, размер: %d КБ" % (len(памятки), len(строка) // 1024))


if __name__ == "__main__":
    main()
