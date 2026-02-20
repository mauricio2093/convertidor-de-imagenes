import os

# Directorio de los videos
directorio = r'D:\programacion\python\imgePNGtoJPEG\videoOut'

# Carpeta donde se guardarán los archivos renombrados
directorio_out = r'D:\programacion\python\imgePNGtoJPEG\videoOut2'

# Verificamos si la carpeta de salida existe; si no, la creamos
if not os.path.exists(directorio_out):
    os.makedirs(directorio_out)

# Recorremos todos los archivos en el directorio
for filename in os.listdir(directorio):
    if filename.endswith('.mp4'):
        # Removemos el texto "Y2meta.app - " o "Y2meta.app-" del nombre del archivo
        nuevo_nombre = filename.replace('Y2meta.app - ', '').replace('Y2meta.app-', '')
        
        # Nos aseguramos de que solo haya un guion y un espacio después del número
        partes = nuevo_nombre.split('-', 1)
        nuevo_nombre = f"{partes[0].strip()}- {partes[1].strip()}"

        # Creamos la ruta completa del archivo original y del nuevo archivo
        old_path = os.path.join(directorio, filename)
        new_path = os.path.join(directorio_out, nuevo_nombre)

        # Renombramos y movemos el archivo
        os.rename(old_path, new_path)

        print(f'Renombrado: {filename} -> {nuevo_nombre}')

print("Renombrado completado.")
