# Usa una imagen base de Python
FROM python:3.9-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos del proyecto al contenedor
COPY . /app

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto
EXPOSE 5000

# Define el comando para ejecutar la aplicación
ENTRYPOINT [ "python3", "app.py" ]
