from PIL import Image
import os
import tkinter as tk
from tkinter import messagebox

def compress_png(input_folder, output_folder, compression_level=9):
    """
    Comprime todas las imágenes PNG en la carpeta de entrada y las guarda en la carpeta de salida.

    :param input_folder: Carpeta que contiene las imágenes PNG de entrada.
    :param output_folder: Carpeta donde se guardarán las imágenes PNG comprimidas.
    :param compression_level: Nivel de compresión (0-9). 9 es la máxima compresión.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.endswith(".png"):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)

            img = Image.open(input_path)
            img.save(output_path, optimize=True, compress_level=compression_level)
            print(f"Comprimido: {filename} -> {output_path}")

def optimize_image(input_folder, output_folder, quality=85):
    """
    Optimiza las imágenes PNG convirtiéndolas a JPEG.

    :param input_folder: Carpeta que contiene las imágenes PNG de entrada.
    :param output_folder: Carpeta donde se guardarán las imágenes optimizadas (JPEG).
    :param quality: Calidad de la imagen JPEG resultante (1-100).
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith('.png'):
            input_path = os.path.join(input_folder, filename)
            output_filename = os.path.splitext(filename)[0] + '.jpeg'
            output_path = os.path.join(output_folder, output_filename)
            with Image.open(input_path) as img:
                img = img.convert("RGB")
                img.save(output_path, "JPEG", quality=quality, optimize=True)
            print(f"Convertido: {filename} -> {output_path}")

def main():
    # Rutas de las carpetas de entrada y salida
    input_dir = r'D:\programacion\python\imgePNGtoJPEG\imgIn'
    output_dir = r'D:\programacion\python\imgePNGtoJPEG\imgOut'

    # Crear la ventana principal
    root = tk.Tk()
    root.withdraw()  # Ocultar la ventana principal

    # Cuadro de diálogo para elegir la opción
    response = messagebox.askquestion("Elige una opción", "¿Qué deseas hacer?\n\n- Sí: Comprimir PNG a PNG\n- No: Convertir PNG a JPEG")

    if response == 'yes':
        compress_png(input_dir, output_dir)
    elif response == 'no':
        optimize_image(input_dir, output_dir, quality=85)

    print("Operación completada.")

if __name__ == "__main__":
    main()
