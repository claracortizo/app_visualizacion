# App de visualización resultados

Aplicación en python para visualizar los resultados de las simulaciones de la región externa del CPC.

## Despliegue en Streamlit Community Cloud

1. El repositorio canónico está en GitLab (`clara.cortizo/app_visualizacion`) y se sincroniza
   automáticamente a GitHub mediante un **push mirror** (GitLab → Settings → Repository →
   Mirroring repositories). Commitea y hace push solo a GitLab:

   ```bash
   git push origin main
   ```

2. Streamlit Community Cloud despliega automáticamente desde GitHub
   (`share.streamlit.io` → app `app_visualizacion` → rama `main` → `app.py`).
   URL pública: la subdominio elegido en `*.streamlit.app`.

## Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Estructura

- `app.py` — aplicación Streamlit
- `Casos a correr.xlsx` — tabla de parámetros de los casos
- `resultados_csv/` — resultados de cada caso (240 CSV)
- `.streamlit/config.toml` — configuración de Streamlit (headless en la nube)
