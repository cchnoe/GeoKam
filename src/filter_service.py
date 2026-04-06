import pandas as pd


class FilterService:
    def get_options(self, df: pd.DataFrame, col: str) -> list[str]:
        if col not in df.columns:
            return []
        values = (
            df[col]
            .dropna()
            .astype(str)
            .str.strip()
        )
        values = values[values != ""]
        return sorted(values.unique().tolist())

    def filter_by_values(self, df: pd.DataFrame, col: str, selected: list[str]) -> pd.DataFrame:
        if col not in df.columns or not selected:
            return df.copy()
        return df[df[col].isin(selected)].copy()

    def filter_by_address_keys(
        self,
        df: pd.DataFrame,
        selected_keys: list[str],
        address_col: str = "nbr_direccion",
        id_col: str = "sk_comercio"
    ) -> pd.DataFrame:
        if not selected_keys:
            return df.copy()

        combo_key = (
            df[id_col].fillna("").astype(str).str.strip()
            + " || "
            + df[address_col].fillna("").astype(str).str.strip()
        )
        result = df[combo_key.isin(selected_keys)].copy()
        # Por defecto, ocultar la columna de id comercial en el resultado
        if id_col in result.columns:
            result = result.drop(columns=[id_col])
        return result

    def get_options_with_filters(self, df: pd.DataFrame, filters: dict, col: str) -> list[str]:
        """Obtener opciones para `col` aplicando los filtros actuales.

        `filters` debe ser un dict donde las claves son nombres de columna
        y los valores son listas de valores seleccionados para filtrar.
        La función aplica todos los filtros excepto el de la propia columna
        objetivo para evitar eliminar sus opciones.
        """
        if col not in df.columns:
            return []

        filtered = df
        for fcol, selected in (filters or {}).items():
            if fcol == col or not selected:
                continue
            if fcol in filtered.columns:
                filtered = self.filter_by_values(filtered, fcol, selected)

        return self.get_options(filtered, col)