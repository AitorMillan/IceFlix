"""Modulo del cliente de IceFlix"""

import sys
import logging
import time
import hashlib
import getpass
from queue import Queue
import os.path
import Ice
import IceStorm
import IceFlix # pylint:disable=import-error
from IceFlix import Media # pylint:disable=unused-import,import-error
from IceFlix import MediaInfo # pylint:disable=unused-import,import-error




LOG_FORMAT = '%(asctime)s - %(levelname)-7s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'

COLA = Queue()
REINTENTOS = 3
ARCHIVO_SUBIDA = None

def setup_logging():
    """Configure the logging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format=LOG_FORMAT,
    )

class ManejadorUsuarios():
    """Clase para manejar la persistencia de usuarios"""
    def anadir_usuario(self, ruta, usuario, contrasena):
        "Añadimos un usuario a la ruta especificada"
        with open(ruta,"a", encoding="utf-8") as archivo:
            archivo.write("\nUser:\n")
            archivo.write("Usuario = "+usuario+"\n")
            archivo.write("Contraseña = "+contrasena+"\n")
            archivo.close()


    def comprueba_usuario(self,ruta, usuario_comprobar, contrasena_comprobar):
        """Comprobamos si un usuario y contraseñas dadas ya existen"""
        archivo = open(ruta,"r",encoding="utf-8") # pylint:disable = consider-using-with
        while True:
            linea = archivo.readline()
            if linea == "User:\n":
                usuario = archivo.readline()
                contrasena = archivo.readline()
                usuario = usuario[usuario.index("= ")+2:]
                contrasena = contrasena[contrasena.index("= ")+2:]
                if usuario_comprobar+"\n" == usuario and contrasena_comprobar+"\n" == contrasena:
                    return True
            if not linea:
                break
        archivo.close()
        return False


    def eliminar_usuario(self, ruta, usuario):
        """Eliminamos un usuario de la ruta especificada"""
        with open(ruta,"r",encoding="utf-8") as archivo:
            lineas = archivo.readlines()
            archivo.close()
        try:
            posicion = lineas.index("Usuario = "+usuario+"\n")
            with open(ruta,"w",encoding="utf-8") as archivo:
                for num_linea, linea in enumerate(lineas):
                    if num_linea not in range(posicion-2,posicion+2):
                        archivo.write(linea)
                archivo.close()
        except ValueError as exc:
            raise exc


class FileAvailabilityAnnounceI(IceFlix.FileAvailabilityAnnounce): # pylint:disable=too-few-public-methods
    """Sirviente que implementa la interfaz File Availability Announce"""
    def announceFiles(self, media_ids, service_id, current = None): # pylint:disable=unused-argument
        """Mostramos los mensajes announceFiles"""
        print(f"El servicio con ID {service_id}, ha anunciado que "
              "posee los siguientes media/s id/s\n")
        for media_id in media_ids:
            print(f"-{media_id}\n")


class CatalogUpdateI(IceFlix.CatalogUpdate):
    """Sirviente que implementa la interfaz Catalog Update"""
    def renameTile(self, media_id, new_name, service_id, current = None): # pylint:disable=unused-argument
        """Mostramos los mensajes renameTile"""
        print(f"Se ha renombrado la película {media_id} con el siguiente nombre {new_name}\n"
              f"ID del servicio al que se ha hecho la llamada: {service_id}\n")


    def addTags(self, media_id, user, tags, service_id, current = None): # pylint:disable=unused-argument, too-many-arguments
        """Mostramos los mensajes addTags"""
        print(f"El usuario {user} ha añadido la/s siguiente/s tag/s\n")
        for etiqueta in tags:
            print(f"-{etiqueta}\n")
        print(f"A la siguiente película: {media_id}\n"
              f"ID del catálogo al que se ha hecho la llamada: {service_id}\n")


    def removeTags(self, media_id, user, tags, service_id, current = None): # pylint:disable=unused-argument, too-many-arguments
        """Mostramos los mensajes removeTags"""
        print(f"El usuario {user} ha eliminado la/s siguiente/s tag/s\n")
        for etiqueta in tags:
            print(f"-{etiqueta}\n")
        print(f"De la siguiente película: {media_id}\n"
              f"ID del catálogo al que se ha hecho la llamada: {service_id}\n")

class UserUpdateI(IceFlix.UserUpdate):
    """Sirviente que implementa la interfaz User Update"""
    def newToken(self, user, token, service_id, current = None): # pylint:disable=unused-argument
        """Mostramos los mensajes newToken"""
        print(f"Se ha otorgado al usuario {user} el siguiente token {token}\n"
              f"ID del servicio que lo ha otorgado: {service_id}\n")


    def revokeToken(self, token, service_id, current = None): # pylint:disable=unused-argument
        """Mostramos los mensajes revokeToken"""
        print(f"Se ha revocado el siguiente token: {token}\n"
              f"ID del servicio que lo revoca: {service_id}\n")


    def newUser(self, user, password_hash, service_id, current = None): # pylint:disable=unused-argument
        """Mostramos los mensajes newUser"""
        print(f"Se ha registrado el usuario {user} con contraseña {password_hash}\n"
              f"ID del servicio en el que se ha registrado: {service_id}\n")


    def removeUser(self, user, service_id, current = None): # pylint:disable=unused-argument
        """Mostramos los mensajes removeUser"""
        print(f"Se ha eliminado el siguiente usuario: {user}\n"
              f"ID del servicio que lo ha eliminado: {service_id}\n")


class AnnouncementI2(IceFlix.Announcement): # pylint:disable=too-few-public-methods
    """Sirviente que implementa la interfaz Announcement para mostrar el flujo de mensajes"""
    def announce(self, service, service_id, current = None): # pylint:disable=unused-argument
        """Escuchamos todos los anunciamientos y los mostramos"""
        if service.ice_isA("::IceFlix::Main"):
            print(f"Se ha anunciado un servicio de tipo MAIN\n"
                  f"ID del servicio: {service_id}\n")
        elif service.ice_isA("::IceFlix::Authenticator"):
            print(f"Se ha anunciado un servicio de tipo AUTHENTICATOR\n"
                  f"ID del servicio: {service_id}\n")
        elif service.ice_isA("::IceFlix::MediaCatalog"):
            print(f"Se ha anunciado un servicio de tipo CATALOG\n"
                  f"ID del servicio: {service_id}\n")
        elif service.ice_isA("::IceFlix::FileService"):
            print(f"Se ha anunciado un servicio de tipo FILE SERVICE\n"
                  f"ID del servicio: {service_id}\n")

class AnnouncementI(IceFlix.Announcement): # pylint:disable=too-few-public-methods
    """Sirviente que implementa la interfaz Announcement para descubrir el main"""
    def announce(self, service, service_id, current = None): # pylint:disable=unused-argument
        """EScuchamos a que un servicio main se anuncie"""
        if service.ice.isA("::IceFlix::Main"):
            proxy = IceFlix.MainPrx.uncheckedCast(service)
            if proxy is None:
                COLA.put("Error")
            else:
                COLA.put(proxy)


class FileUploader(IceFlix.FileUploader):
    """Sirviente que implementa la interfaz File Uploader"""
    def receive(self, size, current = None): # pylint:disable=unused-argument
        """Enviamos el número de bytes que nos pidan"""
        global ARCHIVO_SUBIDA
        return ARCHIVO_SUBIDA.read(size)
    def close(self, current = None): # pylint:disable=unused-argument
        """Cerramos el envío de datos"""
        COLA.put("Hecho")


class Client(Ice.Application):
    """Clase que implementa al cliente de IceFlix"""

    def __init__(self, signalPolicy=0):
        super().__init__()
        self.servant = None
        self.proxy = None
        self.adapter = None
        self.usuario = None
        self.contrasena = None
        self.token_autenticacion = None
        self.prx_auth = None
        self.prx_catalog = None
        self.prx_file = None
        self.principal = None
        self.autenticador = None
        self.file_service = None
        self.catalogo = None
        self.peliculas = []
        self.seleccion = None
        self.admin = False

    def run(self, args):
        """Handles the IceFlix client CLI command."""

        veces_reintentado = 0
        iniciado_setup = False
        setup_logging()
        logging.info("Starting IceFlix client...")
        while veces_reintentado != REINTENTOS:
            try:
                topic_mg_proxy = self.communicator().stringToProxy(
                    "IceStorm/TopicManager:tcp -p 10000")
                topic_manager = IceStorm.TopicManagerPrx.checkedCast(topic_mg_proxy)

                comm = self.communicator()
                servant = AnnouncementI()
                self.adapter = comm.createObjectAdapter("clientAdapter")
                self.adapter.activate()
                serv_prx = self.adapter.addWithUUID(servant)

                topic_anunciamiento = topic_manager.retrieve("Announcements")
                topic_anunciamiento.subscribeAndGetPublisher({},serv_prx)
                print("Buscando servidores Main. Por favor espere...")
                msg = COLA.get(block=True)
                if msg == "Error":
                    raise IceFlix.TemporaryUnavailable
                self.principal = msg
                topic_anunciamiento.unsuscribe(serv_prx)
                self.adapter.remove(serv_prx.ice_getIdentity())

                if iniciado_setup is False:
                    propiedades = self.communicator().getProperties()
                    self.admin = propiedades.getProperty("AdminToken")
                    #Abrimos el archivo por si no estuviera creado ya
                    archivo = open("usuarios.txt","a",encoding="utf-8") # pylint:disable = consider-using-with
                    archivo.close()
                    iniciado_setup = True
                self.menu()
                break
            except IceStorm.NoSuchTopic:
                print("No se ha podido conseguir el topic. Reintentando")
                time.sleep(5)
                veces_reintentado += 1
            except IceFlix.TemporaryUnavailable:
                print("No se ha podido conseguir el topic manager. Reintentando")
                time.sleep(5)
                veces_reintentado += 1
                #Consultar issues para el tema 01 #Pylint error no-members
            except Ice.ConnectionRefusedException:
                print("No se ha podido conectar")
                time.sleep(5)
                veces_reintentado += 1
            except AttributeError:
                while 1:
                    try:
                        opcion = int(input("Se ha perdido la conexión con el servidor principal.\n"
                              "¿Desea reintentar conectarse(0) o salir del programa(1)\n"))
                        while opcion not in (0,1):
                            opcion = int(input("Por favor escoja una opción válida\n"))
                        if opcion == 0:
                            self.adapter.destroy()
                            veces_reintentado = 0
                            break
                        veces_reintentado = 3
                        break
                    except ValueError:
                        print("Introduzca un valor válido")

        print("Hasta la próxima :)")
        if veces_reintentado == REINTENTOS:
            print("No se ha podido establecer la conexión"
                  " con el servidor")
            return 0
        return 0


    def menu(self):
        """Muestra un menú al usuario"""
        while True:
            try:
                if not self.token_autenticacion:
                    opcion = int(input("CONEXIÓN ESTABLECIDA. ESTADO: NO AUTENTICADO. \n"
                                   "Elija qué desea hacer:\n"
                                   "1. Iniciar sesión en el sistema.\n"
                                   "2. Buscar en el catálogo por nombre\n"
                                   "3. Cambiar credenciales\n"
                                   "4. Salir del programa\n"))

                    if opcion == 1:
                        self.conseguir_token()
                    elif opcion == 2:
                        self.buscar_pelis_nombre()
                    elif opcion == 3:
                        self.cambiar_credenciales()
                    elif opcion == 4:
                        break

                else:
                    estado = "CONEXIÓN ESTABLECIDA. ESTADO: AUTENTICADO. \n"
                    if not self.seleccion:
                        estado += "Película seleccionada: Ninguna\n"
                    else:
                        estado += "Película seleccionada: "+self.seleccion.info.name+"\n"
                    opcion = int(input(estado+
                                       "Elija qué desea hacer:\n"
                                       "1. Renovar su sesión.\n"
                                       "2. Buscar en el catálogo por nombre.\n"
                                       "3. Buscar en el catálogo por tags.\n"
                                       "4. Seleccionar una película.\n"
                                       "5. Ver películas que he buscado.\n"
                                       "6. Añadir tags a una película\n"
                                       "7. Eliminar tags de una película\n"
                                         "8. Descargar una película\n"
                                       "9. Abrir menú de aministrador\n"
                                       "10. Cerrar sesión\n"))

                    if opcion == 1:
                        self.conseguir_token()
                    elif opcion == 2:
                        self.buscar_pelis_nombre()
                    elif opcion == 3:
                        self.buscar_pelis_tags()
                    elif opcion == 4:
                        self.selecciona_pelicula()
                    elif opcion == 5:
                        self.mostrar_peliculas()
                    elif opcion == 6:
                        self.anadir_tags()
                    elif opcion == 7:
                        self.eliminar_tags()
                    elif opcion == 8:
                        self.descargar_pelicula()
                    elif opcion == 9:
                        self.menu_admin(estado)
                    elif opcion == 10:
                        self.token_autenticacion = None
            except ValueError:
                print("Por favor introduzca un valor válido\n")
            except AttributeError as exc:
                raise exc


    def menu_admin(self,estado):
        """Menú del administrador"""
        while True:
            try:
                opcion = int(input(estado+
                                   "Elija qué desea hacer\n"
                                   "1. Cambiar el título de la película seleccionada\n"
                                   "2. Añadir usuarios\n"
                                   "3. Eliminar usuarios\n"
                                   "4. Eliminar una película\n"
                                   "5. Subir una película\n"
                                   "6. Monitorizar el canal UserUpdates"
                                   "7. Monitorizar el canal CatalogUpdates"
                                   "8. Monitorizar el canal FileAvailabilityAnnounce"
                                   "9. Monitorizar el canal Announcements"
                                   "10. Salir del menú de administrador\n"))
                if opcion == 1:
                    self.renombra_peli()
                elif opcion == 2:
                    self.anadir_usuario()
                elif opcion == 3:
                    self.eliminar_usuario()
                elif opcion == 4:
                    self.eliminar_pelicula()
                elif opcion == 5:
                    self.subir_pelicula()
                elif opcion == 6:
                    self.monitorizar_user_updates()
                elif opcion == 7:
                    self.monitorizar_catalog_updates()
                elif opcion == 8:
                    self.monitorizar_file_updates()
                elif opcion == 9:
                    self.monitorizar_announcements()
                elif opcion == 10:
                    break

            except ValueError:
                print("Por favor, introduzca un valor válido")
            except AttributeError as exc:
                raise exc


    def monitorizar_announcements(self):
        """Monitorizamos el canal announcements"""
        try:
            topic_mg_proxy = self.communicator().stringToProxy(
                    "IceStorm/TopicManager:tcp -p 10000")
            topic_manager = IceStorm.TopicManagerPrx.checkedCast(topic_mg_proxy)
            print("Mostrando flujo de mensajes de Announcements...\n")
            comm = self.communicator()
            servant = AnnouncementI2()
            self.adapter = comm.createObjectAdapter("clientAdapter")
            self.adapter.activate()
            serv_prx = self.adapter.addWithUUID(servant)

            topic_file = topic_manager.retrieve("Announcements")
            topic_file.subscribeAndGetPublisher({},serv_prx)

            while input("Para dejar de escuchar pulsa 'Q'") != "Q":
                pass
            topic_file.unsuscribe(serv_prx)
            self.adapter.remove(serv_prx.ice_getIdentity())
            self.adapter.destroy()
        except IceStorm.NoSuchTopic:
            print("No se ha encontrado el canal Announcements\n")


    def monitorizar_file_updates(self):
        """Monitorizamos el canal file availability announces"""
        try:
            topic_mg_proxy = self.communicator().stringToProxy(
                    "IceStorm/TopicManager:tcp -p 10000")
            topic_manager = IceStorm.TopicManagerPrx.checkedCast(topic_mg_proxy)
            print("Mostrando flujo de mensajes de FileAvailabilityAnnounces...\n")
            comm = self.communicator()
            servant = FileAvailabilityAnnounceI()
            self.adapter = comm.createObjectAdapter("clientAdapter")
            self.adapter.activate()
            serv_prx = self.adapter.addWithUUID(servant)

            topic_file = topic_manager.retrieve("FileAvailabilityAnnounces")
            topic_file.subscribeAndGetPublisher({},serv_prx)

            while input("Para dejar de escuchar pulsa 'Q'") != "Q":
                pass
            topic_file.unsuscribe(serv_prx)
            self.adapter.remove(serv_prx.ice_getIdentity())
            self.adapter.destroy()
        except IceStorm.NoSuchTopic:
            print("No se ha encontrado el canal FileAvailabilityAnnounce\n")


    def monitorizar_catalog_updates(self):
        """Monitorizamos el canal catalog updates"""
        try:
            topic_mg_proxy = self.communicator().stringToProxy(
                    "IceStorm/TopicManager:tcp -p 10000")
            topic_manager = IceStorm.TopicManagerPrx.checkedCast(topic_mg_proxy)
            print("Mostrando flujo de mensajes de Catalog Updates...\n")
            comm = self.communicator()
            servant = CatalogUpdateI()
            self.adapter = comm.createObjectAdapter("clientAdapter")
            self.adapter.activate()
            serv_prx = self.adapter.addWithUUID(servant)

            topic_cat = topic_manager.retrieve("CatalogUpdates")
            topic_cat.subscribeAndGetPublisher({},serv_prx)

            while input("Para dejar de escuchar pulsa 'Q'") != "Q":
                pass
            topic_cat.unsuscribe(serv_prx)
            self.adapter.remove(serv_prx.ice_getIdentity())
            self.adapter.destroy()
        except IceStorm.NoSuchTopic:
            print("No se ha encontrado el canal CatalogUpdates\n")


    def monitorizar_user_updates(self):
        """Monitorizamos el canal user updates"""
        try:
            topic_mg_proxy = self.communicator().stringToProxy(
                    "IceStorm/TopicManager:tcp -p 10000")
            topic_manager = IceStorm.TopicManagerPrx.checkedCast(topic_mg_proxy)
            print("Mostrando flujo de mensajes de User Updates...\n")
            comm = self.communicator()
            servant = UserUpdateI()
            self.adapter = comm.createObjectAdapter("clientAdapter")
            self.adapter.activate()
            serv_prx = self.adapter.addWithUUID(servant)

            topic_auth = topic_manager.retrieve("UserUpdates")
            topic_auth.subscribeAndGetPublisher({},serv_prx)

            while input("Para dejar de escuchar pulsa 'Q'") != "Q":
                pass
            topic_auth.unsuscribe(serv_prx)
            self.adapter.remove(serv_prx.ice_getIdentity())
            self.adapter.destroy()
        except IceStorm.NoSuchTopic:
            print("No se ha encontrado el canal UserUpdate\n")


    def subir_pelicula(self):
        """Subimos una película al servidor"""
        ruta = input("Introduzca la ruta ABSOLUTA de la película que desea subir\n")
        try:
            if os.path.isfile(ruta) is False:
                print("La ruta introducida es errónea, por favor, inténtelo de nuevo\n")
            else:
                global ARCHIVO_SUBIDA
                self.comprueba_proxy_file_service()
                with open(ruta, "rb") as ARCHIVO_SUBIDA:
                    self.servant = FileUploader()
                    print("Subiendo su película, espere por favor...\n")
                    self.inicia_file_uploader()
                    ARCHIVO_SUBIDA.close()
                    print("El archivo se ha subido correctamente\n")
        except AttributeError as exc:
            raise exc
        except IceFlix.Unauthorized:
            print("Carece de los permisos para realizar esta opción, por favor contacte"
                  " con el administrador\n")
        except IceFlix.TemporaryUnavailable:
            print("No se ha podido subir la película, inténtelo más tarde\n")

    def inicia_file_uploader(self):
        """Iniciamos el servidor del file_uploader"""
        comm = self.communicator()
        self.adapter = comm.createObjectAdapter("clientAdapter")
        self.adapter.activate()

        self.proxy = self.adapter.addWithUUID(self.servant)
        self.proxy = IceFlix.FileUploaderPrx.uncheckedCast(self.proxy)
        try:
            self.file_service.uploadFile(self.proxy,self.admin)
            COLA.get(block=True)
            self.adapter.remove(self.proxy.ice_getIdentity())
            self.adapter.destroy()
        except IceFlix.Unauthorized as exc:
            self.adapter.remove(self.proxy.ice_getIdentity())
            raise exc


    def descargar_pelicula(self):
        """Descargamos la película seleccionada"""
        if not self.seleccion:
            print("No tiene ninguna película seleccionada.\n"
                  "Para descargar una, selecciónela primero\n")
        elif self.seleccion.provider is None:
            print("No se puede descargar la película elegida\n")
        else:
            num_reintentos = 0
            while num_reintentos < REINTENTOS:
                try:
                    self.comprueba_proxy_autenticador()
                    self.file_service = self.seleccion.provider
                    file_handler = self.file_service.openFile(self.seleccion.mediaId,
                                                              self.token_autenticacion)

                    archivo = open("./archivos/"+self.seleccion.info.name, # pylint:disable = consider-using-with
                                   "ab+")
                    break
                except FileNotFoundError:
                    print(f"No se encontró la ruta /archivos/{self.seleccion.info.name}")
                    break
                except AttributeError as exc:
                    raise exc
                except IceFlix.WrongMediaId:
                    print("Hay un error con el identificador de la película, por favor,"
                          " contacte con la empresa\n")
                    num_reintentos = 3
                    break
                except IceFlix.TemporaryUnavailable:
                    print("No se ha podido descargar su película, inténtelo más tarde\n")
                    num_reintentos = 3
                    break
                except IceFlix.Unauthorized:
                    self.token_autenticacion = self.autenticador.refreshAuthorization(self.usuario,
                                                                                    self.contrasena)
                    num_reintentos += 1
                    time.sleep(1)
            if num_reintentos == REINTENTOS:
                print("No se ha podido establecer la conexion\n")
                self.token_autenticacion = None
                return None
            num_reintentos = 0
            print("Descargando su película... Espere por favor\n")
            while True:
                try:
                    contenido = file_handler.receive(100,self.token_autenticacion)
                    if not contenido:
                        file_handler.close(self.token_autenticacion)
                        break
                    archivo.write(contenido)
                except IceFlix.Unauthorized:
                    self.token_autenticacion = self.autenticador.refreshAuthorization(self.usuario,
                                                                                    self.contrasena)
            archivo.close()
            print("Su archivo se ha descargado en el direcotio archivos\n")


    def eliminar_pelicula(self):
        """El administrador elimina la película seleccionada"""
        if not self.seleccion:
            print("Por favor, seleccione una película primero\n")
        elif self.seleccion is None:
            print("No se puede eliminar la película\n")
        else:
            try:
                self.file_service = self.seleccion.provider
                self.file_service.removeFile(self.seleccion.mediaId,self.admin)
            except IceFlix.TemporaryUnavailable:
                print("El servicio se encuentra temporalmente fuera de servicio.\n"
                      "Por favor, inténtelo de nuevo más tarde\n")
            except IceFlix.Unauthorized:
                print("Carece de los permisos para realizar esta acción\n")
            except IceFlix.WrongMediaId:
                print("Hay un error con el identificador de la película, por favor,"
                      " contacte con la empresa\n")
            except Ice.ConnectTimeoutException:
                print("Servicio de ficheros no disponible\n")

    def eliminar_usuario(self):
        """Eliminamos un usuario"""
        try:
            self.comprueba_proxy_autenticador()
            usuario = input("Introduzca el nombre de usuario a eliminar\n")
            if usuario == self.usuario:
                print("No puedes eliminarte a ti mismo\n")
            else:
                self.autenticador.removeUser(usuario, self.admin)
                manejador = ManejadorUsuarios()
                manejador.eliminar_usuario("usuarios.txt",usuario)
                print("Usuario eliminado correctamente\n")

        except IceFlix.TemporaryUnavailable:
            print("No se puede añadir el usuario ahora mismo, inténtelo más tarden\n")
        except AttributeError as exc:
            raise exc
        except IceFlix.Unauthorized:
            print("Carece de los permisos para realizar esta acción\n")
        except Ice.ConnectTimeoutException:
            print("AUtenticador no disponible\n")
        except ValueError:
            print(f"El usuario {usuario} no existe\n")


    def anadir_usuario(self):
        """Añadimos un usuario"""
        try:
            self.comprueba_proxy_autenticador()
            usuario = input("Introduzca el nombre de usuario\n")
            contrasena = hashlib.sha256(getpass.getpass("Introduzca "
                                                        "la contraseña\n").encode()).hexdigest()
            manejador = ManejadorUsuarios()
            #Comprobamos que el usuario no exista ya en el archivo de usuarios
            #De ser así no tendría sentido añadir un usuario igual a otro que ya hay
            #Y no enviaremos información redundante al autenticador
            if manejador.comprueba_usuario("usuarios.txt",usuario,contrasena) is False:
                self.autenticador.addUser(usuario, contrasena, self.admin)
                manejador.anadir_usuario("usuarios.txt",usuario,contrasena)
            print("Usuario añadido correctamente\n")

        except IceFlix.TemporaryUnavailable:
            print("No se puede añadir el usuario ahora mismo, inténtelo más tarden\n")
        except AttributeError as exc:
            raise exc
        except IceFlix.Unauthorized:
            print("Carece de los permisos para realizar esta acción\n")
        except Ice.ConnectTimeoutException:
            print("Autenticador no disponible\n")


    def renombra_peli(self):
        """Cambiamos el nombre a la película seleccionada"""
        if not self.seleccion:
            print("POr favor seleccione la película que desea renombrar")
        else:
            try:
                self.comprueba_proxy_catalogo()
                nuevo_nombre = input("Introduzca el nuevo título que deseas para "+
                                     self.seleccion.info.name+"\n")
                self.catalogo.renameTile(self.seleccion.mediaId,nuevo_nombre,self.admin)
                self.seleccion.info.name = nuevo_nombre

            except AttributeError as exc:
                raise exc
            except IceFlix.TemporaryUnavailable:
                print("El catálogo no se encuantra actualmente disponible, pruebe más tarde\n")
            except IceFlix.Unauthorized:
                print("Ha habido un error al ejecutar la opción administrativa. Por favor "
                      "póngase en contacto con su administrador\n")
            except IceFlix.WrongMediaId:
                print("Ha habido un error al añadir los tags a la película seleccionada.\n"
                      "Por favor, inténtelo con otra película\n")
            except Ice.ConnectTimeoutException:
                print("Catálogo no disponible\n")


    def anadir_tags(self):
        #TRY-EXCEPT
        """Añadimos tags a la película seleccionada"""
        if not self.seleccion:
            print("Por favor seleccione una película antes de añadir tags\n")
        else:
            tags = []
            try:
                self.comprueba_proxy_catalogo()
                tags.append(input("Introduce la etiqueta que deseas añadir a la película "+
                                       self.seleccion.info.name+"\n"))

                while input("¿Desea añadir más etiquetas? (S/N)\n").capitalize() == "S":
                    tags.append(input("Introduzca la etiqueta\n"))
                num_reintentos = 0
            except AttributeError as exc:
                raise exc
            except IceFlix.TemporaryUnavailable:
                print("El catálogo no se encuentra actualmente disponible, pruebe más tarde\n")
                num_reintentos = 3

            while num_reintentos < REINTENTOS:
                try:
                    self.comprueba_proxy_autenticador()
                    self.catalogo.addTags(self.seleccion.mediaId,tags,self.token_autenticacion)
                    print("Las etiquetas se han añadido correctamente\n")
                    break
                except IceFlix.Unauthorized:
                    self.token_autenticacion = self.autenticador.refreshAuthorization(self.usuario,
                                                                                    self.contrasena)
                    num_reintentos += 1
                    time.sleep(1)
                except AttributeError as exc:
                    raise exc
                except IceFlix.TemporaryUnavailable:
                    print("Ha ocurrido un error, por favor trate de iniciar sesión de nuevo\n")
                    self.token_autenticacion = None
                    break
                except IceFlix.WrongMediaId:
                    print("Ha habido un error al añadir los tags a la película seleccionada.\n"
                          "Por favor, inténtelo con otra película\n")
                    break
                except Ice.ConnectTimeoutException:
                    print("NO se ha podido conectar con el catálogo\n")
                    break
            if num_reintentos == REINTENTOS:
                print("No se han podido añadir los tags\n")



    def eliminar_tags(self):
        #TRY-EXCEPT
        """Eliminamos tags de la película seleccionada"""
        if not self.seleccion:
            print("Por favor seleccione una película antes de eliminar tags\n")
        else:
            tags = []
            try:
                self.comprueba_proxy_catalogo()
                tags.append(input("Introduce la etiqueta que deseas eliminar de la película "+
                                       self.seleccion.info.name+"\n"))

                while input("¿Desea añadir más etiquetas a eliminar? (S/N)\n").capitalize() == "S":
                    tags.append(input("Introduzca la etiqueta\n"))
                num_reintentos = 0
            except AttributeError as exc:
                raise exc
            except IceFlix.TemporaryUnavailable:
                print("El catálogo no se encuantra actualmente disponible, pruebe más tarde\n")
                num_reintentos = 3

            while num_reintentos < REINTENTOS:
                try:
                    self.comprueba_proxy_autenticador()
                    self.catalogo.removeTags(self.seleccion.mediaId,tags,self.token_autenticacion)
                    print("Las etiquetas se han eliminado correctamente\n")
                    break
                except IceFlix.Unauthorized:
                    self.token_autenticacion = self.autenticador.refreshAuthorization(self.usuario,
                                                                                    self.contrasena)
                    num_reintentos+=1
                    time.sleep(1)
                except AttributeError as exc:
                    raise exc
                except IceFlix.WrongMediaId:
                    print("Ha habido un error al eliminar los tags a la película seleccionada.\n"
                          "Por favor, inténtelo con otra película\n")
                    break
                except IceFlix.TemporaryUnavailable:
                    print("Ha ocurrido un error, por favor trate de iniciar sesión de nuevo\n")
                    self.token_autenticacion = None
                    break
                except Ice.ConnectTimeoutException:
                    print("No se ha podido conectar al catálogo\n")
                    break
            if num_reintentos == REINTENTOS:
                print("No se han podido eliminar los tags\n")


    def selecciona_pelicula(self):
        """Seleccionamos una película de una búsqueda"""
        seleccion = None

        if len(self.peliculas) == 0:
            print("Por favor busque películas antes de seleccionar alguna\n.")
        else:
            while seleccion not in range(1,len(self.peliculas)+1):
                try:
                    self.mostrar_peliculas()
                    seleccion = int(input("Introduzca el número de la película que "
                                    "desea seleccionar\n"))
                except ValueError:
                    print("Por favor, introduzca un valor válido\n")
            self.seleccion = self.peliculas[seleccion-1]


    def buscar_pelis_tags(self):
        #TRY-EXCEPT
        """Buscamos en el catálogo películas por tags"""
        try:
            self.comprueba_proxy_catalogo()
            tags = []
            tags.append(input("Introduzca la etiqueta por la que desea buscar\n"))
            while input("¿Desea añadir más etiquetas? (S/N)\n").capitalize() == "S":
                tags.append(input("Introduzca otra etiqueta por la que desea buscar\n"))

            opcion = int(input("¿Desea buscar películas que contengan alguna de las etiquetas (0)"
                               " o buscar películas que contengan todas las etiquetas (1)\n"))
            while opcion not in (0,1):
                opcion = int(input("Por favor, escoja una opción válida\n"))
            num_reintentos = 0
        except AttributeError as exc:
            raise exc
        except IceFlix.TemporaryUnavailable:
            print("El servicio se encuentra temporalmente fuera de servicio, "
                  "por favor, inténtelo más tarde\n")
            num_reintentos = 3

        while num_reintentos < REINTENTOS:
            try:
                self.comprueba_proxy_autenticador()
                if opcion == 0:
                    self.peliculas = self.catalogo.getTilesByTags(tags,False,
                                                                self.token_autenticacion)
                else:
                    self.peliculas = self.catalogo.getTilesByTags(tags,True,
                                                                self.token_autenticacion)

                self.muestra_pelis_busqueda(1)
                break
            except IceFlix.Unauthorized:
                self.token_autenticacion = self.autenticador.refreshAuthorization(self.usuario,
                                                                                self.contrasena)
                num_reintentos += 1
                time.sleep(1)
            except AttributeError as exc:
                raise exc
            except IceFlix.WrongMediaId:
                print("Ha habido un eror al procesar los títulos\n")
                break
            except IceFlix.TemporaryUnavailable:
                print("Ha ocurrido un error, por favor trate de iniciar sesión de nuevo\n")
                self.token_autenticacion = None
                break
            except Ice.ConnectTimeoutException:
                print("No está disponible el catálogo\n")
                break


    def buscar_pelis_nombre(self):
        #TRY-EXCEPT
        """Buscamos en el catálogo películas por nombre"""
        try:
            self.comprueba_proxy_catalogo()
            cadena = input("Introduzca el nombre de la película"
                        " que desea buscar\n")
            opcion = int(input("¿Desea buscar por el título exacto que ha introducido (0)"
                            " o buscar todas las películas que contengan ese título? (1)\n"))
            while opcion not in (0, 1):
                opcion = int(input("Por favor, escoja una opción válida\n"))
            num_reintentos = 0

        except AttributeError as exc:
            raise exc
        except IceFlix.TemporaryUnavailable:
            print("El servicio se encuentra temporalmente fuera de servicio, "
                "por favor, inténtelo más tarde\n")
            num_reintentos = 3

        while num_reintentos < REINTENTOS:
            try:
                if opcion == 0:
                    self.peliculas = self.catalogo.getTilesByName(cadena, True)
                else:
                    self.peliculas = self.catalogo.getTilesByName(cadena, False)

                if not self.token_autenticacion:
                    self.muestra_pelis_busqueda(0)
                    self.peliculas = []
                else:
                    self.muestra_pelis_busqueda(1)
                break
            except IceFlix.Unauthorized:
                self.token_autenticacion = self.autenticador.refreshAuthorization(self.usuario,
                                                                                self.contrasena)
                num_reintentos += 1
                time.sleep(1)
            except IceFlix.WrongMediaId:
                print("Ha habido un eror al procesar los títulos\n")
                break
            except IceFlix.TemporaryUnavailable:
                print("Ha ocurrido un error, por favor trate de iniciar sesión de nuevo\n")
                self.token_autenticacion = None
                break
            except Ice.ConnectTimeoutException:
                print("No está disponible el catálogo\n")
                break

    def muestra_pelis_busqueda(self,autenticado):
        #TRY-EXCEPT
        """Mostramos las películas que se han obtenido de una búsqueda.
        Diferente si el usuario está autenticado en el sistema o no"""

        i = 1
        if len(self.peliculas) == 0:
            print("No se han obtenido resultados para su búsqueda.\n")
            self.seleccion = None
        elif autenticado == 0:
            for pelicula in self.peliculas:
                print(i,":",pelicula)
                i += 1
            print("Para ver más información de las películas inicie sesión\n")
        else:
            num_reintentos = 0
            while num_reintentos < REINTENTOS:
                try:
                    listado = []

                    for pelicula in self.peliculas:
                        media = self.catalogo.getTile(pelicula,self.token_autenticacion)
                        print(i,": ",media.info.name, " [",media.info.tags,"]")
                        listado.append(media)
                        i += 1

                    self.peliculas = listado.copy()
                    break

                except IceFlix.Unauthorized:
                    self.token_autenticacion = self.autenticador.refreshAuthorization(self.usuario,
                                                                                    self.contrasena)
                    num_reintentos += 1
                    time.sleep(1)
                except IceFlix.WrongMediaId as exc:
                    raise exc
                except IceFlix.TemporaryUnavailable as exc:
                    raise exc
                except Ice.ConnectTimeoutException as exc:
                    raise exc

    def mostrar_peliculas(self):
        """Mostramos las películas almacenadas en memoria"""
        i = 0
        if len(self.peliculas)==0:
            print("No has realziado ninguna búsqueda de películas")

        else:
            for pelicula in self.peliculas:
                print((i+1),": ",pelicula.info.name, " [",pelicula.info.tags,"]")
                i += 1


    def cambiar_credenciales(self):
        """Cambia las credenciales del usuario por otras"""
        try:
            user = self.usuario
            manejador = ManejadorUsuarios()
            self.comprueba_proxy_autenticador()
            usuario = input("Introduzca su nuevo nombre de usuario\n")
            contrasena = hashlib.sha256(getpass.getpass("Introduzca "
                                                        "la contraseña\n").encode()).hexdigest()
            self.autenticador.addUser(usuario, contrasena, self.admin)
            self.autenticador.removeUser(self.usuario,self.admin)
            self.usuario = usuario
            self.contrasena = contrasena
            print("Usuario cambiado correctamente")
            manejador.anadir_usuario("usuarios.txt",self.usuario,self.contrasena)
            manejador.eliminar_usuario("usuarios.txt",user)

        except IceFlix.TemporaryUnavailable:
            print("No se puede cambiar su usuario ahora mismo, inténtelo más tarden\n")
        except AttributeError as exc:
            raise exc
        except IceFlix.Unauthorized:
            print("Carece de los permisos para realizar esta acción\n")
        except Ice.ConnectTimeoutException:
            print("No se ha podido conectar con el autenticador\n")
        except Ice.ConnectFailedException:
            print("No se ha podido conectar con el autenticador\n")


    def conseguir_token(self):
        """Pedimos el token al authenticator"""
        try:
            self.comprueba_proxy_autenticador()
            if not self.usuario:
                print("Vamos a crear un usuario\n")
                user = input("Introduce un nombre de usuario\n")
                password = hashlib.sha256(getpass.getpass("Introduzca "
                                                        "la contraseña\n").encode()).hexdigest()
                self.usuario = user
                self.contrasena = password
                manejador = ManejadorUsuarios()
                if manejador.comprueba_usuario("usuarios.txt",user,password) is False:
                    manejador.anadir_usuario("usuarios.txt",self.usuario,self.contrasena)
                    self.autenticador.addUser(user,password,self.admin)

            self.token_autenticacion = self.autenticador.refreshAuthorization(self.usuario,
                                                                              self.contrasena)
            print("Token obtenido correctamente\n")

        except IceFlix.Unauthorized:
            print("Error intentando conseguir el token de autenticación\n")
            self.token_autenticacion = None
        except AttributeError as exc:
            raise exc
        except IceFlix.TemporaryUnavailable:
            print("No se ha podido conseguir el token porque está desconectado\n")
        except Ice.ConnectTimeoutException:
            print("NO se ha podido conectar con el autenticador\n")


    def comprueba_proxy_autenticador(self):
        """Comprobamos si tenemos el proy del autenticador"""
        try:
            auth = self.principal.getAuthenticator()
            auth = self.conexion_autenticador(auth)
            if not auth:
                raise IceFlix.TemporaryUnavailable
            if auth != self.autenticador:
                self.autenticador = auth

        except IceFlix.TemporaryUnavailable as exc:
            raise exc
        except AttributeError as exc:
            raise exc


    def comprueba_proxy_file_service(self):
        """Comprobamos el proxy del file service"""
        try:
            file_service = self.principal.getFileService()
            file_service = self.conexion_file_service(file_service)
            if not file_service:
                raise IceFlix.TemporaryUnavailable
            if file_service != self.file_service:
                self.file_service = file_service


        except IceFlix.TemporaryUnavailable as exc:
            print("El servidor de archivos está temporalmente fuera de servicio"
                  " inténtelo de nuevo más tarde")
            raise exc
        except AttributeError as exc:
            raise exc


    def comprueba_proxy_catalogo(self):
        """Comprobamos si tenemos el proy del catálogo"""
        try:
            catalog = self.principal.getCatalog()
            catalog = self.conexion_catalogo(catalog)
            if not catalog:
                raise IceFlix.TemporaryUnavailable
            if catalog != self.catalogo:
                self.catalogo = catalog


        except IceFlix.TemporaryUnavailable as exc:
            print("El catálogo está temporalmente fuera de servicio"
                  " inténtelo de nuevo más tarde")
            raise exc
        except AttributeError as exc:
            raise exc


    def conexion_catalogo(self,catalog):
        """Creamos una conexión con el autenticador"""
        return IceFlix.MediaCatalogPrx.checkedCast(catalog)


    def conexion_file_service(self,file_service):
        """Creamos una conexión con el file service"""
        return IceFlix.FileServicePrx.checkedCast(file_service)


    def conexion_autenticador(self,autenticador):
        """Creamos una conexión con el autenticador"""
        return IceFlix.AuthenticatorPrx.checkedCast(autenticador)


if __name__ == "__main__":
    sys.exit(Client().main(sys.argv))
