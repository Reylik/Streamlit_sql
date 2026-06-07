"""
Chargement et validation de la configuration YAML / TOML.
"""
import os
import streamlit as st

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.yaml")


def _validate_config(data: dict) -> None:
    """Lève ValueError si le fichier de config est mal formé."""
    for key in ("schema", "enrich"):
        if key not in data:
            raise ValueError(f"Clé '{key}' manquante dans le fichier de config.")

    schema = data["schema"]
    for table, info in schema.items():
        if "columns" not in info:
            raise ValueError(f"schema.{table} : 'columns' manquant.")
        if "pk" not in info:
            raise ValueError(f"schema.{table} : 'pk' manquant.")
        if info["pk"] not in info["columns"]:
            raise ValueError(f"schema.{table} : pk '{info['pk']}' absent de columns.")
        for fk in info.get("fk") or []:
            for k in ("col", "ref", "ref_col"):
                if k not in fk:
                    raise ValueError(f"schema.{table}.fk : clé '{k}' manquante.")
            if fk["ref"] not in schema:
                raise ValueError(f"schema.{table}.fk : table '{fk['ref']}' inexistante.")


@st.cache_data
def _load_config_cached(path: str, mtime: float) -> dict:
    """Lit et valide le fichier de config (cache invalidé si mtime change)."""
    with open(path, "rb") as fh:
        raw = fh.read()

    if path.endswith(".toml"):
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        data = tomllib.loads(raw.decode("utf-8"))
    else:
        import yaml
        data = yaml.safe_load(raw)

    for info in data.get("schema", {}).values():
        if info.get("fk") is None:
            info["fk"] = []

    _validate_config(data)
    return data


def load_config(path: str = CONFIG_PATH) -> dict:
    """
    Charge la config depuis un fichier YAML ou TOML.
    Rechargement automatique dès que le fichier est modifié sur disque.
    """
    try:
        mtime = os.path.getmtime(path)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Fichier de config introuvable : {path}\n"
            "Créez config.yaml (ou config.toml) dans le même répertoire que app.py."
        )
    return _load_config_cached(path, mtime)
