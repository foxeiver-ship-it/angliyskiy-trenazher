#!/usr/bin/env python3
"""Собирает trainer/build/демо.js из демоверсии программы вступительного испытания.

Источник: ~/Documents/Экзамен-английский/демо-2025.json — 25 заданий с
официальными ключами из PDF программы 2025 года. В отличие от банка эти
вопросы живут отдельно: они не подмешиваются в темы, вариант экзамена и
режим «весь банк», а показываются одним фиксированным блоком.

Рубрикатор тем берётся из собрать-банк.py, чтобы номера тем совпадали.

Запуск: python3 trainer/собрать-демо.py
"""

import importlib.util
import json
from pathlib import Path

КОРЕНЬ = Path(__file__).resolve().parent.parent
ИСТОЧНИК = Path.home() / "Documents" / "Экзамен-английский" / "демо-2025.json"
ВЫХОД = КОРЕНЬ / "trainer" / "build" / "демо.js"

ТИПЫ = {"multichoice": "one", "match": "match", "gaps": "gaps"}


def порядок_тем():
    спец = importlib.util.spec_from_file_location(
        "собрать_банк", Path(__file__).resolve().parent / "собрать-банк.py"
    )
    модуль = importlib.util.module_from_spec(спец)
    спец.loader.exec_module(модуль)
    return модуль.ПОРЯДОК_ТЕМ


def main():
    данные = json.loads(ИСТОЧНИК.read_text(encoding="utf-8"))
    темы = порядок_тем()
    номер = {т: i for i, т in enumerate(темы)}

    демо = []
    for в in данные["вопросы"]:
        if в["тема"] not in номер:
            raise SystemExit("тема вне рубрикатора: " + в["тема"])
        вопрос = {
            "id": в["id"],
            "t": номер[в["тема"]],
            "ty": ТИПЫ[в["тип"]],
            "блок": в["блок"],
            "q": в["текст"],
            "qru": в.get("текст_ru", ""),
            "o": [],
            "oru": [],
            "a": [],
            "pairs": [],
            "pairsru": [],
            "pool": [],
            "poolru": {},
            "ans": "",
            "img": None,
            "oimg": [],
            "e": в["e"],
            "w": в["w"],
            "k": в["k"],
        }
        if в["тип"] == "multichoice":
            вопрос["o"] = [х["текст"] for х in в["варианты"]]
            вопрос["oru"] = [х["ru"] for х in в["варианты"]]
            вопрос["a"] = [i for i, х in enumerate(в["варианты"]) if х["верный"]]
            вопрос["oimg"] = [None] * len(вопрос["o"])
            if len(вопрос["a"]) != 1:
                raise SystemExit("в демоверсии ожидается один верный вариант: " + в["id"])
        else:
            вопрос["pairs"] = [{"l": п["слева"], "r": п["справа"]} for п in в["пары"]]
            # у текстов с пропусками слева стоит только номер — переводить нечего
            вопрос["pairsru"] = [п.get("слева_ru", "") for п in в["пары"]]
            вопрос["pool"] = list(в["пул"])
            вопрос["poolru"] = dict(в["пул_ru"])
            лишние = {п["r"] for п in вопрос["pairs"]} - set(вопрос["pool"])
            if лишние:
                raise SystemExit("ответ вне пула у " + в["id"] + ": " + ", ".join(лишние))
        демо.append(вопрос)

    строки = [
        "// Файл собран скриптом trainer/собрать-демо.py — правки вносите в источники.",
        "window.ДЕМО = [",
    ]
    строки += [json.dumps(в, ensure_ascii=False) + "," for в in демо]
    строки.append("];")
    текст = "\n".join(строки) + "\n"
    if "</script" in текст.lower():
        raise SystemExit("в демоверсии встретился '</script'")
    ВЫХОД.write_text(текст, encoding="utf-8")

    print("Заданий демоверсии: %d, размер: %d КБ" % (len(демо), len(текст) // 1024))


if __name__ == "__main__":
    main()
