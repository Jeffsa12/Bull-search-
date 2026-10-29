# Genealogía Lechera Online

Aplicación Flask conectada a internet. Busca un código NAAB en fuentes públicas, extrae nombre, PTA y relaciones de pedigrí cuando la página los expone. Incluye respaldo local para 007HO16276.

## Ejecutar en Windows
1. Instale Python 3.11 o superior.
2. Abra PowerShell en esta carpeta.
3. Ejecute: `py -m venv .venv`
4. Ejecute: `.venv\Scripts\activate`
5. Ejecute: `pip install -r requirements.txt`
6. Ejecute: `python app.py`
7. Abra `http://127.0.0.1:5000`

## Publicar gratis en Render
Suba esta carpeta a GitHub, cree un Web Service en Render y use `pip install -r requirements.txt` y `gunicorn app:app`. El archivo render.yaml ya contiene la configuración.

## Consideraciones
- El extractor depende del HTML público y puede requerir ajustes si un proveedor cambia su página.
- Respete términos de uso y robots.txt de cada proveedor.
- Para producción, la opción estable es licenciar una API o carga oficial de CDCB/NAAB.
- Los PTA deben compararse en misma raza, fecha y base genética.

## Profundidad ampliada
La interfaz permite elegir entre 4 y 8 generaciones. El servidor intenta completar cada antecesor de forma recursiva por nombre. Para evitar bloqueos, limita cada búsqueda a 5 resultados y la profundidad a 8 generaciones. Un árbol binario completo de 8 generaciones puede contener hasta 255 animales, por lo que la consulta puede tardar varios minutos y algunas ramas pueden quedar como N/D si la fuente no publica la información.
