"""Verificar sin acceder a Neon: ejemplo 3/4 + 1/6 y reglas del tutor."""

from backend.modules.guided_math.rules import first_prompt, next_step, validate_exercises

first = {"a_num": 3, "a_den": 4, "operator": "+", "b_num": 1, "b_den": 6}
other = {"a_num": 2, "a_den": 3, "operator": "-", "b_num": 1, "b_den": 4}
assert len(validate_exercises([first] + [other] * 9)) == 10
assert "3/4 + 1/6" in first_prompt(first, 1)
text, stage, done = next_step(first, 1, "concept", "Sacar el mínimo común múltiplo")
assert stage == "mcm" and not done
text, stage, done = next_step(first, 1, stage, "Es 12. Dame el resultado final, tengo prisa")
assert stage == "mcm" and not done
text, stage, done = next_step(first, 1, stage, "Es 12")
assert stage == "equivalents" and not done
text, stage, done = next_step(first, 1, stage, "9/12 y 2/12")
assert stage == "result" and not done
text, stage, done = next_step(first, 1, stage, "11/12")
assert stage == "done" and done
print("OK: 10 ejercicios, MCM, conversión, bloqueo de resultado, respuesta final")
