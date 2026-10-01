import streamlit as st
import pandas as pd
import plotly.express as px
import os
import numpy as np

# Configuración de la página
st.set_page_config(layout="wide", page_title="Análisis de Colectores")

# Funciones de cálculo
def calculate_metrics(df, col):
    metrics = {
        'Valor Medio': df[col].mean(),
        'Máximo': df[col].max(),
        'Mínimo': df[col].min(),
        'Integral': np.trapezoid(df[col], df['theta']),
        'Desv. Estándar': df[col].std(),
    }
    # Uniformidad Absoluta: media de abs / max de abs
    abs_col = np.abs(df[col])
    metrics['Uniformidad Absoluta'] = abs_col.mean() / abs_col.max() if abs_col.max() != 0 else 0
    
    # Coeficiente de Variación de Uniformidad: 1 - sigma / abs(media)
    mean_val = df[col].mean()
    abs_mean = np.abs(mean_val)
    metrics['Coef. Variación'] = 1 - (df[col].std() / abs_mean) if abs_mean != 0 else 0
    
    return metrics

def display_formulas():
    with st.expander("ℹ️ Ver fórmulas utilizadas"):
        st.latex(r'''
            \begin{aligned}
            &\text{Valor Medio: } \bar{x} = \frac{1}{n} \sum_{i=1}^{n} x_i \\
            &\text{Máximo: } \max(x) \\
            &\text{Mínimo: } \min(x) \\
            &\text{Integral: } \int x \, d\theta \approx \sum_{i=1}^{n-1} \frac{x_i + x_{i+1}}{2} \Delta\theta_i \\
            &\text{Desv. Estándar: } \sigma = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (x_i - \bar{x})^2} \\
            &\text{Uniformidad Absoluta: } \frac{\bar{|x|}}{\max(|x|)} \\
            &\text{Coef. Variación: } 1 - \frac{\sigma}{|\bar{x}|}
            \end{aligned}
        ''')

def create_compact_label(row):
    # Format: A<aceptación>_G<gap>_C<caudal>_I<incidente>
    acept = int(row['ang aceptación'])
    gap = int(row['gap tubo [m]'] * 1000)
    caudal = str(row['velocidad caudal [m/s]']).replace('.', '')
    inc = int(row['ang rad incidente'])
    return f"A{acept}_G{gap}_C{caudal}_I{inc}"

# Carga de datos
@st.cache_data
def load_data():
    # Cargar tabla de parámetros
    df_params = pd.read_excel('Casos a correr.xlsx', sheet_name='Hoja 1')
    # Limpiar columnas innecesarias
    df_params = df_params.drop(columns=[col for col in df_params.columns if 'Unnamed' in col])
    
    # Mapear nombres de archivo esperados
    df_params['filename'] = df_params['Nombre caso'].str.replace(' ', '_') + '.csv'
    
    # Crear etiqueta compacta
    df_params['label'] = df_params.apply(create_compact_label, axis=1)
    
    return df_params

def load_case_data(filename):
    path = os.path.join('resultados_csv', filename)
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

@st.cache_data
def get_all_metrics_df(df_params):
    all_metrics = []
    for _, row in df_params.iterrows():
        df_case = load_case_data(row['filename'])
        if df_case is not None:
            case_metrics = {'Label': row['label'], 'Caudal': row['velocidad caudal [m/s]'], 'Incidente': row['ang rad incidente'], 'Aceptación': row['ang aceptación'], 'Gap': int(row['gap tubo [m]'] * 1000)}
            
            # Métricas estándar
            for col in ['wallHeatFlux', 'qr', 'T']:
                m = calculate_metrics(df_case, col)
                for k, v in m.items():
                    case_metrics[f"{col}_{k}"] = v
            
            # Métricas para wallHeatFlux en valor absoluto
            df_case_abs = df_case.assign(wallHeatFlux=np.abs(df_case['wallHeatFlux']))
            m_abs = calculate_metrics(df_case_abs, 'wallHeatFlux')
            for k, v in m_abs.items():
                case_metrics[f"abs_wallHeatFlux_{k}"] = v
                
            all_metrics.append(case_metrics)
    return pd.DataFrame(all_metrics)

# --- UI ---
st.title("📊 Análisis de Resultados de Colectores")

df_params = load_data()
df_all_metrics = get_all_metrics_df(df_params)

# Sidebar: Filtros de entrada
st.sidebar.header("Filtros de Parámetros")
mode = st.sidebar.radio("Modo de visualización", ["Individual", "Comparativo", "Análisis Avanzado"])

velocidad = st.sidebar.multiselect("Velocidad Caudal [m/s]", sorted(df_params['velocidad caudal [m/s]'].unique()))
ang_incidente = st.sidebar.multiselect("Ángulo Incidente [°]", sorted(df_params['ang rad incidente'].unique()))
ang_aceptacion = st.sidebar.multiselect("Ángulo Aceptación [°]", sorted(df_params['ang aceptación'].unique()))

# Gap: convertir a mm para el filtro
gap_options_m = sorted(df_params['gap tubo [m]'].unique())
gap_options_mm = [int(g * 1000) for g in gap_options_m]
selected_gaps_mm = st.sidebar.multiselect("Gap Tubo [mm]", gap_options_mm)

# Aplicar filtros
mask = pd.Series(True, index=df_params.index)
if velocidad: mask &= df_params['velocidad caudal [m/s]'].isin(velocidad)
if ang_incidente: mask &= df_params['ang rad incidente'].isin(ang_incidente)
if ang_aceptacion: mask &= df_params['ang aceptación'].isin(ang_aceptacion)
if selected_gaps_mm:
    selected_gaps_m = [g / 1000 for g in selected_gaps_mm]
    mask &= df_params['gap tubo [m]'].isin(selected_gaps_m)

df_filtered = df_params[mask]

if df_filtered.empty:
    st.warning("No hay casos que coincidan con los filtros seleccionados.")
else:
    st.write(f"Casos encontrados: {len(df_filtered)}")
    
    if mode == "Individual":
        # Selección de caso específico
        selected_label = st.selectbox("Seleccionar Caso para detalle:", df_filtered['label'].tolist())
        
        case_info = df_filtered[df_filtered['label'] == selected_label].iloc[0]
        filename = case_info['filename']
        
        df_case = load_case_data(filename)
        
        if df_case is not None:
            tab1, tab2 = st.tabs(["Visualización", "Análisis Cuantitativo"])
            
            with tab1:
                st.subheader(f"Resultados: {selected_label}")
                st.write(f"**Referencia:** {case_info['Nombre caso']}")
                st.write(f"**Parámetros:** Caudal: {case_info['velocidad caudal [m/s]']} m/s, Incidente: {case_info['ang rad incidente']}°, Aceptación: {case_info['ang aceptación']}°, Gap: {int(case_info['gap tubo [m]'] * 1000)} mm")
                
                # Gráficos
                cols = ['wallHeatFlux', 'qr', 'T']
                for col in cols:
                    fig = px.line(df_case, x='theta', y=col, labels={'theta': 'Gamma [°]'}, title=f"Distribución de {col}")
                    st.plotly_chart(fig, width="stretch")
            
            with tab2:
                st.subheader(f"Métricas Cuantitativas: {selected_label}")
                display_formulas()
                metrics_data = []
                for col in ['wallHeatFlux', 'qr', 'T']:
                    metrics = calculate_metrics(df_case, col)
                    metrics['Variable'] = col
                    metrics_data.append(metrics)
                
                st.table(pd.DataFrame(metrics_data).set_index('Variable'))

        else:
            st.error(f"No se encontró el archivo de datos para {case_info['Nombre caso']}")

    elif mode == "Comparativo": # Modo Comparativo
        # Selección de casos a comparar
        selected_labels = st.multiselect("Seleccionar Casos a comparar:", df_filtered['label'].tolist(), default=df_filtered['label'].tolist()[:min(5, len(df_filtered))])
        
        if not selected_labels:
            st.info("Selecciona al menos un caso para comparar.")
        else:
            all_data = []
            for label in selected_labels:
                case_info = df_filtered[df_filtered['label'] == label].iloc[0]
                df_case = load_case_data(case_info['filename'])
                if df_case is not None:
                    df_case = df_case.sort_values(by='theta')
                    df_case['Caso'] = label # Añadir etiqueta compacta
                    all_data.append(df_case)
            
            if all_data:
                combined_df = pd.concat(all_data)
                
                tab1, tab2 = st.tabs(["Visualización", "Análisis Cuantitativo"])
                
                with tab1:
                    st.subheader("Comparativa de Resultados")
                    # Gráficos
                    cols = ['wallHeatFlux', 'qr', 'T']
                    for col in cols:
                        fig = px.line(combined_df, x='theta', y=col, labels={'theta': 'Gamma [°]'}, color='Caso', title=f"Comparativa de {col}")
                        st.plotly_chart(fig, width="stretch")
                
                with tab2:
                    st.subheader("Tabla Comparativa de Métricas")
                    display_formulas()
                    summary_data = []
                    for label in selected_labels:
                        case_info = df_filtered[df_filtered['label'] == label].iloc[0]
                        df_case = load_case_data(case_info['filename'])
                        if df_case is not None:
                            for col in ['wallHeatFlux', 'qr', 'T']:
                                metrics = calculate_metrics(df_case, col)
                                metrics['Caso'] = label
                                metrics['Variable'] = col
                                summary_data.append(metrics)
                    
                    df_summary = pd.DataFrame(summary_data)
                    st.dataframe(df_summary)
    
    else: # Análisis Avanzado
        st.subheader("Análisis Avanzado")
        
        # Mapa de calor
        st.subheader("Mapa de Calor de Métricas")
        c1, c2, c3, c4 = st.columns(4)
        
        # Mapeo de nombres para mostrar en el dropdown
        metric_map = {c: c.replace('abs_', 'Absoluto: ').replace('_', ' ') for c in df_all_metrics.columns if c not in ['Label', 'Caudal', 'Incidente', 'Aceptación', 'Gap']}
        
        selected_metric_display = c1.selectbox("Métrica a plotear:", list(metric_map.values()))
        # Invertir el mapeo para obtener la columna real
        metric_to_plot = [k for k, v in metric_map.items() if v == selected_metric_display][0]
        
        histfunc = c2.selectbox("Función de agregación:", ['avg', 'sum', 'max', 'min', 'count'])
        x_axis = c3.selectbox("Eje X:", ['Caudal', 'Incidente', 'Aceptación', 'Gap'])
        y_axis = c4.selectbox("Eje Y:", ['Incidente', 'Aceptación', 'Gap', 'Caudal'], index=1)
        
        st.info("Nota: Las métricas prefijadas con 'Absoluto:' utilizan el valor positivo para facilitar la visualización de la intensidad.")
        
        fig_heat = px.density_heatmap(df_all_metrics, x=x_axis, y=y_axis, z=metric_to_plot, 
                                      histfunc=histfunc, title=f"Mapa de Calor: {selected_metric_display} (Agregación: {histfunc})")
        st.plotly_chart(fig_heat, width="stretch")
