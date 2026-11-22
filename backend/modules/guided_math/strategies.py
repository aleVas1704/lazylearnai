"""Estrategias cerradas por tema; Gemini nunca determina el progreso."""

import math
import re

from backend.modules.guided_math import rules


class Fractions:
    task_type = "fraction_add_sub"
    total_exercises = 10
    validate_plan = staticmethod(rules.validate_exercises)
    intro_message = staticmethod(rules.first_prompt)
    evaluate_response = staticmethod(rules.next_step)

    def completed_count(self, progress):
        if progress.get("stage") == "done" and progress.get("completed_at"):
            return self.total_exercises
        return max(0, min(self.total_exercises - 1, (progress.get("exercise_index") or 1) - 1))


class MCM(Fractions):
    task_type = "mcm"
    total_exercises = 1

    @staticmethod
    def validate_plan(value):
        if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], dict):
            raise ValueError("La actividad MCM necesita un ejercicio.")
        ex = value[0]
        if set(ex) != {"a", "b"} or any(
            type(ex[k]) is not int or not 1 <= ex[k] <= 100 for k in ("a", "b")
        ):
            raise ValueError("Usa dos enteros entre 1 y 100.")
        return [dict(ex)]

    @staticmethod
    def intro_message(ex, index=1):
        return (
            "Para sumar fracciones con distinto denominador necesitamos un denominador común. "
            f"¿Cuál es el mínimo común múltiplo (MCM) de {ex['a']} y {ex['b']}?"
        )

    @staticmethod
    def explanation(ex):
        return (
            "El MCM es el número positivo más pequeño que aparece entre los múltiplos de ambos números. "
            "Escribe los múltiplos de cada número, sumándolo una y otra vez, y busca el primero que se repite en ambas listas. "
            f"Inténtalo con {ex['a']} y {ex['b']}: ¿cuál es el menor que comparten?"
        )

    @staticmethod
    def evaluate_response(ex, index, stage, message):
        if stage == "done":
            return "Ya completaste esta actividad. ¡Buen trabajo!", "done", False
        # Gramática cerrada: no aceptar números incidentales, dudas ni sufijos arbitrarios.
        norm = rules.normalize(message).strip()
        match = re.fullmatch(
            r"(?:(?:es|el mcm es|el minimo comun multiplo es|la respuesta es)\s+)?"
            r"(\d{1,5})(?:\s*,?\s+porque es el (?:menor|minimo) multiplo comun)?[.!]?",
            norm,
        )
        expected = math.lcm(ex["a"], ex["b"])
        if match and int(match[1]) == expected:
            return (
                f"¡Correcto! El MCM de {ex['a']} y {ex['b']} es {expected}. Completaste esta actividad.",
                "done",
                True,
            )
        return MCM.explanation(ex), "concept", False

    @staticmethod
    def hidden_solution(ex, text):
        expected = math.lcm(ex["a"], ex["b"])
        norm = rules.normalize(text)
        # Palabras frecuentes de la demo además de representación numérica.
        words = {12: "doce", 6: "seis", 1: "uno", 2: "dos", 4: "cuatro"}
        return bool(
            re.search(rf"(?<!\d){expected}(?!\d)", norm)
            or (expected in words and re.search(rf"\b{words[expected]}\b", norm))
        )


STRATEGIES = {"fraction_add_sub": Fractions(), "mcm": MCM()}


def strategy(task_type=None):
    try:
        return STRATEGIES[task_type or "fraction_add_sub"]
    except (KeyError, TypeError):
        raise ValueError("Tipo de tarea no compatible.") from None


def progress_view(row):
    engine = strategy(row.get("task_type"))
    return {
        **row,
        "total_exercises": engine.total_exercises,
        "completed_count": engine.completed_count(row),
        "completed": row.get("stage") == "done" and bool(row.get("completed_at")),
    }
