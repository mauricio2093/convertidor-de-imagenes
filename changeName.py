import os
import shutil

# Directorio de entrada y salida
directorio = r'D:\programacion\python\imgePNGtoJPEG\videoIn'
directorio_salida = r'D:\programacion\python\imgePNGtoJPEG\videoOut'

# Número inicial
num_inicial = 92

# Crear el directorio de salida si no existe
os.makedirs(directorio_salida, exist_ok=True)

# Listar todos los archivos en el directorio
videos = [f for f in os.listdir(directorio) if f.endswith('.mp4')]
videos.sort()

# Renombrar y mover archivos
for i, video in enumerate(videos, start=num_inicial):
    nuevo_nombre = f"{i}- {video}"
    ruta_origen = os.path.join(directorio, video)
    ruta_destino = os.path.join(directorio_salida, nuevo_nombre)
    
    # Renombrar y mover
    shutil.move(ruta_origen, ruta_destino)
    
    print(f"{video} renombrado y movido a {ruta_destino}")
