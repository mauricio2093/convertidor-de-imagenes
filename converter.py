from PIL import Image
import os

def optimize_image(input_path, output_path, quality=85):
    """
    Optimiza la imagen para la web cambiando su formato de PNG a JPEG.

    :param input_path: Ruta de la imagen de entrada (PNG).
    :param output_path: Ruta donde se guardará la imagen optimizada (JPEG).
    :param quality: Calidad de la imagen JPEG resultante (1-100).
    """
    with Image.open(input_path) as img:
        # Convertir a JPEG y optimizar
        img = img.convert("RGB")  # Convertir a RGB si es necesario
        img.save(output_path, "JPEG", quality=quality, optimize=True)

# Ejemplo de uso
input_dir = r'D:\programacion\python\imgePNGtoJPEG\imgIn'
output_dir = r'D:\programacion\python\imgePNGtoJPEG\imgIn'
quality = 85  # Ajusta este valor según tus necesidades de calidad

# Asegurarse de que el directorio de salida exista
os.makedirs(output_dir, exist_ok=True)

for filename in os.listdir(input_dir):
    if filename.lower().endswith('.png'):
        input_path = os.path.join(input_dir, filename)
        output_filename = os.path.splitext(filename)[0] + '.jpeg'
        output_path = os.path.join(output_dir, output_filename)
        optimize_image(input_path, output_path, quality=quality)

print("Imágenes optimizadas correctamente.")
