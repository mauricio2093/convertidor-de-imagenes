from PIL import Image
import os

def convert_jpeg_to_webp(input_dir, output_dir):
    try:
        # Crear el directorio de salida si no existe
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Iterar sobre todos los archivos en la carpeta de entrada
        for filename in os.listdir(input_dir):
            if filename.lower().endswith((".jpg", ".jpeg")):  # Verificar extensiones de JPEG
                input_path = os.path.join(input_dir, filename)
                output_path = os.path.join(output_dir, os.path.splitext(filename)[0] + ".webp")

                # Abrir y convertir la imagen
                img = Image.open(input_path).convert("RGB")  # Convertir a RGB
                img.save(output_path, "WEBP")
                print(f"Imagen convertida correctamente: {output_path}")
    except Exception as e:
        print(f"Error al convertir la imagen: {e}")

# Rutas de entrada y salida
input_dir = r'D:\programacion\python\imgePNGtoJPEG\imgIn'
output_dir = r'D:\programacion\python\imgePNGtoJPEG\imgOut'

# Llamar a la función
convert_jpeg_to_webp(input_dir, output_dir)
