# -*- coding: utf-8 -*-
"""Сборка тренажёра в один самодостаточный файл.

Склеивает куски из trainer/build/ в ../trenazher.html:
  * все *.html из build/ берутся по алфавиту имён (01-стили, 02-разметка,
    03..06 — логика), поэтому порядок предсказуем и новый кусок достаточно
    просто положить рядом с нужным номером;
  * все *.js из build/ вставляются отдельными <script> перед первым куском
    логики, чтобы window.ТЕМЫ, window.БАНК и window.ПАМЯТКИ уже существовали
    к моменту запуска;
  * ничего не грузится из сети — результат открывается по file://.
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
DEST = os.path.join(os.path.dirname(ROOT), "trenazher.html")

HEAD_MARK = "02-"          # после этого куска идёт разметка, дальше — банк и логика
BANK = "банк.js"


def read(path):
    return io.open(path, encoding="utf-8").read().rstrip() + "\n"


def main():
    if not os.path.isdir(BUILD):
        sys.exit("нет каталога " + BUILD)

    parts = sorted(f for f in os.listdir(BUILD) if f.endswith(".html"))
    if not parts:
        sys.exit("в build/ нет кусков *.html")

    data_parts = sorted(f for f in os.listdir(BUILD) if f.endswith(".js"))
    if BANK not in data_parts:
        sys.exit("нет файла " + os.path.join(BUILD, BANK))
    data = []
    for f in data_parts:
        текст = read(os.path.join(BUILD, f))
        if "</script" in текст.lower():
            sys.exit("в " + f + " встретился '</script' — файл нельзя вставить инлайн")
        data.append(текст)

    # первый кусок — <head> (стили и мета), остальные — тело страницы
    head_parts = [f for f in parts if f.startswith("01-")]
    body_parts = [f for f in parts if not f.startswith("01-")]
    if not head_parts:
        sys.exit("не нашёлся кусок 01-* со стилями")

    # логика — всё, что идёт после куска разметки
    markup = [f for f in body_parts if f.startswith(HEAD_MARK)]
    logic = [f for f in body_parts if not f.startswith(HEAD_MARK)]

    out = ["<!doctype html>", '<html lang="ru">', "<head>"]
    out += [read(os.path.join(BUILD, f)) for f in head_parts]
    out += ["</head>", "<body>"]
    out += [read(os.path.join(BUILD, f)) for f in markup]
    for текст in data:
        out += ["<script>", текст, "</script>"]
    out += [read(os.path.join(BUILD, f)) for f in logic]
    out += ["</body>", "</html>", ""]

    io.open(DEST, "w", encoding="utf-8").write("\n".join(out))
    size = os.path.getsize(DEST)
    print("куски:", ", ".join(head_parts + markup + data_parts + logic))
    print("OK", DEST, size, "байт")


if __name__ == "__main__":
    main()
