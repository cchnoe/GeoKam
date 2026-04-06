import streamlit as st
import pandas as pd


class UIService:
    def multiselect_with_all(self, label: str, options: list[str], key: str) -> list[str]:
        if not options:
            st.multiselect(label, [], default=[], key=key, disabled=True)
            return []

        select_all = st.checkbox(f"Seleccionar todos en {label}", value=False, key=f"{key}_all")

        if select_all:
            selected = st.multiselect(label, options, default=options, key=key)
        else:
            selected = st.multiselect(label, options, default=[], key=key)

        return selected

    def address_checkboxes(
        self,
        df: pd.DataFrame,
        address_col: str = "nbr_direccion",
        group_col: str = "grupo_economico",
        id_col: str = "sk_comercio"
    ) -> list[str]:
        if df.empty:
            st.info("No hay direcciones disponibles con los filtros actuales.")
            return []

        work = df[[group_col, address_col, id_col]].copy()
        work[group_col] = work[group_col].fillna("").astype(str).str.strip()
        work[address_col] = work[address_col].fillna("").astype(str).str.strip()
        work[id_col] = work[id_col].fillna("").astype(str).str.strip()

        work = work.drop_duplicates().sort_values([group_col, address_col])

        selected_keys = []

        grupos = work[group_col].dropna().unique().tolist()

        for grupo in grupos:
            if not grupo:
                grupo = "SIN GRUPO"

            st.markdown(f"**{grupo}**")
            bloque = work[work[group_col] == grupo].copy()

            cols = st.columns(2)
            for i, (_, row) in enumerate(bloque.iterrows()):
                key_value = f"{row[id_col]} || {row[address_col]}"
                label = row[address_col] if row[address_col] else f"Dirección sin nombre ({row[id_col]})"

                with cols[i % 2]:
                    checked = st.checkbox(label, key=f"address_{key_value}")
                    if checked:
                        selected_keys.append(key_value)

        return selected_keys