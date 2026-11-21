def prepare_preview(text: str) -> str:
    """Ejemplo reemplazable: no guarda información ni asume un reto educativo."""
    cleaned = " ".join(text.strip().split())
    return cleaned[:80] if cleaned else "Sin tema seleccionado"
