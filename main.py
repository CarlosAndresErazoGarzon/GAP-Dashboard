import streamlit as st
import sys
import os

# Lanzador automático
if not st.runtime.exists():
    import subprocess
    subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])
    sys.exit()

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from data_manager import DataManager

st.set_page_config(
    page_title="Executive Project Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&display=swap');
    
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Outfit', sans-serif;
    }
    
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 20px;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    
    .metric-label {
        color: #555555;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        color: #111111;
        font-size: 2.2rem;
        font-weight: 700;
        margin-top: 8px;
    }
    
    .stApp {
        background-color: #f4f6f8;
        color: #333333;
    }
    
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }
    
    h1, h2, h3 {
        color: #111111 !important;
    }
    
    /* Custom highlight for top comments */
    .top-comment {
        background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
        border-left: 4px solid #f1c40f;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_data_manager():
    dm = DataManager()
    migrated = False
    for tipo in ["comentarios", "reprocesos", "aciertos_fallos"]:
        for i in range(len(dm.registros[tipo])):
            if isinstance(dm.registros[tipo][i], str):
                dm.registros[tipo][i] = {"text": dm.registros[tipo][i], "score": 0}
                migrated = True
    if migrated:
        dm.save_json_data()
    return dm

dm = get_data_manager()

# Navegación
st.sidebar.markdown("<h2 style='text-align: center;'>PORTAFOLIO</h2><hr>", unsafe_allow_html=True)
opciones = ["RESUMEN EJECUTIVO", "CRONOGRAMA (GANTT)", "FLUJO DE CAJA", "CONTROL DE PAQUETES", "INDICADORES MENSUALES", "BITÁCORA"]
seleccion = st.sidebar.radio("Navegación", opciones, label_visibility="collapsed")

if seleccion == "RESUMEN EJECUTIVO":
    st.markdown("<h1>Estado General del Proyecto</h1>", unsafe_allow_html=True)
    
    kpis = dm.get_kpi_metrics()
    
    # KPIs
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"<div class='metric-card'><div class='metric-label'>SPI (Eficiencia Cronograma)</div><div class='metric-value'>{round(kpis.get('SPI', 0), 3)}</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-card'><div class='metric-label'>CPI (Eficiencia Costo)</div><div class='metric-value'>{round(kpis.get('CPI', 0), 3)}</div></div>", unsafe_allow_html=True)
    with c3:
        cv = kpis.get('CV', 0)
        cv_color = "#27ae60" if cv >= 0 else "#e74c3c"
        st.markdown(f"<div class='metric-card'><div class='metric-label'>CV (Variación de Costo)</div><div class='metric-value' style='color: {cv_color}'>${cv:,.0f}</div></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    colA, colB = st.columns([0.65, 0.35])
    
    with colA:
        st.markdown("### Análisis de Valor Ganado (Curva S)")
        try:
            fechas, vp, cr, vg = dm.get_scurve_data()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=fechas, y=vp, name='VP (Planificado)', line=dict(color='#2980b9', width=3)))
            fig.add_trace(go.Scatter(x=fechas, y=cr, name='CR (Real)', line=dict(color='#e74c3c', width=3)))
            fig.add_trace(go.Scatter(x=fechas, y=vg, name='VG (Ganado)', line=dict(color='#27ae60', width=3, dash='dash')))
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=10, b=0), height=400, hovermode="x unified",
                xaxis=dict(showgrid=True, gridcolor='#e0e0e0', color="#333"),
                yaxis=dict(showgrid=True, gridcolor='#e0e0e0', tickformat="$,.0f", color="#333"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.error(f"Error generando Curva S: {e}")
            
    with colB:
        st.markdown("### Puntos Críticos (Puntuación ≥ 5)")
        
        destacados = []
        for tipo in ["comentarios", "reprocesos", "aciertos_fallos"]:
            for item in dm.registros[tipo]:
                if item.get("score", 0) >= 5:
                    tipo_str = "Comentario" if tipo == "comentarios" else "Reproceso" if tipo == "reprocesos" else "Lección"
                    destacados.append((tipo_str, item))
                    
        destacados = sorted(destacados, key=lambda x: x[1]["score"], reverse=True)
        
        if destacados:
            for tipo_str, item in destacados:
                st.markdown(f"""
                <div class='top-comment'>
                    <div style='font-size: 0.75rem; color: #7f8c8d; text-transform: uppercase; font-weight: bold;'>{tipo_str}</div>
                    <strong>{item['score']} ⭐</strong> - {item['text']}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No hay registros con puntuación ≥ 5 en la Bitácora.")

elif seleccion == "CRONOGRAMA (GANTT)":
    st.markdown("<h1>Cronograma de Actividades (Gantt)</h1>", unsafe_allow_html=True)
    gantt_data = dm.get_gantt_data()
    
    if gantt_data:
        df_gantt = pd.DataFrame(gantt_data)
        
        # Convertir fechas MM-DD a datetime para que Plotly las ordene bien
        # Asumimos año 2024 para visualización
        def fix_date(d):
            if len(d) == 5: # MM-DD
                return f"2024-{d}"
            return d
            
        df_gantt['Start'] = df_gantt['Start'].apply(fix_date)
        df_gantt['Finish'] = df_gantt['Finish'].apply(fix_date)
        
        # Asegurar que Finish sea estrictamente después de Start para visualización si son iguales
        # (ej. si una tarea empieza y termina el mismo mes)
        # df_gantt['Finish'] = pd.to_datetime(df_gantt['Finish']) + pd.DateOffset(days=28)
        
        import plotly.express as px
        fig_gantt = px.timeline(
            df_gantt, 
            x_start="Start", 
            x_end="Finish", 
            y="Task",
            color="Completion",
            color_continuous_scale='RdYlGn',
            labels={"Task": "Actividad", "Completion": "Avance %"},
            hover_data=["Completion"]
        )
        
        fig_gantt.update_yaxes(autorange="reversed") # Tareas de arriba hacia abajo
        fig_gantt.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title="Línea de Tiempo",
            height=500,
            xaxis=dict(
                showgrid=True,
                gridcolor='#e0e0e0',
                tickformat="%b", # Mostrar nombre del mes
                dtick="M1" # Intervalo de un mes
            )
        )
        
        st.plotly_chart(fig_gantt, use_container_width=True)
        
        # Tabla resumen
        with st.expander("Ver detalle de fechas"):
            st.table(df_gantt)
    else:
        st.warning("No hay datos disponibles para generar el cronograma.")

elif seleccion == "FLUJO DE CAJA":
    st.markdown("<h1>Análisis de Flujo de Caja Mensual</h1>", unsafe_allow_html=True)
    try:
        df_calc = dm.df_calculos
        if not df_calc.empty:
            # Calcular flujo de caja periódico (diferencias)
            df_calc['Flujo_CR'] = pd.to_numeric(df_calc['CR'], errors='coerce').fillna(0).diff().fillna(pd.to_numeric(df_calc['CR'], errors='coerce').fillna(0).iloc[0])
            df_calc['Flujo_VP'] = pd.to_numeric(df_calc['VPi'], errors='coerce').fillna(0).diff().fillna(pd.to_numeric(df_calc['VPi'], errors='coerce').fillna(0).iloc[0])
            
            # Acumulados
            df_calc['CR_Acum'] = pd.to_numeric(df_calc['CR'], errors='coerce').fillna(0)
            df_calc['VP_Acum'] = pd.to_numeric(df_calc['VPi'], errors='coerce').fillna(0)
            
            fechas = df_calc['Fecha'].tolist()
            
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=fechas, y=df_calc['Flujo_VP'], name='Desembolso Planificado', marker_color='#bdc3c7'))
            fig2.add_trace(go.Bar(x=fechas, y=df_calc['Flujo_CR'], name='Desembolso Real', marker_color='#e67e22'))
            
            fig2.update_layout(
                barmode='group',
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                height=450, hovermode="x unified",
                xaxis=dict(showgrid=True, gridcolor='#e0e0e0', color="#333"),
                yaxis=dict(showgrid=True, gridcolor='#e0e0e0', tickformat="$,.0f", color="#333", title="Monto Desembolsado ($)"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig2, width='stretch')
    except Exception as e:
        st.error(f"Error procesando flujo de caja: {e}")

elif seleccion == "CONTROL DE PAQUETES":
    st.markdown("<h1>Estado de Actividades (EDT)</h1>", unsafe_allow_html=True)
    wbs = dm.get_wbs_data()
    
    if wbs:
        df_wbs = pd.DataFrame(wbs)
        for col in ['AR', 'VPi', 'CR']:
            if col in df_wbs.columns:
                df_wbs[col] = pd.to_numeric(df_wbs[col], errors='coerce').fillna(0)
                
        df_wbs = df_wbs.sort_values(by='AR', ascending=True)
        
        fig3 = px.bar(
            df_wbs, x='AR', y='Actividad', orientation='h',
            text='AR', color='AR',
            color_continuous_scale=['#e74c3c', '#f1c40f', '#27ae60'],
            range_color=[0, 100], labels={'AR': 'Avance (%)'}
        )
        
        fig3.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig3.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=max(400, len(df_wbs)*40),
            xaxis=dict(range=[0, 115], showgrid=True, gridcolor='#e0e0e0', color="#333"),
            yaxis=dict(color="#333"), coloraxis_showscale=False
        )
        st.plotly_chart(fig3, width='stretch')

elif seleccion == "INDICADORES MENSUALES":
    st.markdown("<h1>Detalle de Cierre Mensual</h1>", unsafe_allow_html=True)
    
    df_mes = dm.df_indicadores_mes
    if not df_mes.empty:
        mes_sel = st.selectbox("Seleccione el Periodo de Evaluación:", df_mes["Mes"].tolist())
        datos_mes = df_mes[df_mes["Mes"] == mes_sel].iloc[0]
        
        st.markdown("---")
        
        fig_gauges = go.Figure()
        
        fig_gauges.add_trace(go.Indicator(
            mode="gauge+number",
            value=float(datos_mes.get('Ia', 0)),
            title={'text': "Índice de Avance (Ia)"},
            domain={'x': [0, 0.45], 'y': [0, 1]},
            gauge={'axis': {'range': [0, 1.5]}, 'bar': {'color': "#2980b9"}}
        ))
        
        fig_gauges.add_trace(go.Indicator(
            mode="gauge+number",
            value=float(datos_mes.get('IδT', 0)),
            title={'text': "Índice Desviación Tiempo (IδT)"},
            domain={'x': [0.55, 1], 'y': [0, 1]},
            gauge={'axis': {'range': [0, 1.5]}, 'bar': {'color': "#27ae60"}}
        ))
        
        fig_gauges.update_layout(height=300, margin=dict(t=50, b=0), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_gauges, width='stretch')
        
        # Tarjetas de desviaciones
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"<div class='metric-card'><div class='metric-label'>Desviación Tiempo (δT)</div><div class='metric-value'>{datos_mes.get('δT')}</div></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-card'><div class='metric-label'>Desviación Costo (δC)</div><div class='metric-value'>{datos_mes.get('δC')}</div></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='metric-card'><div class='metric-label'>Variación Estimada (VEP)</div><div class='metric-value'>{datos_mes.get('VEP')}</div></div>", unsafe_allow_html=True)

elif seleccion == "BITÁCORA":
    st.markdown("<h1>Gestión de Conocimiento y Bitácora</h1>", unsafe_allow_html=True)
    
    t1, t2, t3 = st.tabs(["COMENTARIOS", "REPROCESOS", "LECCIONES APRENDIDAS"])
    
    def render_exec_list(tipo):
        items = dm.registros[tipo]
        
        # Ordenar por puntaje
        items_sorted = sorted(enumerate(items), key=lambda x: x[1]['score'], reverse=True)
        
        for idx, item in items_sorted:
            c1, c2, c3 = st.columns([0.1, 0.8, 0.1])
            with c1:
                if st.button(f"⭐ {item['score']}", key=f"up_{tipo}_{idx}", help="Puntuar"):
                    dm.registros[tipo][idx]['score'] += 1
                    dm.save_json_data()
                    st.rerun()
            with c2:
                st.markdown(f"<div style='background: #ffffff; padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px;'>{item['text']}</div>", unsafe_allow_html=True)
            with c3:
                if st.button("🗑️", key=f"del_{tipo}_{idx}"):
                    dm.delete_registro(tipo, idx)
                    st.rerun()
                
        st.markdown("---")
        nuevo = st.text_area(f"Registrar nueva entrada:", key=f"in_{tipo}")
        if st.button("Guardar Registro", key=f"btn_{tipo}", type="primary"):
            if nuevo.strip():
                dm.add_registro(tipo, {"text": nuevo.strip(), "score": 0})
                st.rerun()

    with t1: render_exec_list("comentarios")
    with t2: render_exec_list("reprocesos")
    with t3: render_exec_list("aciertos_fallos")
