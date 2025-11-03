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
| Drivers | POST | /api/v1/drivers | Registrar conductor |
| Drivers | PUT | /api/v1/drivers/{id}/status | Actualizar disponibilidad |
| Drivers | GET | /api/v1/drivers/{id} | Obtener detalles conductor |
| Rides | POST | /api/v1/rides | Solicitar viaje |
| Rides | GET | /api/v1/rides/{id} | Obtener detalle de viaje |
| Rides | PUT | /api/v1/rides/{id}/status | Actualizar estado de viaje |
| Payments | POST | /api/v1/payments | Registrar pago |
| Payments | GET | /api/v1/payments/{id} | Obtener pago |

Todos los endpoints siguen principios REST y devuelven JSON.

---

## Representación de Recursos (JSON)

Ejemplo Ride:
```json
{
  "rideId": "ride-12345",
  "riderId": "user-101",
  "driverId": "driver-55",
  "pickupLocation": "Main St 123",
  "dropoffLocation": "Airport",
  "status": "IN_PROGRESS",
  "fare": 25.50
}
```

Ejemplo error:
```json
{
  "error": "INVALID_REQUEST",
  "message": "Missing riderId field"
}
```
---

## Arquitectura

- API Gateway: entrada REST
- AWS Lambda (Python 3.9): lógica de negocio
- EC2: motor de matching
- RABBITMQ: mensajería asíncrona

---

## Microservicios

| Servicio | Responsabilidad | Componentes AWS |
|---|---:|---|
| User Service | Gestión de usuarios | Lambda + API Gateway |
| Driver Service | Gestión de conductores | Lambda + API Gateway |
| Ride Service | Solicitudes y estado de viajes | Lambda + API Gateway |
| Payment Service | Facturación y pagos | Lambda + API Gateway |
| Matching Engine | Asignación de drivers | EC2 |

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

Notas:
- Si ejecutas APIs localmente y el worker en Docker, configura `DRIVERS_URL` y `RIDES_URL` del worker para usar `host.docker.internal` (o publica los puertos de las APIs) para que el worker pueda invocarlas.

## Depliegue en Lambda AWS

- Empaquetar el contenido de los servicios junto con el código del servicio.
- Usar Mangum como handler en la aplicación para recibir eventos de API Gateway.

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