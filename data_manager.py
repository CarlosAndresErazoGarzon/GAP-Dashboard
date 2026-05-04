import pandas as pd
import json
import os

import sys
import os

if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
    if base_dir.endswith("MacOS"):
        base_dir = os.path.abspath(os.path.join(base_dir, "../../.."))
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

EXCEL_FILE = os.path.join(base_dir, "Entrega3.xlsx")
JSON_FILE = os.path.join(base_dir, "registros.json")

class DataManager:
    def __init__(self):
        self.load_excel_data()
        self.load_json_data()

    def load_excel_data(self):
        try:
            xl = pd.ExcelFile(EXCEL_FILE)
            self.df_indicadores_totales = xl.parse("Indicadores_totales")
            self.df_paquetes = xl.parse("paquetes_trabajo")
            self.df_kpi = xl.parse("KPI")
            self.df_indicadores_mes = xl.parse("Indicadores_pormes")
            self.df_calculos = xl.parse("calculos_totales")
        except Exception as e:
            print(f"Error loading Excel: {e}")
            self.df_indicadores_totales = pd.DataFrame()
            self.df_paquetes = pd.DataFrame()
            self.df_kpi = pd.DataFrame()
            self.df_indicadores_mes = pd.DataFrame()
            self.df_calculos = pd.DataFrame()

    def load_json_data(self):
        if not os.path.exists(JSON_FILE):
            self.registros = {
                "comentarios": [],
                "reprocesos": [],
                "aciertos_fallos": []
            }
            self.save_json_data()
        else:
            try:
                with open(JSON_FILE, "r", encoding="utf-8") as f:
                    self.registros = json.load(f)
            except Exception as e:
                print(f"Error loading JSON: {e}")
                self.registros = {
                    "comentarios": [],
                    "reprocesos": [],
                    "aciertos_fallos": []
                }

    def save_json_data(self):
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(self.registros, f, indent=4, ensure_ascii=False)

    def get_kpi_metrics(self):
        # Returns the latest KPIs from the KPI sheet
        if self.df_kpi.empty:
            return {}
        latest = self.df_kpi.iloc[-1]
        return {
            "VP": latest.get("VP", 0),
            "CR": latest.get("CR", 0),
            "VG": latest.get("VG", 0),
            "SPI": latest.get("SPI", 0),
            "CPI": latest.get("CPI", 0),
            "CV": latest.get("CV (VG-CR)", 0),
            "SV": latest.get("SV (VG-VP)", 0), 
        }

    def get_kpi_by_month(self, month_or_date):
        if self.df_kpi.empty:
            return {}
        # Filtrar por fecha
        df_filtered = self.df_kpi[self.df_kpi["Fecha"] == month_or_date]
        if df_filtered.empty:
            return self.get_kpi_metrics() 
        row = df_filtered.iloc[-1]
        return {
            "VP": row.get("VP", 0),
            "CR": row.get("CR", 0),
            "VG": row.get("VG", 0),
            "SPI": row.get("SPI", 0),
            "CPI": row.get("CPI", 0),
            "CV": row.get("CV (VG-CR)", 0)
        }

    def get_scurve_data(self):
        if self.df_kpi.empty:
            return [], [], [], []
        fechas = self.df_kpi["Fecha"].tolist()
        vp = self.df_kpi["VP"].tolist()
        cr = self.df_kpi["CR"].tolist()
        vg = self.df_kpi["VG"].tolist()
        return fechas, vp, cr, vg

    def get_wbs_data(self):
        if self.df_paquetes.empty:
            return []
        # Return dicts for the data table
        return self.df_paquetes.to_dict(orient="records")

    def add_registro(self, tipo, data):
        # tipo: "comentarios", "reprocesos", "aciertos_fallos"
        if tipo in self.registros:
            self.registros[tipo].append(data)
            self.save_json_data()

    def delete_registro(self, tipo, index):
        if tipo in self.registros and 0 <= index < len(self.registros[tipo]):
            self.registros[tipo].pop(index)
            self.save_json_data()
