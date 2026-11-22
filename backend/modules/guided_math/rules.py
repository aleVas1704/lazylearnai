"""Reglas matemáticas deterministas: la IA no decide si una fracción es correcta."""

import math
import re
import unicodedata
from fractions import Fraction

EXERCISE_COUNT = 10
STAGES = ("concept", "mcm", "equivalents", "result", "done")


def validate_exercises(value: object) -> list[dict[str, int | str]]:
    """Solo 10 sumas/restas de fracciones heterogéneas de complejidad de 1ro."""
    if not isinstance(value, list) or len(value) != EXERCISE_COUNT:
        raise ValueError("Gemini debe producir exactamente 10 ejercicios.")
    result: list[dict[str, int | str]] = []
    for row in value:
        if not isinstance(row, dict):
            raise TypeError("Formato de ejercicio inválido.")
        keys = ("a_num", "a_den", "operator", "b_num", "b_den")
        if not all(k in row for k in keys):
            raise ValueError("El ejercicio no contiene todos los campos.")
        a, ad, op, b, bd = (row[k] for k in keys)
        if any(type(n) is not int for n in (a, ad, b, bd)):
            raise ValueError("Los valores de las fracciones deben ser enteros.")
        if not (1 <= a <= 20 and 2 <= ad <= 24 and 1 <= b <= 20 and 2 <= bd <= 24):
            raise ValueError("Valores de fracciones fuera del rango del MVP.")
        if op not in ("+", "-") or ad == bd:
            raise ValueError("Se requieren operaciones heterogéneas de suma o resta.")
        result.append(dict(zip(keys, (a, ad, op, b, bd))))
    return result


def expression(ex: dict) -> str:
    return f"{ex['a_num']}/{ex['a_den']} {ex['operator']} {ex['b_num']}/{ex['b_den']}"


def normalize(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text.casefold()) if unicodedata.category(c) != "Mn"
    )


def asks_for_answer(text: str) -> bool:
    norm = normalize(text)
    return bool(
        re.search(
            r"(resultado final|respuesta final|dame (el |la )?(resultado|respuesta|solucion)"
            r"|solo (la |el )?(respuesta|resultado)|hazlo por mi|resuelvelo todo|tengo prisa)",
            norm,
        )
    )


def first_prompt(ex: dict, index: int) -> str:
    prefix = "¡Hola! El profesor te asignó 10 ejercicios de fracciones. " if index == 1 else ""
    return (
        f"{prefix}Ejercicio {index}/10: {expression(ex)}. "
        "Como los denominadores son distintos, ¿cuál es el primer paso para poder operar?"
    )


def next_step(ex: dict, index: int, stage: str, message: str) -> tuple[str, str, bool]:
    """Retorna (respuesta, etapa_siguiente, ejercicio_terminado). Nunca adelanta la solución."""
    norm = normalize(message)
    answer_request = asks_for_answer(message)
    if answer_request or re.search(r"[¿?]|\b(no se|no entiendo|como|que es|sera|quizas)\b", norm):
        return "Vamos paso a paso. ¿Qué parte necesitas que te explique?", stage, False
    refusal = (
        "Entiendo que quieras avanzar rápido, pero te guiaré sin darte la respuesta final. "
        if answer_request
        else ""
    )
    lcm = math.lcm(ex["a_den"], ex["b_den"])
    if stage == "concept":
        if "mcm" in norm or "minimo comun multiplo" in norm or "denominador comun" in norm:
            return (
                refusal
                + (
                    f"¡Exacto! ¿Cuál es el mínimo común múltiplo entre "
                    f"{ex['a_den']} y {ex['b_den']}?"
                ),
                "mcm",
                False,
            )
        return (
            refusal
            + (
                f"Pista: necesitamos un denominador común para {ex['a_den']} y "
                f"{ex['b_den']}. ¿Cómo se llama el menor múltiplo que comparten?"
            ),
            "concept",
            False,
        )
    if stage == "mcm":
        numbers = [int(n) for n in re.findall(r"(?<![\d/])\d+(?![\d/])", norm)]
        if lcm in numbers:
            return (
                refusal
                + (
                    f"Correcto, el MCM es {lcm}. Ahora, con denominador {lcm}, "
                    "¿cómo quedan convertidas las dos fracciones?"
                ),
                "equivalents",
                False,
            )
        return (
            refusal
            + (
                f"Piensa en los múltiplos de {ex['a_den']} y de {ex['b_den']}. "
                "Busca el más pequeño que aparece en las dos listas."
            ),
            "mcm",
            False,
        )
    if stage == "equivalents":
        pairs = [(int(n), int(d)) for n, d in re.findall(r"(-?\d+)\s*/\s*(\d+)", norm)]
        left = (ex["a_num"] * (lcm // ex["a_den"]), lcm)
        right = (ex["b_num"] * (lcm // ex["b_den"]), lcm)
        if len(pairs) >= 2 and pairs[:2] == [left, right]:
            return (
                refusal
                + (
                    "¡Muy bien! Ahora que ambas tienen el mismo denominador, "
                    f"¿qué debes hacer con los numeradores para {ex['operator']}? "
                    "Escribe el resultado como fracción."
                ),
                "result",
                False,
            )
        return (
            refusal
            + (
                f"Para convertir una fracción a denominador {lcm}, multiplica su "
                "numerador y denominador por el mismo número. "
                "Escribe ambas fracciones en el orden original."
            ),
            "equivalents",
            False,
        )
    if stage == "result":
        fractions = re.findall(r"(-?\d+)\s*/\s*(\d+)", norm)
        left = Fraction(ex["a_num"], ex["a_den"])
        right = Fraction(ex["b_num"], ex["b_den"])
        expected = left + right if ex["operator"] == "+" else left - right
        if fractions:
            n, d = (int(x) for x in fractions[0])
            if d != 0 and Fraction(n, d) == expected:
                return f"¡Excelente! Resuelves el ejercicio {index} correctamente.", "done", True
        return (
            refusal
            + (
                f"Ya tienes denominador {lcm}. "
                "Opera los numeradores y conserva ese denominador. "
                "Revisa tu cálculo e intenta nuevamente."
            ),
            "result",
            False,
        )
    return "La tarea ya está completada. ¡Buen trabajo!", "done", False
