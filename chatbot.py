from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

API_BASE_URL = "http://localhost/3-prueba/web2-entrega3/api"

class ChatbotEngine:
    def __init__(self):
        self.token = None
        self.user_data = {}
        self.conversation_state = None

    def procesar_mensaje(self, mensaje: str) -> Dict[str, str]:
        """
        Procesa el mensaje del usuario con manejo de estados
        """
        try:
            mensaje = mensaje.lower().strip()
            logger.info(f"Procesando mensaje: {mensaje}")
            logger.info(f"Estado actual: {self.conversation_state}")

            if mensaje in ['hola', 'ayuda', 'help']:
                return {
                    "response": "¡Hola! ¿En qué puedo ayudarte? Puedes:\n" +
                              "- Asignar turno\n" +
                              "- eliminar turno\n" +
                              "- Ver turnos existentes"
                }

            if mensaje == 'ver turnos existentes':
                return self.obtener_turnos()

            if not self.token:
                return self.manejar_autenticacion(mensaje)

            return self.manejar_solicitud_turno(mensaje)
        except Exception as e:
            logger.error(f"Error en procesar_mensaje: {str(e)}")
            return {"response": "Ocurrió un error procesando tu mensaje. Por favor, intenta nuevamente."}

    def manejar_autenticacion(self, mensaje: str) -> Dict[str, str]:
        """
        Maneja el flujo de autenticación
        """
        try:
            logger.info(f"Manejando autenticación. Estado actual: {self.conversation_state}")
            logger.info(f"Datos actuales: {self.user_data}")

            if not self.conversation_state:
                self.conversation_state = 'pedir_usuario'
                return {"response": "Por favor, ingresa tu usuario:"}

            if self.conversation_state == 'pedir_usuario':
                self.user_data['usuario'] = mensaje
                self.conversation_state = 'pedir_contrasena'
                return {"response": "Ahora, por favor ingresa tu contraseña:"}

            if self.conversation_state == 'pedir_contrasena':
                token = self.obtener_token(self.user_data['usuario'], mensaje)
                
                if token:
                    self.conversation_state = 'autenticado'
                    return {
                        "response": "Autenticación exitosa. ¿En qué puedo ayudarte?\n" +
                                  "Opciones:\n" +
                                  "- Asignar turno\n" +
                                  "- eliminar turno\n" +
                                  "- Ver turnos existentes"
                    }
                else:
                    self.conversation_state = None
                    self.user_data.clear()
                    return {"response": "Credenciales inválidas. Por favor, intenta nuevamente."}

        except Exception as e:
            logger.error(f"Error en manejar_autenticacion: {str(e)}")
            self.conversation_state = None
            self.user_data.clear()
            return {"response": "Error en el proceso de autenticación. Por favor, intenta nuevamente."}

    def obtener_token(self, usuario: str, contrasena: str) -> Optional[str]:
     """
     Obtiene un token de autenticación
     """
     try:
        logger.info(f"Intentando obtener token para usuario: {usuario}")
        
        response = requests.get(
            f"{API_BASE_URL}/usuarios/token",
            auth=(usuario, contrasena)
        )
        
        logger.info(f"Código de estado de autenticación: {response.status_code}")
        logger.info(f"Respuesta de autenticación: {response.text}")

        if response.status_code == 200:
            token = response.text.strip().strip('"')  # Remove whitespace and quotes
            if token:
                self.token = token  # Store without quotes
                logger.info("Token obtenido exitosamente")
                return token
            else:
                logger.warning("No se encontró token en la respuesta")
                return None

        logger.warning(f"Error de autenticación: {response.status_code}")
        return None

     except Exception as e:
        logger.error(f"Error obteniendo token: {str(e)}")
        return None

    def obtener_turnos(self) -> Dict[str, str]:
        """Obtiene los turnos existentes"""
        try:
            response = requests.get(f"{API_BASE_URL}/turnos")
            
            if response.status_code != 200:
                logger.error(f"Error HTTP: {response.status_code}")
                return {"response": f"Error al obtener turnos: {response.status_code}"}
            
            turnos = response.json()
            
            if not turnos:
                return {"response": "No hay turnos disponibles actualmente."}
            
            return {"response": "Turnos obtenidos correctamente", "turnos": turnos}
        
        except Exception as e:
            logger.error(f"Error obteniendo turnos: {str(e)}")
            return {"response": "Error al obtener los turnos."}

    def manejar_solicitud_turno(self, mensaje: str) -> Dict[str, str]:
        """
        Maneja las solicitudes de gestión de turnos
        """
        try:
            logger.info(f"Manejando solicitud de turno. Estado: {self.conversation_state}")
            logger.info(f"Datos actuales: {self.user_data}")

            if "asignar turno" in mensaje:
                self.conversation_state = 'asignar_turno_nombre'
                return {"response": "Vamos a asignar un turno. ¿Cuál es tu nombre?"}

            if self.conversation_state == 'asignar_turno_nombre':
                self.user_data['nombre'] = mensaje
                self.conversation_state = 'asignar_turno_fecha'
                return {"response": "¿Qué fecha deseas para el turno? (YYYY-MM-DD)"}

            if self.conversation_state == 'asignar_turno_fecha':
                if not self.validar_formato_fecha(mensaje):
                    return {"response": "Formato de fecha inválido. Por favor usa YYYY-MM-DD"}
                self.user_data['fecha'] = mensaje
                self.conversation_state = 'asignar_turno_hora'
                return {"response": "¿A qué hora te gustaría el turno? (HH:MM:SS)"}

            if self.conversation_state == 'asignar_turno_hora':
                if not self.validar_formato_hora(mensaje):
                    return {"response": "Formato de hora inválido. Por favor usa HH:MM:SS"}
                return self.crear_turno(mensaje)
            


             # Modificar turno
            if "modificar turno" in mensaje:
                self.conversation_state = 'modificar_turno_nombre'
                return {"response": "Por favor, proporciona un ID de turno válido (debe ser un número)."}
                
            
            if self.conversation_state == 'modificar_turno_nombre':
                self.user_data['id_turno'] = mensaje
                self.conversation_state = 'modificar_turno_fecha'
                return {"response": "Vamos a asignar un turno. ¿Cuál es tu nombre?"}

            if self.conversation_state == 'modificar_turno_nombre':
                self.user_data['nombre'] = mensaje
                self.conversation_state = 'modificar_turno_fecha'
                return {"response": "¿Qué fecha deseas para el turno? (YYYY-MM-DD)"}

            if self.conversation_state == 'modificar_turno_fecha':
                if not self.validar_formato_fecha(mensaje):
                    return {"response": "Formato de fecha inválido. Por favor usa YYYY-MM-DD"}
                self.user_data['fecha'] = mensaje
                self.conversation_state = 'modificar_turno_hora'
                return {"response": "¿A qué hora te gustaría el turno? (HH:MM:SS)"}

            if self.conversation_state == 'modificar_turno_hora':
                if not self.validar_formato_hora(mensaje):
                    return {"response": "Formato de hora inválido. Por favor usa HH:MM:SS"}
                return self.modificar_turno(mensaje)
            


             # Solicitud de cancelar turno
            if "eliminar turno" in mensaje:
                 self.conversation_state = 'asignar_id_turno'
                 return {"response": "Por favor, proporciona un ID de turno válido (debe ser un número)."}

            if self.conversation_state == 'asignar_id_turno':
                 if not mensaje.isdigit():
                     return {"response": "El ID del turno debe ser un número. Por favor, inténtalo nuevamente."}

                 # Guardar el ID del turno en los datos del usuario
                 self.user_data['id_turno'] = mensaje

                 # Llamar al método para cancelar el turno
                 id_turno = self.user_data['id_turno']
                 return self.cancelar_turno(id_turno)

              
         
            

            return {"response": "Lo siento, no entendí tu solicitud. Sé más específico."}

        except Exception as e:
            logger.error(f"Error en manejar_solicitud_turno: {str(e)}")
            return {"response": "Error procesando la solicitud de turno."}
        
    

    def cancelar_turno(self, id_turno: str) -> Dict[str, str]:
     """
     Cancela un turno en la API usando el ID del turno.
     """
     try:
        logger.info(f"Intentando cancelar turno con ID: {id_turno}")
        
        # Limpiamos el token por si tiene comillas adicionales
        token = self.token.strip('"') if isinstance(self.token, str) else self.token
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Headers enviados para cancelar turno: {headers}")
        
        # Realizamos la solicitud DELETE a la API
        response = requests.delete(
            f"{API_BASE_URL}/turnos/{id_turno}",
            headers=headers
        )
        
        logger.info(f"Respuesta al intentar cancelar turno: {response.status_code}")
        logger.info(f"Contenido respuesta: {response.text}")
        
        if response.status_code == 200:
          return {"response": f"El turno con ID {id_turno} ha sido cancelado exitosamente."}
        elif response.status_code == 404:
            return {"response": f"No se encontró un turno con ID {id_turno}."}
        else:
            error_msg = response.text if response.text else "Error desconocido"
            return {"response": f"Error al cancelar el turno: {error_msg}"}
    
     except requests.exceptions.RequestException as e:
        logger.error(f"Error de red al cancelar turno: {str(e)}")
        return {"response": "Error de conexión al intentar cancelar el turno."}
     except Exception as e:
        logger.error(f"Error inesperado al cancelar turno: {str(e)}")
        return {"response": "Error inesperado al intentar cancelar el turno."}
    

    def validar_formato_fecha(self, fecha: str) -> bool:
        """Valida el formato de la fecha"""
        try:
            from datetime import datetime
            datetime.strptime(fecha, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def validar_formato_hora(self, hora: str) -> bool:
        """Valida el formato de la hora"""
        try:
            from datetime import datetime
            datetime.strptime(hora, '%H:%M:%S')
            return True
        except ValueError:
            return False

    def crear_turno(self, hora_turno: str) -> Dict[str, str]:
     """Crea un turno en la API"""
     try:
        logger.info(f"Intentando crear turno para: {self.user_data['nombre']}")
        
        response_cliente = requests.get(
            f"{API_BASE_URL}/clientes",
            params={"nombre": self.user_data['nombre']}
        )
        
        logger.info(f"Respuesta búsqueda cliente: {response_cliente.status_code}")
        logger.info(f"Contenido respuesta cliente: {response_cliente.text}")
        
        if response_cliente.status_code != 200:
            return {"response": "Error al buscar cliente en el sistema."}
        
        # Parseamos la respuesta JSON
        response_data = response_cliente.json()
        
        # Accedemos a la lista de clientes dentro de 'data'
        clientes = response_data.get('data', [])
        
        if not clientes:
            return {"response": "No se encontró un cliente con ese nombre en el sistema."}
        
        # Tomamos el primer cliente de la lista
        cliente_id = clientes[0]["id_cliente"]
        logger.info(f"ID del cliente encontrado: {cliente_id}")

        turno_data = {
            "id_cliente": cliente_id,
            "fecha_turno": self.user_data['fecha'],
            "hora_turno": hora_turno,
            "finalizado": 0
        }
        
        logger.info(f"Datos del turno a crear: {turno_data}")
        logger.info(f"Token original: {self.token}")

        # Remove quotes from token if present
        token = self.token.strip('"') if isinstance(self.token, str) else self.token

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        logger.info(f"Headers enviados: {headers}")

        response_turno = requests.post(
            f"{API_BASE_URL}/turnos",
            headers=headers,
            json=turno_data
        )
        
        logger.info(f"Respuesta creación turno: {response_turno.status_code}")
        logger.info(f"Contenido respuesta turno: {response_turno.text}")

        if response_turno.status_code == 201:
            self.conversation_state = None
            return {
                "response": f"Turno asignado para {self.user_data['nombre']} " +
                          f"el {self.user_data['fecha']} a las {hora_turno}."
            }
        
        error_msg = response_turno.text if response_turno.text else "Error desconocido"
        return {"response": f"Error al crear el turno: {error_msg}"}

     except requests.exceptions.RequestException as e:
        logger.error(f"Error de red creando turno: {str(e)}")
        return {"response": "Error de conexión al crear el turno."}
     except ValueError as e:
        logger.error(f"Error parseando JSON: {str(e)}")
        return {"response": "Error procesando la respuesta del servidor."}
     except Exception as e:
        logger.error(f"Error creando turno: {str(e)}")
        return {"response": "Error inesperado al crear el turno."}
     

    def modificar_turno(self, hora_turno: str) -> Dict[str, str]:
     """Crea un turno en la API"""
     try:
        logger.info(f"Intentando crear turno para: {self.user_data['nombre']}")
        
        response_cliente = requests.get(
            f"{API_BASE_URL}/clientes",
            params={"nombre": self.user_data['nombre']}
        )
        
        logger.info(f"Respuesta búsqueda cliente: {response_cliente.status_code}")
        logger.info(f"Contenido respuesta cliente: {response_cliente.text}")
        
        if response_cliente.status_code != 200:
            return {"response": "Error al buscar cliente en el sistema."}
        
        # Parseamos la respuesta JSON
        response_data = response_cliente.json()
        
        # Accedemos a la lista de clientes dentro de 'data'
        clientes = response_data.get('data', [])
        
        if not clientes:
            return {"response": "No se encontró un cliente con ese nombre en el sistema."}
        
        # Tomamos el primer cliente de la lista
        cliente_id = clientes[0]["id_cliente"]
        logger.info(f"ID del cliente encontrado: {cliente_id}")

        turno_data = {
            "id_cliente": cliente_id,
            "fecha_turno": self.user_data['fecha'],
            "hora_turno": hora_turno,
            "finalizado": 0
        }
        
        logger.info(f"Datos del turno a crear: {turno_data}")
        logger.info(f"Token original: {self.token}")

        # Remove quotes from token if present
        token = self.token.strip('"') if isinstance(self.token, str) else self.token

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        logger.info(f"Headers enviados: {headers}")

        response_turno = requests.put(
            f"{API_BASE_URL}/turnos/{self.user_data['id_turno']}",
            headers=headers,
            json=turno_data
        )
        
        logger.info(f"Respuesta creación turno: {response_turno.status_code}")
        logger.info(f"Contenido respuesta turno: {response_turno.text}")

        if response_turno.status_code == 201:
            self.conversation_state = None
            return {
                "response": f"Turno asignado para {self.user_data['nombre']} " +
                          f"el {self.user_data['fecha']} a las {hora_turno}."
            }
        
        error_msg = response_turno.text if response_turno.text else "Error desconocido"
        return {"response": f"Error al crear el turno: {error_msg}"}

     except requests.exceptions.RequestException as e:
        logger.error(f"Error de red creando turno: {str(e)}")
        return {"response": "Error de conexión al crear el turno."}
     except ValueError as e:
        logger.error(f"Error parseando JSON: {str(e)}")
        return {"response": "Error procesando la respuesta del servidor."}
     except Exception as e:
        logger.error(f"Error creando turno: {str(e)}")
        return {"response": "Error inesperado al crear el turno."}
     
    


chatbot_engine = ChatbotEngine()

@app.route('/chat', methods=['POST'])
def chatbot_endpoint():
    """Endpoint principal del chatbot"""
    try:
        data = request.get_json()
        if not data:
            logger.error("No se recibieron datos JSON")
            return jsonify({"response": "No se recibieron datos."}), 400

        user_input = data.get("message", "").lower()
        if not user_input:
            logger.warning("Mensaje vacío recibido")
            return jsonify({"response": "Por favor, envía un mensaje."}), 400

        logger.info(f"Mensaje recibido: {user_input}")
        response = chatbot_engine.procesar_mensaje(user_input)
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error en el endpoint: {str(e)}")
        return jsonify({"response": "Error interno del servidor."}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)