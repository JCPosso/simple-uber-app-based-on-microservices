# Ride-Sharing Platform – Microservice Architecture (AWS Cloud Prototype)

## Resumen
Proyecto que diseña e implementa una plataforma de ride-sharing basada en microservicios (inspirada en sistemas tipo Uber). Demuestra cómo una arquitectura distribuida gestiona usuarios, conductores, viajes y pagos, priorizando escalabilidad, modularidad e interacción en tiempo real. Implementado en Python y desplegado en AWS (Lambda, API Gateway).

---

## Modelado de Dominio

Los modelos del dominio son implementados como Pydantic.
Entidades principales:

- User: userId, name, email, phone
- Driver: driverId, name, carModel, status (OFFLINE|AVAILABLE|ON_TRIP), location
- Ride: rideId, riderId, driverId, pickup, dropoff, status, fare
- Payment: paymentId, rideId, amount, method, status

Estados típicos de un ride: REQUESTED → MATCHED → ACCEPTED → STARTED → COMPLETED → PAID

<p align="center">
  <img src="img/design.png" />
</p>

## Metáfora de Diseño
- User Service = Recepción
- Driver Service = Centro de operaciones
- Ride Service = Despacho
- Payment Service = Facturación

Cada servicio con responsabilidad clara para modularidad y escalado.

##  URIs de Recursos (Endpoints REST)

| Recurso | Método | URI | Descripción |
|---|---:|---|---|
| Users | POST | /api/v1/users | Crear usuario |
| Users | GET | /api/v1/users/{id} | Obtener usuario |
| Users | GET | /api/v1/users | Obtener usuarios |
| Drivers | POST | /api/v1/drivers | Registrar conductor |
| Drivers | POST | /api/v1/drivers/{id}/location | Actualizar ubicacion conductor |
| Drivers | GET | /api/v1/drivers | Obtener conductores |
| Drivers | GET | /api/v1/drivers/available | Conductores Disponibles |
| Drivers | PUT | /api/v1/drivers/{id}/status | Actualizar disponibilidad |
| Drivers | GET | /api/v1/drivers/{id} | Obtener detalles conductor |
| Rides | POST | /api/v1/rides | Solicitar viaje |
| Rides | GET | /api/v1/rides | Listar viajes |
| Rides | PATCH | /api/v1/rides/{id}/assign | Asignar viaje |
| Rides | GET | /api/v1/rides/{id} | Obtener detalle de viaje |
| Payments | POST | /api/v1/payments | Registrar pago |
| Payments | GET | /api/v1/payments | Obtener pagos |
| Payments | GET | /api/v1/payments/{id} | Obtener pago |
| Payments | POST | /api/v1/payments/{id}/state | Actualizar estado del pago |

Todos los endpoints siguen principios REST y devuelven JSON.

---
## Arquitectura

- API Gateway: entrada REST
- AWS Lambda (Python 3.13): lógica de negocio
- EC2: motor de matching
- RABBITMQ: mensajería asíncrona

La aplicacion estara distribuida en 4 microservicios y un servicio de mensajeria RabbitMQ servido en un contenedor docker y al igual que un servicio adicional
llamado matching worker que se encargara de asignar viajes solicitados a conductores disponibles.

![architecture.png](img/architecture.png)


| Servicio | Responsabilidad | Componentes AWS |
|---|---:|---|
| User Service | Gestión de usuarios | Lambda + API Gateway |
| Driver Service | Gestión de conductores | Lambda + API Gateway |
| Ride Service | Solicitudes y estado de viajes | Lambda + API Gateway |
| Payment Service | Facturación y pagos | Lambda + API Gateway |
| Matching Engine | Asignación de drivers | EC2 |

## Representación de Recursos (JSON)

Ejemplo Ride:
```json
{
    "riderId":"ussdfer-1234",
    "pickup":{"lat":4.6,"lon":-74.07},
    "dropoff":{"lat":4.7,"lon":-74.10},
    "paymentMethodId":"card-1"
  }
```
---

## Desarrollo local

La implementación contempla tres microservicios desarrollados con el framework FastAPI (Python). Para empaquetar cada servicio se usa virtualenv para crear entornos aislados.

El `docker-compose.yml` del repositorio actualmente ejecuta la infraestructura mínima (RabbitMQ) y el `matching_worker` (consumer). Las APIs (`auth`, `users`, `drivers`, `rides`, `payments`) están pensadas para desplegarse como Lambdas; sus Dockerfiles locales fueron deshabilitados para evitar builds accidentales.

Flujo recomendado para desarrollo local:

1) Levantar RabbitMQ (y opcionalmente el worker) con Docker Compose:

```bash
docker compose up -d rabbitmq
# opcional: ejecutar el worker en Docker
docker compose up --build -d matching_worker
```

2) Ejecutar las APIs localmente con `uvicorn` cuando necesites probarlas en tu máquina (ejemplo para `rides`):


Instalación:
https://virtualenv.pypa.io/en/latest/installation.html

Ejemplo en Debian/Ubuntu:
```bash
sudo apt install python3-virtualenv
```

Ingresamos a la carpeta del servicio y se crea el entorno virtual:
```bash
# Entrar en la carpeta del servicio
cd src/services/<service-name>

python3 -m venv .venv
source .venv/bin/activate
```
Instalar requisitos del entorno:
```bash
pip install -r requirements.txt
```

o hacer Instalación directa de paquetes clave:
```bash
pip install fastapi
pip install "uvicorn[standard]"
pip install mangum
```
### Dependencias
Notas:
- Uvicorn es el servidor ASGI recomendado para ejecutar FastAPI en desarrollo y pruebas.
- Mangum permite adaptar las llamadas de API Gateway a aplicaciones ASGI para desplegar FastAPI en AWS Lambda.

En algunos sistemas puede ser necesario instalar uvicorn globalmente:
```bash
sudo apt install uvicorn
```
Si RabbitMQ corre en Docker
```bash
export RABBITMQ_URL="amqp://guest:guest@localhost:5672/"
PYTHONPATH=$(pwd) uvicorn services.rides.app:app --host 0.0.0.0 --port 8003 --reload
```

3) Crear un ride (ejemplo):

```bash
curl -s -X POST http://localhost:8003/api/v1/rides \
  -H "Content-Type: application/json" \
  -d '{"riderId":"user-123","pickup":{"lat":4.6,"lon":-74.07},"dropoff":{"lat":4.7,"lon":-74.10}}' | jq
```

4) Verificar consumo en el worker:

```bash
docker compose logs -f matching_worker
```

## Depliegue en Lambda AWS

### Empaquetando servicios en .zip

- Para cargar nuestros microservicios en lambda debemos empaquetarlos en un archivo .zip junto a las librerias python a utilizar para ello podemos usar estos comandos:
```bash

# Nos ubicamos en la carpeta del servicio
../../drivers
# Creamos directorio temporal
mkdir -p lambda-package
# levantamos una imagen dockker  donde se instalaran las dependencias
docker run --rm --platform linux/amd64 \
  -v "$PWD":/var/task \
  -w /var/task \
  python:3.11-slim \
  pip install -r requirements.txt -t lambda-package --no-cache-dir

#copiamos el contendo de la carpeta app en el directorio temporal
cp -r app lambda-package/

# empaquetamos en un .zip
cd lambda-package
zip -r9 ../api-service.zip .
cd ..
rm -rf lambda-package
```
### Cargar zip a aws Lambda
1. creamos 4 funciones lambda de la siguiente manera
![lambda.png](img/lambda.png)
2. Seleccionamos cargar archivo .zip
![lambda.png](img/lambda.png)
3. Generamos la lambda y en la sección de código seleccionamos configurar tiempo de ejecución y editamos
![lambda.png](img/lambda.png)
4. Cambaimos datos por app.main.handler
### Api Gateway
1. Nos dirigimos a api gateway y generamos nuevo API de REST
![lambda.png](img/lambda.png)
2. Creamos los 4 recursos siguiendo el nombre de ruta puesto en los archivos main.py de cada servicio
![lambda.png](img/lambda.png)
3. Por cada endpoint creamos tipode método ANY, Funcion Lambda, seleccionamos integracion proxy de lambda, seleccionamos la lambda correspondiente al servicio y le damos en guardar.
![lambda.png](img/lambda.png)
4. Después para cada Recurso creamos un recurso de tipo proxy con la misma configuracion anterior.
![lambda.png](img/lambda.png)
5. Finalmente, debemos tener los servicios similar a lo siguiente:
![lambda.png](img/lambda.png)
6. Damos click en implementar API y generamos un nuevo stage lo llamamos dev y guardamos
![lambda.png](img/lambda.png)
### EC2
1. Ingresamos a una EC2 previamente creada
![lambda.png](img/lambda.png)
2. Luego, vamos a necesitar desargar las imagenes docker. Para ello, ejecutamos los siguientes comandos:
RabbitMQ:
```bash
docker run -d --name rabbitmq \
  --network app_network \
  -p 5672:5672 -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=guest \
  -e RABBITMQ_DEFAULT_PASS=guest \
  rabbitmq:3-management
```
matching_worker:
- Es Indispensable  tener los servicios de conductores y viajes previamente creados e integrados con api gateway.
- Ingresamos las url de los servicios y mantenemos el resto de variables igual:
```bash
docker run -d --name matching_worker \
  --network app_network \
  -e PYTHONUNBUFFERED=1 \
  -e PYTHONPATH=/workspace \
  -e RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/ \
  -e DRIVERS_URL=https://swgyv053e7.execute-api.us-east-1.amazonaws.com/dev/drivers-api\
  -e RIDES_URL=https://swgyv053e7.execute-api.us-east-1.amazonaws.com/dev/rides-api\
  juancamiloposso/matching_worker:latest
```
### Configurando reglas seguridad y VPC
1. nos digirimos al servicio VPC de AWS, y vamos a la seccion security groups
![lambda.png](img/lambda.png)
2. creamos uno nuevo le damos un nombre, seleccionamos VPC defecto  y aceptamos todo el trafico entrante y le damos en crear
![lambda.png](img/lambda.png)
3. Nos dirigimos a la lambda de rides service y en el apartado configuración seleccionamos VPC y damos en crear nuevo.
![lambda.png](img/lambda.png)
4. elegimos la VPC por defecto , seleccionamos 2 subnets disponibles y el grupo de seguridad previamente creado
![lambda.png](img/lambda.png)
5. guardamos y nos dirigimos al EC2 e ingresamos al apartado security
![lambda.png](img/lambda.png)
6. ajustamos las Inbopund rules agregando la nueva regla que nos permitirá aceptar trafico a través del puerto 5672 que se usará para RabbitMQ

### Pruebas Endpoints

### Diagramas y OpenAPI

La documentación OpenAPI mínima para los servicios está en `docs/openapi/`.
El modelado del dominio se mantiene en código (principalmente en `shared_models.py`) y en las definiciones Pydantic dentro de cada servicio.

Usa las especificaciones en `docs/openapi/*.yaml` para generar stubs, documentación interactiva (Swagger/Redoc) o pruebas de contrato.


```bash
# instalar redoc-cli si no está: npm i -g redoc-cli
redoc-cli serve docs/openapi/rides.yaml
```

---

## Referencias & Autor
- REST API Tutorial
- AWS Lambda Developer Guide
- Autor: JCPosso ( AYGO - AWS Academy Learner Lab – 2025)