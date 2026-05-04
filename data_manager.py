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
    VERSION = "1.1"
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

    def normalize_date(self, d):
        if pd.isna(d):
            return None
        d_str = str(d).strip()
        try:
            # Try YY-MM format (e.g., 01-10)
            if len(d_str) == 5 and d_str[2] == '-':
                return pd.to_datetime(d_str, format="%y-%m").strftime("%Y-%m-%d")
            # Try standard formats
            return pd.to_datetime(d_str).strftime("%Y-%m-%d")
        except:
            return d_str

    def get_kpi_by_month(self, month_or_date):
        if self.df_kpi.empty:
            return {}
        
        target = self.normalize_date(month_or_date)
        
        # Filtrar por fecha normalizada
        mask = self.df_kpi["Fecha"].apply(self.normalize_date) == target
        df_filtered = self.df_kpi[mask]
        
        if df_filtered.empty:
            # Si no hay coincidencia exacta, intentamos buscar si el KPI tiene la fecha en el formato original
            df_filtered = self.df_kpi[self.df_kpi["Fecha"].astype(str) == str(month_or_date)]
            
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

    def get_gantt_data(self):
        if self.df_indicadores_totales.empty:
            return []
        
        results = []
        activities = [a for a in self.df_indicadores_totales['Actividad'].unique() if a != 'TOTAL']
        
        for act in activities:
            sub = self.df_indicadores_totales[self.df_indicadores_totales['Actividad'] == act].copy()
            # Asegurar que Fecha sea string para comparaciones si es necesario, o manejarla como objeto
            sub['Fecha_str'] = sub['Fecha'].astype(str)
            sub = sub.sort_values('Fecha_str')
            
            # Start: First month with AR > 0
            start_row = sub[sub['AR'] > 0]
            if not start_row.empty:
                start = start_row['Fecha_str'].iloc[0]
            else:
                start = sub['Fecha_str'].iloc[0]
                
            # End: First month with AR >= 100
            end_row = sub[sub['AR'] >= 100]
            if not end_row.empty:
                end = end_row['Fecha_str'].iloc[0]
            else:
                end = sub['Fecha_str'].iloc[-1]
            
            results.append({
                'Task': act,
                'Start': start,
                'Finish': end,
                'Completion': sub['AR'].iloc[-1]
            })
            
        return results
