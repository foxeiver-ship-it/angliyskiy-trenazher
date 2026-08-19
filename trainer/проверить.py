#!/usr/bin/env python3
"""Структурная проверка банка перед сборкой.

Читает trainer/build/банк.js, разбирает объявления window.ТЕМЫ и window.БАНК
и проверяет каждый вопрос по СПЕЦИФИКАЦИЯ.md. Ненулевой код возврата означает,
что собирать нельзя.

Запуск: python3 trainer/проверить.py
"""

import json
import sys
from collections import Counter
from pathlib import Path

БАНК_JS = Path(__file__).resolve().parent / "build" / "банк.js"


def прочитать():
    темы, банк = [], []
    for строка in БАНК_JS.read_text(encoding="utf-8").splitlines():
        if строка.startswith("window.ТЕМЫ = "):
            темы = json.loads(строка[len("window.ТЕМЫ = ") : -1])
        elif строка.startswith('{"id"'):
            банк.append(json.loads(строка.rstrip(",")))
    return темы, банк


def main():
    темы, банк = прочитать()
    номера = {т["n"] for т in темы}
    беды = []

    for в in банк:
        и = в["id"]
        if в["t"] not in номера:
            беды.append(f"{и}: тема {в['t']} отсутствует в списке тем")
        for поле in ("q", "e", "k"):
            if not в[поле].strip():
                беды.append(f"{и}: пустое поле {поле}")
        if в["ty"] in ("one", "many"):
            if len(в["w"]) != len(в["o"]):
                беды.append(f"{и}: w={len(в['w'])}, вариантов {len(в['o'])}")
            if not в["a"]:
                беды.append(f"{и}: не отмечен ни один верный вариант")
            if в["ty"] == "one" and len(в["a"]) != 1:
                беды.append(f"{и}: тип one, а верных вариантов {len(в['a'])}")
            for i in в["a"]:
                if i < len(в["w"]) and в["w"][i]:
                    беды.append(f"{и}: у верного варианта {i} непустое пояснение")
            for i, п in enumerate(в["w"]):
                if i not in в["a"] and not п.strip():
                    беды.append(f"{и}: у неверного варианта {i} пустое пояснение")
        elif в["ty"] == "short":
            if not в["ans"].strip():
                беды.append(f"{и}: пустой эталонный ответ")
        elif в["ty"] == "match":
            if not в["pairs"]:
                беды.append(f"{и}: нет пар соответствия")
            for п in в["pairs"]:
                if п["r"] not in в["pool"]:
                    беды.append(f"{и}: ответ «{п['r']}» отсутствует в списке вариантов")
        else:
            беды.append(f"{и}: неизвестный тип {в['ty']}")

    повторы = [и for и, с in Counter(в["id"] for в in банк).items() if с > 1]
    беды += [f"{и}: дубль id" for и in повторы]

    по_темам = Counter(в["t"] for в in банк)
    print(f"Вопросов: {len(банк)}, тем: {len(темы)}")
    print("По типам:", dict(Counter(в["ty"] for в in банк)))
    for т in темы:
        print(f"  {т['n'] + 1:>2}. {т['название']} — {по_темам[т['n']]}")

    if беды:
        print(f"\nОШИБКИ ({len(беды)}):")
        for б in беды[:50]:
            print(" ", б)
        sys.exit(1)
    print("\nСтруктура в порядке.")


if __name__ == "__main__":
    main()
