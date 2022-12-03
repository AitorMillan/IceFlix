"""Modulo del cliente de IceFlix"""

import sys
import logging
import time
import hashlib
import getpass
from queue import Queue
import os.path
import Ice
import IceFlix # pylint:disable=import-error
from IceFlix import Media # pylint:disable=unused-import,import-error
from IceFlix import MediaInfo # pylint:disable=unused-import,import-error




LOG_FORMAT = '%(asctime)s - %(levelname)-7s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'

COLA = Queue()
REINTENTOS = 3
ARCHIVO = None

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
        except ValueError:
            print(f"El usuario {usuario} no se encuentra registrado")


class FileUploader(IceFlix.FileUploader):
    """Sirviente que implementa la interfaz File Uploader"""
    def receive(self, size, current = None): # pylint:disable=unused-argument
        pass
    def close(self, current = None): # pylint:disable=unused-argument
        COLA.put("Hecho")


class UploaderApp(Ice.Application):
    """Clase encargada de hacer de servidor del File Uploader"""
    def __init__(self, file_service, admin_token):
        super().__init__()
        self.servant = FileUploader()
        self.proxy = None
        self.adapter = None
        self.file_service = file_service
        self.admin_token = admin_token


    def run(self,args):
        """Ejecuta el Uploader"""
        comm = self.communicator()
        self.adapter = comm.createObjectAdapter("clientAdapter")
        self.adapter.activate()

        self.proxy = self.adapter.addWithUUID(self.servant)
        self.proxy = IceFlix.FileUploaderPrx.uncheckedCast(self.proxy)
        try:
            self.file_service.uploadFile(self.proxy,self.admin_token)
            COLA.get(block=True)
        except IceFlix.Unauthorized as exc:
            raise exc


class Client(Ice.Application):
    """Clase que implementa al cliente de IceFlix"""

    def __init__(self, signalPolicy=0):
        super().__init__()
        self.usuario = "user"
        self.contrasena = hashlib.sha256("pass".encode()).hexdigest()
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
        setup_logging()
        logging.info("Starting IceFlix client...")
        if len(args) <= 1:
            print("No ha introducido ningún fichero de configuracón\n"
                "Puede continuar usando la aplicación con normalidad, pero no"
                " podrá subir películas como administrador\n")
            if input("¿Desea continuar? (S/N)\n") == "N":
                veces_reintentado = 3
        while veces_reintentado != REINTENTOS:
            try:
                prx_main = self.communicator().stringToProxy(args[1])


                self.principal = IceFlix.MainPrx.checkedCast(prx_main)

                if not self.principal:
                    raise IceFlix.TemporaryUnavailable
                break
            except IceFlix.TemporaryUnavailable:
                print("Servicio no disponible. Reintentando...")
                time.sleep(5)
                veces_reintentado += 1
                #Consultar issues para el tema 01 #Pylint error no-members
            except Ice.ConnectionRefusedException:
                print("No se ha podido conectar")
                time.sleep(5)
                veces_reintentado += 1

        if veces_reintentado == REINTENTOS:
            print("No se ha podido establecer la conexión"
                  " con el servidor")
            return 0

        self.menu()
        print("Hasta la próxima :)")
        return 0


    def menu(self):
        """Muestra un menú al usuario"""
        while True:
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
                    estado += "Película seleccionada: ",self.seleccion.info.name,"\n"
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
                                   "6. Salir del menú de administrador\n"))
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
                    break

            except ValueError:
                print("Por favor, introduzca un valor válido")


    def subir_pelicula(self):
        """Subimos una película al servidor"""
        ruta = input("Introduzca la ruta ABSOLUTA de la película que desea subir\n")
        try:
            if os.path.isfile(ruta) is False:
                print("La ruta introducida es errónea, por favor, inténtelo de nuevo\n")
            else:
                ARCHIVO = open(ruta,"r",encoding="utf-8")
                server = UploaderApp(self.file_service,"1234")
                server.main(sys.argv)
                ARCHIVO.close()
                print("El archivo se ha subido correctamente\n")
        except FileNotFoundError:
            print("La ruta introducida es errónea, por favor, inténtelo de nuevo\n")


    def descargar_pelicula(self):
        if not self.seleccion:
            print("No tiene ninguna película seleccionada.\n"
                  "Para descargar una, selecciónela primero\n")
        else:
            pass


    def eliminar_pelicula(self):
        """El administrador elimina la película seleccionada"""
        pass


    def eliminar_usuario(self):
        """Eliminamos un usuario"""
        try:
            self.comprueba_proxy_autenticador()
            usuario = input("Introduzca el nombre de usuario a eliminar\n")
            self.autenticador.removeUser(usuario, "1234")
            print("Usuario eliminado correctamente\n")
            manejador = ManejadorUsuarios()
            manejador.eliminar_usuario("usuarios.txt",usuario)

        except IceFlix.TemporaryUnavailable:
            print("No se puede añadir el usuario ahora mismo, inténtelo más tarden\n")
        except IceFlix.Unauthorized:
            print("Carece de los permisos para realizar esta acción\n")


    def anadir_usuario(self):
        """Añadimos un usuario"""
        try:
            self.comprueba_proxy_autenticador()
            usuario = input("Introduzca el nombre de usuario\n")
            contrasena = hashlib.sha256(getpass.getpass("Introduzca "
                                                        "la contraseña\n").encode()).hexdigest()
            self.autenticador.addUser(usuario, contrasena, "1234")
            print("Usuario añadido correctamente\n")
            manejador = ManejadorUsuarios()
            manejador.anadir_usuario("usuarios.txt",usuario,contrasena)

        except IceFlix.TemporaryUnavailable:
            print("No se puede eliminar el usuario ahora mismo, inténtelo más tarden\n")
        except IceFlix.Unauthorized:
            print("Carece de los permisos para realizar esta acción\n")


    def renombra_peli(self):
        """Cambiamos el nombre a la película seleccionada"""
        if not self.seleccion:
            print("POr favor seleccione la película que desea renombrar")
        else:
            try:
                self.comprueba_proxy_catalogo()
                nuevo_nombre = input("Introduzca el nuevo título que deseas para ",
                                     self.seleccion.info.name,"\n")
                self.catalogo.renameTile(self.seleccion.mediaId,nuevo_nombre,"1234")

            except IceFlix.TemporaryUnavailable:
                print("El catálogo no se encuantra actualmente disponible, pruebe más tarde\n")
            except IceFlix.Unauthorized:
                print("Ha habido un error al ejecutar la opción administrativa. Por favor "
                      "póngase en contacto con su administrador\n")
            except IceFlix.WrongMediaId:
                print("Ha habido un error al añadir los tags a la película seleccionada.\n"
                      "Por favor, inténtelo con otra película\n")


    def anadir_tags(self):
        #TRY-EXCEPT
        """Añadimos tags a la película seleccionada"""
        if not self.seleccion:
            print("Por favor seleccione una película antes de añadir tags\n")
        else:
            tags = []
            try:
                self.comprueba_proxy_catalogo()
                tags.append(input("Introduce la etiqueta que deseas añadir a la película ",
                                       self.seleccion.info.name,"\n"))

                while input("¿Desea añadir más etiquetas? (S/N)\n").capitalize() == "S":
                    tags.append(input("Introduzca la etiqueta\n"))
                num_reintentos = 0
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
                    self.autenticador.refreshAuthorization(self.usuario,self.contrasena)
                    num_reintentos += 1
                except IceFlix.TemporaryUnavailable:
                    print("Ha ocurrido un error, por favor trate de iniciar sesión de nuevo\n")
                    self.token_autenticacion = None
                    break
                except IceFlix.WrongMediaId:
                    print("Ha habido un error al añadir los tags a la película seleccionada.\n"
                          "Por favor, inténtelo con otra película\n")
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
                tags.append(input("Introduce la etiqueta que deseas eliminar de la película ",
                                       self.seleccion.info.name,"\n"))

                while input("¿Desea añadir más etiquetas a eliminar? (S/N)\n").capitalize() == "S":
                    tags.append(input("Introduzca la etiqueta\n"))
                num_reintentos = 0
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
                    self.autenticador.refreshAuthorization(self.usuario,self.contrasena)
                    num_reintentos+=1
                except IceFlix.WrongMediaId:
                    print("Ha habido un error al eliminar los tags a la película seleccionada.\n"
                          "Por favor, inténtelo con otra película\n")
                    break
                except IceFlix.TemporaryUnavailable:
                    print("Ha ocurrido un error, por favor trate de iniciar sesión de nuevo\n")
                    self.token_autenticacion = None
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
                    seleccion = int("Introduzca el número de la película que "
                                    "desea seleccionar\n")
                except ValueError:
                    print("Por favor, introduzca un valor válido")
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
                self.autenticador.refreshAuthorization(self.usuario,self.contrasena)
                num_reintentos += 1
            except IceFlix.WrongMediaId:
                print("Ha habido un eror al procesar los títulos\n")
                break
            except IceFlix.TemporaryUnavailable:
                print("Ha ocurrido un error, por favor trate de iniciar sesión de nuevo\n")
                self.token_autenticacion = None
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
                else:
                    self.muestra_pelis_busqueda(1)
                break
            except IceFlix.Unauthorized:
                self.autenticador.refreshAuthorization(self.usuario,self.contrasena)
                num_reintentos += 1
            except IceFlix.WrongMediaId:
                print("Ha habido un eror al procesar los títulos\n")
                break
            except IceFlix.TemporaryUnavailable:
                print("Ha ocurrido un error, por favor trate de iniciar sesión de nuevo\n")
                self.token_autenticacion = None
                break


    def muestra_pelis_busqueda(self,autenticado):
        #TRY-EXCEPT
        """Mostramos las películas que se han obtenido de una búsqueda.
        Diferente si el usuario está autenticado en el sistema o no"""

        i = 1

        if len(self.peliculas == 0):
            print("No se han obtenido resultados para su búsqueda.\n")
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
                    self.autenticador.refreshAuthorization(self.usuario,self.contrasena)
                    num_reintentos += 1
                except IceFlix.WrongMediaId as exc:
                    raise exc
                except IceFlix.TemporaryUnavailable as exc:
                    raise exc


    def mostrar_peliculas(self):
        """Mostramos las películas almacenadas en memoria"""
        i = 0
        if len(self.peliculas == 0):
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
            self.usuario = input("Introduzca su nuevo nombre de usuario\n")
            self.contrasena = hashlib.sha256(getpass.getpass("Introduzca "
                                                        "la contraseña\n").encode()).hexdigest()
            self.autenticador.addUser(self.usuario, self.contrasena, "1234")
            self.autenticador.removeUser(user, "1234")
            print("Usuario cambiado correctamente")
            manejador.anadir_usuario("usuarios.txt",self.usuario,self.contrasena)
            manejador.eliminar_usuario("usuarios.txt",user)

        except IceFlix.TemporaryUnavailable:
            print("No se puede cambiar su usuario ahora mismo, inténtelo más tarden\n")
        except IceFlix.Unauthorized:
            print("Carece de los permisos para realizar esta acción\n")


    def conseguir_token(self):
        """Pedimos el token al authenticator"""
        try:
            self.comprueba_proxy_autenticador()
            self.token_autenticacion = self.autenticador.refreshAuthorization(self.usuario,
                                                                              self.contrasena)
            print("Token obtenido correctamente\n")

        except IceFlix.Unauthorized:
            print("Error intentando conseguir el token de autenticación\n")
            self.token_autenticacion = None #Igual no hace falta porque no se asigna.
        except IceFlix.TemporaryUnavailable:
            print("No se ha podido conseguir el token, inténtelo más tarde\n")


    def comprueba_proxy_autenticador(self):
        """Comprobamos si tenemos el proy del autenticador"""
        try:
            #prx = self.principal.getAuthenticator()
            #if prx is not self.prx_auth:
            #    self.prx_auth = prx
            #    self.conexion_autenticador()

            if  not self.prx_auth:
                self.prx_auth = self.principal.getAuthenticator()
                self.conexion_autenticador()

        except IceFlix.TemporaryUnavailable as exc:
            raise exc



    def comprueba_proxy_catalogo(self):
        """Comprobamos si tenemos el proy del autenticador"""
        try:
            #prx = self.principal.getCatalog()
            #if prx is not self.prx_catalog:
            #    self.prx_catalog = prx
            #    self.conexion_catalogo()

            if  not self.prx_catalog:
                self.prx_auth = self.principal.getCatalog()
                self.conexion_catalogo()

        except IceFlix.TemporaryUnavailable as exc:
            print("El catálogo está temporalmente fuera de servicio"
                  " inténtelo de nuevo más tarde")
            raise exc


    def conexion_catalogo(self):
        """Creamos una conexión con el autenticador"""
        self.catalogo = IceFlix.MediaCatalogPrx.checkedCast(self.prx_catalog)

        if not self.catalogo:
            raise IceFlix.TemporaryUnavailable


    def conexion_autenticador(self):
        """Creamos una conexión con el autenticador"""
        self.autenticador = IceFlix.AuthenticatorPrx.checkedCast(self.prx_auth)

        if not self.autenticador:
            raise IceFlix.TemporaryUnavailable


if __name__ == "__main__":
    sys.exit(Client().main(sys.argv))
