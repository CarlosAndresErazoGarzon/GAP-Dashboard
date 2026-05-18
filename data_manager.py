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
        # Returns the latest KPIs dynamically calculated using Cco as VP
        if self.df_kpi.empty or self.df_calculos.empty:
            return {}
        latest_kpi = self.df_kpi.iloc[-1]
        latest_calc = self.df_calculos.iloc[-1]
        
        vp_val = float(latest_calc.get("Cco", 0))
        cr_val = float(latest_kpi.get("CR", 0))
        vg_val = float(latest_kpi.get("VG", 0))
        
        sv_val = vg_val - vp_val
        spi_val = (vg_val / vp_val) if vp_val > 0 else 1.0
        cv_val = vg_val - cr_val
        cpi_val = (vg_val / cr_val) if cr_val > 0 else 1.0
        
        return {
            "VP": vp_val,
            "CR": cr_val,
            "VG": vg_val,
            "SPI": spi_val,
            "CPI": cpi_val,
            "CV": cv_val,
            "SV": sv_val,
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
        if month_or_date == "Inicio":
            return {
                "VP": 0.0,
                "CR": 0.0,
                "VG": 0.0,
                "SPI": 1.0,
                "CPI": 1.0,
                "CV": 0.0,
                "SV": 0.0
            }
            
        if self.df_kpi.empty or self.df_calculos.empty:
            return {}
        
        target = self.normalize_date(month_or_date)
        
        # Filtrar por fecha normalizada
        mask_kpi = self.df_kpi["Fecha"].apply(self.normalize_date) == target
        df_kpi_filt = self.df_kpi[mask_kpi]
        
        mask_calc = self.df_calculos["Fecha"].apply(self.normalize_date) == target
        df_calc_filt = self.df_calculos[mask_calc]
        
        if df_kpi_filt.empty:
            # Si no hay coincidencia exacta, intentamos buscar si el KPI tiene la fecha en el formato original
            df_kpi_filt = self.df_kpi[self.df_kpi["Fecha"].astype(str) == str(month_or_date)]
            df_calc_filt = self.df_calculos[self.df_calculos["Fecha"].astype(str) == str(month_or_date)]
            
        if df_kpi_filt.empty:
            return self.get_kpi_metrics() 
            
        row_kpi = df_kpi_filt.iloc[-1]
        
        # Obtener Cco como el VP acumulado real
        vp_val = 0.0
        if not df_calc_filt.empty:
            vp_val = float(df_calc_filt.iloc[-1].get("Cco", 0))
        else:
            vp_val = float(row_kpi.get("VP", 0))
            
        cr_val = float(row_kpi.get("CR", 0))
        vg_val = float(row_kpi.get("VG", 0))
        
        # Calcular de forma dinámica
        sv_val = vg_val - vp_val
        spi_val = (vg_val / vp_val) if vp_val > 0 else 1.0
        cv_val = vg_val - cr_val
        cpi_val = (vg_val / cr_val) if cr_val > 0 else 1.0
        
        return {
            "VP": vp_val,
            "CR": cr_val,
            "VG": vg_val,
            "SPI": spi_val,
            "CPI": cpi_val,
            "CV": cv_val,
            "SV": sv_val
        }

    def get_scurve_data(self):
        if self.df_kpi.empty or self.df_calculos.empty:
            return [], [], [], []
        
        fechas = self.df_kpi["Fecha"].tolist()
        vp = pd.to_numeric(self.df_calculos["Cco"], errors="coerce").fillna(0).tolist()
        cr = pd.to_numeric(self.df_kpi["CR"], errors="coerce").fillna(0).tolist()
        vg = pd.to_numeric(self.df_kpi["VG"], errors="coerce").fillna(0).tolist()
        
        # Prepend 'Inicio' to start at 0.0
        fechas_res = ["Inicio"] + fechas
        vp_res = [0.0] + vp
        cr_res = [0.0] + cr
        vg_res = [0.0] + vg
        
        return fechas_res, vp_res, cr_res, vg_res

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
