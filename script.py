import os
from dotenv import load_dotenv
import subprocess as sp
import random
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()
parameters = {
    "image_name": os.getenv("IMAGE_NAME"),
    "image_version": os.getenv("IMAGE_TAG"),
    "resource_group": os.getenv("RESOURCE_GROUP"),
    "location": os.getenv("LOCATION"),
    "acr_name": os.getenv("ACR_NAME"),
    "container_name": os.getenv("CONTAINER_NAME"),
    "port_container": int(os.getenv("PORT_CONTAINER"))
}

def docker_build():
    image_name = f"{parameters['image_name']}:{parameters['image_version']}"
    logging.info(f"Creando Imagen: {image_name}")
    docker_build = sp.run(["docker", "build", "-t", image_name, "."], capture_output=True)
    logging.info(f"Imagen creada: {image_name}")
    logging.info(docker_build.stdout.decode('utf-8'))

def docker_images():
    image_name = f"{parameters['image_name']}:{parameters['image_version']}"
    logging.info(f"Verificando imagen: {image_name}")
    try:
        imagen = sp.run(["docker", "images", "--format", "json", "--filter", f"reference={image_name}"], 
                        capture_output=True, text=True, check=True)
        if imagen.stdout:
            logging.info(imagen.stdout)
            return True
        else:
            logging.error(f"IMAGEN {image_name} NO CREADA")
            return False
    except sp.CalledProcessError as e:
        logging.error(f"Error al verificar imagen: {e}")
        return False

def analyze_image(image_name, image_version):
    full_image_name = f"{image_name}:{image_version}"
    logging.info(f"Analizando imagen con Grype: {full_image_name}")
    try:
        result = sp.run(["grype", full_image_name], capture_output=True, text=True, check=True)
        vulnerabilities = result.stdout
        
        if vulnerabilities:
            logging.info("Análisis de vulnerabilidades completado:")
            logging.info(vulnerabilities)
            return True, vulnerabilities  
        return False, None
    except sp.CalledProcessError as e:
        logging.error(f"Error al analizar la imagen: {e}")
        return False, None


def az_run():
    filtro = f"[?name=='{parameters['resource_group']}']"
    logging.info(filtro)
        # Verifica si existe un grupo de recursos
    try:
        catch_groups = sp.run(["az", "group", "list", "--query", filtro], capture_output=True, text=True, check=True)
        if catch_groups.stdout:
            logging.info(catch_groups.stdout)
        else:
            logging.info(f"Creando grupo: {parameters['resource_group']}, en la localizacion: {parameters['location']}")
            create_r_group = sp.run(["az", "group", "create", "--name", parameters['resource_group'], "--location", parameters['location']], 
                                    capture_output=True)
            logging.info(create_r_group.stdout.decode('utf-8'))
        
        # Crear Registro de Contenedor
        logging.info(f"Creando ACR: {parameters['acr_name']}")
        create_acr = sp.run(["az", "acr", "create", "--resource-group", parameters['resource_group'], 
                             "--name", parameters['acr_name'], "--sku", "Basic"], capture_output=True)
        logging.info(create_acr.stdout.decode('utf-8'))
        
        # Iniciar sesión
        logging.info(f"Iniciando sesión en ACR: {parameters['acr_name']}")
        login_acr = sp.run(["az", "acr", "login", "--name", parameters['acr_name']], capture_output=True)
        logging.info(login_acr.stdout.decode('utf-8'))
        
        # Etiqueta y empuja imagen
        tagged_image = f"{parameters['acr_name']}.azurecr.io/{parameters['image_name']}:{parameters['image_version']}"
        logging.info(f"Etiquetando imagen: {tagged_image}")
        tag_image = sp.run(["docker", "tag", f"{parameters['image_name']}:{parameters['image_version']}", tagged_image], 
                           capture_output=True)
        logging.info(tag_image.stdout.decode('utf-8'))
        
        logging.info(f"Empujando imagen: {tagged_image}")
        push_image = sp.run(["docker", "push", tagged_image], capture_output=True)
        logging.info(push_image.stdout.decode('utf-8'))
        
        # Listar repositorios
        logging.info(f"Listando repositorios de ACR: {parameters['acr_name']}")
        list_repos = sp.run(["az", "acr", "repository", "list", "--name", parameters['acr_name'], "--output", "table"], 
                            capture_output=True, text=True)
        logging.info(list_repos.stdout)
        
        # Crear contenedor
        dns_label = f"dns-{parameters['acr_name']}-{random.randint(1000, 9999)}"
        logging.info(f"Creando contenedor: {parameters['container_name']} con DNS label: {dns_label}")
        create_container = sp.run(["az", "container", "create", "--resource-group", parameters['resource_group'], 
                                   "--name", parameters['container_name'], "--image", tagged_image, 
                                   "--cpu", "1", "--memory", "1", "--registry-login-server", f"{parameters['acr_name']}.azurecr.io",
                                   "--ip-address", "Public", "--location", parameters['location'],
                                   "--dns-name-label", dns_label, "--ports", str(parameters['port_container'])], 
                                   capture_output=True)
        logging.info(create_container.stdout.decode('utf-8'))
    
    except sp.CalledProcessError as e:
        logging.error(f"Error en az: {e}")

def docker_run():
    if docker_images():
        has_vulnerabilities, vulnerabilities = analyze_image(parameters['image_name'], parameters['image_version'])
        if has_vulnerabilities:
            logging.info("Se encontraron las siguientes vulnerabilidades:")
            logging.info(vulnerabilities)
            user_input = input("¿Deseas continuar con el push a Azure? (s/n): ")
            if user_input.lower() == 's':
                az_run()
            else:
                logging.info("Push a Azure cancelado por el usuario.")
        else:
            logging.info("No se encontraron vulnerabilidades. Procediendo a empujar la imagen a Azure...")
            az_run()


if __name__ == "__main__":
    docker_build()
    docker_run()
