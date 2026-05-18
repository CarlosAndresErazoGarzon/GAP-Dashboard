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
    VERSION = "1.3"
    def __init__(self):
        self.project_name = "Caso Base (Original)"
        self.using_simulation = False
        self.load_excel_data()
        self.load_json_data()

    def get_project_id(self):
        return self.project_name.lower().replace(" (original)", "").replace(" ", "_")

    def set_project(self, project_name):
        self.project_name = project_name
        
        # Check if a custom project-specific Excel file exists
        project_id = self.get_project_id()
        project_excel_filename = f"Entrega3_{project_id}.xlsx"
        project_excel_path = os.path.join(base_dir, project_excel_filename)
        
        if os.path.exists(project_excel_path):
            # 1. Load real data from custom project Excel database
            self.load_excel_data(project_excel_path)
            self.using_simulation = False
        else:
            # 2. Fall back to base Excel database and apply high-fidelity programmatic simulation
            self.load_excel_data(EXCEL_FILE)
            self.using_simulation = True
            
            # Apply mathematical transformations to generate realistic project scenarios
            if project_name == "Caso Base (Original)":
                pass
            elif project_name == "Proyecto Acelerado":
                self._apply_scaling(factor_vg=1.15, factor_cr=1.10, factor_vp=1.0)
            elif project_name == "Retraso en Procura":
                self._apply_delay_scaling()
            elif project_name == "Sobrecosto por Cambios":
                self._apply_scaling(factor_vg=0.90, factor_cr=1.35, factor_vp=1.15)
            elif project_name == "Rendimiento Excepcional":
                self._apply_scaling(factor_vg=1.08, factor_cr=0.85, factor_vp=1.0)
            
        self.load_json_data() # Load project-specific JSON logs

    def _apply_scaling(self, factor_vg, factor_cr, factor_vp):
        # Scale df_kpi
        for col, factor in [("VG", factor_vg), ("CR", factor_cr), ("VP", factor_vp)]:
            if col in self.df_kpi.columns:
                self.df_kpi[col] = pd.to_numeric(self.df_kpi[col], errors='coerce').fillna(0) * factor
        if "AR (%)" in self.df_kpi.columns:
            self.df_kpi["AR (%)"] = (pd.to_numeric(self.df_kpi["AR (%)"], errors='coerce').fillna(0) * factor_vg).clip(0, 100)
            
        # Scale df_calculos
        for col, factor in [("VG", factor_vg), ("CR", factor_cr), ("Cco", factor_vp)]:
            if col in self.df_calculos.columns:
                self.df_calculos[col] = pd.to_numeric(self.df_calculos[col], errors='coerce').fillna(0) * factor
        if "AR" in self.df_calculos.columns:
            self.df_calculos["AR"] = (pd.to_numeric(self.df_calculos["AR"], errors='coerce').fillna(0) * factor_vg).clip(0, 100)

        # Scale df_indicadores_totales
        for col, factor in [("VG", factor_vg), ("CR", factor_cr), ("Cco", factor_vp)]:
            if col in self.df_indicadores_totales.columns:
                self.df_indicadores_totales[col] = pd.to_numeric(self.df_indicadores_totales[col], errors='coerce').fillna(0) * factor
        if "AR" in self.df_indicadores_totales.columns:
            self.df_indicadores_totales["AR"] = (pd.to_numeric(self.df_indicadores_totales["AR"], errors='coerce').fillna(0) * factor_vg).clip(0, 100)

        # Scale df_paquetes
        if not self.df_paquetes.empty:
            if "AR" in self.df_paquetes.columns:
                self.df_paquetes["AR"] = (pd.to_numeric(self.df_paquetes["AR"], errors='coerce').fillna(0) * factor_vg).clip(0, 100)
            if "CR" in self.df_paquetes.columns:
                self.df_paquetes["CR"] = pd.to_numeric(self.df_paquetes["CR"], errors='coerce').fillna(0) * factor_cr

    def _apply_delay_scaling(self):
        # Simulates a severe delay in procurement (months 4-8) with subsequent cost catch-up (months 9-12)
        delay_dates = ["01-04", "01-05", "01-06", "01-07", "01-08"]
        rush_dates = ["01-09", "01-10", "01-11", "01-12"]
        
        def get_vg_factor(date_val):
            d_str = str(date_val).strip()
            if any(x in d_str for x in delay_dates):
                return 0.65
            elif any(x in d_str for x in rush_dates):
                return 0.90
            return 1.0
            
        def get_cr_factor(date_val):
            d_str = str(date_val).strip()
            if any(x in d_str for x in rush_dates):
                return 1.25
            return 1.0
            
        for df in [self.df_kpi, self.df_calculos, self.df_indicadores_totales]:
            if df.empty or "Fecha" not in df.columns:
                continue
            vg_factors = df["Fecha"].apply(get_vg_factor)
            cr_factors = df["Fecha"].apply(get_cr_factor)
            
            for col in ["VG", "AR (%)", "AR"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0) * vg_factors
                    if "AR" in col:
                        df[col] = df[col].clip(0, 100)
            if "CR" in df.columns:
                df["CR"] = pd.to_numeric(df["CR"], errors='coerce').fillna(0) * cr_factors

        # Scale df_paquetes
        if not self.df_paquetes.empty:
            if "AR" in self.df_paquetes.columns:
                self.df_paquetes["AR"] = (pd.to_numeric(self.df_paquetes["AR"], errors='coerce').fillna(0) * 0.90).clip(0, 100)
            if "CR" in self.df_paquetes.columns:
                self.df_paquetes["CR"] = pd.to_numeric(self.df_paquetes["CR"], errors='coerce').fillna(0) * 1.25

    def load_excel_data(self, excel_path=None):
        if excel_path is None:
            excel_path = EXCEL_FILE
        try:
            xl = pd.ExcelFile(excel_path)
            self.df_indicadores_totales = xl.parse("Indicadores_totales")
            self.df_paquetes = xl.parse("paquetes_trabajo")
            self.df_kpi = xl.parse("KPI")
            self.df_indicadores_mes = xl.parse("Indicadores_pormes")
            self.df_calculos = xl.parse("calculos_totales")
        except Exception as e:
            print(f"Error loading Excel ({excel_path}): {e}")
            self.df_indicadores_totales = pd.DataFrame()
            self.df_paquetes = pd.DataFrame()
            self.df_kpi = pd.DataFrame()
            self.df_indicadores_mes = pd.DataFrame()
            self.df_calculos = pd.DataFrame()

    def load_json_data(self):
        json_filename = f"registros_{self.get_project_id()}.json"
        self.json_file_path = os.path.join(base_dir, json_filename)
        if not os.path.exists(self.json_file_path):
            self.registros = {
                "comentarios": [],
                "reprocesos": [],
                "aciertos_fallos": []
            }
            self.save_json_data()
        else:
            try:
                with open(self.json_file_path, "r", encoding="utf-8") as f:
                    self.registros = json.load(f)
            except Exception as e:
                print(f"Error loading JSON: {e}")
                self.registros = {
                    "comentarios": [],
                    "reprocesos": [],
                    "aciertos_fallos": []
                }

    def save_json_data(self):
        if hasattr(self, 'json_file_path') and self.json_file_path:
            try:
                with open(self.json_file_path, "w", encoding="utf-8") as f:
                    json.dump(self.registros, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"Error saving JSON: {e}")

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
