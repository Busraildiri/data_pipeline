from importlib import import_module


WRITER_MODULES = {
    "mysql": "src.load.mysql_writer",
    "postgres": "src.load.postgres_writer",
}


def get_writer(target: str):
    """Mock hedefi için writer modülünü döndürür."""
    normalized_target = (target or "").strip().lower()
    module_name = WRITER_MODULES.get(normalized_target)
    if module_name is None:
        allowed = ", ".join(sorted(WRITER_MODULES))
        raise ValueError(
            f"Geçersiz MOCK_TARGET={target!r}. Desteklenen değerler: {allowed}"
        )
    return import_module(module_name)
