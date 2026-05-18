# 🚀 Ficha Técnica y Arquitectura del Dashboard

## 1. ¿En qué está construido? (Tecnologías)
El **Executive Project Dashboard** ha sido desarrollado bajo un stack de desarrollo web ágil y moderno en Python, enfocado en el alto rendimiento visual de datos (*Data Science*):
*   **Streamlit (Framework Web):** Utilizado para renderizar la interfaz de usuario interactiva y responsiva de manera rápida y eficiente.
*   **Pandas (Procesamiento de Datos):** El motor matemático que estructura, limpia y procesa la información de costos, avances y plazos en tiempo real.
*   **Plotly (Gráficos Interactivos):** Motor gráfico para representar de forma dinámica la Curva S, el diagrama de Gantt y los flujos de caja, permitiendo interactividad completa (hacer zoom, aislar curvas y hacer clics en puntos específicos).
*   **Google Fonts & CSS Personalizado:** Tipografía premium ('Outfit') y estilos limpios con *glassmorphism* (diseño limpio y translúcido) para lograr un acabado visual corporativo y de alto nivel.

---

## 2. ¿Dónde está alojado? (Despliegue)
*   **Repositorio Central:** El código está alojado en **GitHub** en una rama estable (`main`), lo cual garantiza el control de versiones y el trabajo colaborativo.
*   **Alojamiento (Hosting):** Actualmente se ejecuta de manera local, pero gracias a la arquitectura ligera de Streamlit, se puede desplegar con un solo clic en **Streamlit Community Cloud** (u otras plataformas en la nube como AWS/Heroku), quedando accesible de manera pública o privada mediante un enlace web HTTPS seguro para cualquier parte interesada (*stakeholder*).

---

## 3. ¿Cómo se garantiza la integridad de los datos? (Seguridad y Lectura Limpia)
Uno de los pilares del diseño del dashboard es la **inmutabilidad de la información contractual**:
1.  **Desacoplamiento Base de Datos / Visualización:** El dashboard lee la información directamente de un archivo Excel de control de proyectos (`Entrega3.xlsx`). **La lectura es estrictamente de "Solo Lectura" (Read-Only)** a través de Pandas. Ningún usuario puede editar, alterar o corromper los indicadores del proyecto, contratos o históricos financieros desde la interfaz web.
2.  **Seguridad en el Registro de Cambios (Bitácora):** Para no alterar el archivo maestro de Excel con anotaciones dinámicas, la **Bitácora de Cambios** almacena las observaciones directamente en un archivo **JSON local independiente (`bitacora.json`)**. Esto garantiza que las notas de gerencia y explicaciones cualitativas queden registradas sin alterar la base dura de datos del proyecto, manteniendo el Excel intacto como fuente única de verdad auditada.

---

## 4. Estructura y Propósito de Cada Pestaña (De un Vistazo)

El menú de navegación lateral divide la gestión del proyecto en **6 áreas clave**:

*   **📊 Resumen Ejecutivo (EVM):** El panel de control principal. Utiliza la metodología de *Earned Value Management* (EVM) para cruzar el Valor Planificado (`VP`), Costo Real (`CR`) y Valor Ganado (`VG`) mediante una **Curva S interactiva** que inicia en 0. Permite al gerente conocer la eficiencia en tiempo (SPI) y costo (CPI) en cualquier mes del proyecto.
*   **📅 Cronograma (Gantt):** Un diagrama de barras horizontales interactivo que muestra las fechas reales de inicio y finalización de cada paquete de trabajo (EDT). Permite identificar las secuencias de ejecución y plazos reales de las actividades.
*   **💰 Flujo de Caja:** Compara mes a mes los desembolsos periódicos y acumulados programados contra los reales. Permite al administrador evaluar la tesorería del proyecto e identificar cuándo ocurrieron los mayores requerimientos de caja.
*   **📦 Control de Paquetes (Progreso EDT):** Vista visual de semáforo (rojo, amarillo, verde) que ordena las actividades de la EDT según su porcentaje de avance físico real (de 0% a 100%), permitiendo ver qué entregables están cerrados y cuáles requieren atención.
*   **📈 Indicadores Mensuales:** Vista detallada tipo tabla con todas las métricas y fórmulas del proyecto desglosadas mes a mes. Es la herramienta de auditoría de datos para el equipo de control de proyectos.
*   **📝 Bitácora:** El registro cualitativo del proyecto. Permite a los gerentes documentar eventos, incidentes, justificaciones de retraso o aprobaciones de cambios sobre la marcha, dotando de contexto narrativo a las cifras y gráficas de control.

---

## 5. Gestión de Portafolio Multi-Proyecto (Simulación Avanzada)
El dashboard se ha generalizado para soportar un **Portafolio de 5 Proyectos** dinámicos, seleccionables desde el menú lateral superior. Utilizando el archivo maestro de Excel (`Entrega3.xlsx`) como "Caso Base", el sistema simula con rigor matemático 4 escenarios reales adicionales:

1.  **Caso Base (Original):** El proyecto tal cual fue planificado y ejecutado en el archivo Excel maestro.
2.  **Proyecto Acelerado (Crash Project):** Simula una aceleración programada de actividades. El avance físico real (`AR`) e ingresos de valor (`VG`) se adelantan un 15%, logrando terminar antes del plazo con un leve incremento de costo del 10% (debido a sobretiempos).
3.  **Retraso en Procura (Supply Chain Delay):** Modela un escenario de crisis logística real. Las actividades críticas sufren una paralización y retraso de avance físico del 35% entre los meses 4 y 8 (representado en caídas agudas del SPI a ~0.65). Posteriormente, se acelera en el último trimestre con un sobrecosto del 25% (horas extras, fletes urgentes) para intentar recuperar terreno.
4.  **Sobrecosto por Cambios (Scope Creep):** Modela un crecimiento del alcance del proyecto (órdenes de cambio multiplicadas por 2.5x). Esto incrementa el presupuesto total planificado (`Cco`/`VP`) en un 15%, y dispara el Costo Real (`CR`) en un 35% debido a reprocesos, manteniendo eficiencias de costo muy bajas (CPI ~0.75).
5.  **Rendimiento Excepcional (Star Project):** Simula el escenario ideal de un proyecto con una gerencia sobresaliente. El avance físico se adelanta en un 8% mientras que se ahorra un 15% del costo real programado (operando bajo presupuesto con CPI y SPI > 1.05).

### Aislamiento de Bitácora por Proyecto:
Para garantizar la integridad y coherencia de los análisis históricos, **cada proyecto posee su propia base de datos JSON de Bitácora aislada** (`registros_caso_base.json`, `registros_proyecto_acelerado.json`, etc.). Esto permite registrar comentarios, reprocesos y lecciones aprendidas de forma independiente para cada escenario del portafolio.

