"""Modulo del cliente de IceFlix"""

import sys
import logging
import time
import hashlib
import Ice
import IceFlix # pylint:disable=import-error
from IceFlix import Media # pylint:disable=unused-import,import-error
from IceFlix import MediaInfo # pylint:disable=unused-import,import-error


LOG_FORMAT = '%(asctime)s - %(levelname)-7s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'

REINTENTOS = 3

def setup_logging():
    """Configure the logging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format=LOG_FORMAT,
    )


class Client(Ice.Application):
    """Clase que implementa al cliente de IceFlix"""

    def __init__(self, signalPolicy=0):
        super().__init__()
        self.usuario = "user"
        self.contrasena = hashlib.sha256("pass".encode())
        self.token_autenticacion = None
        self.prx_auth = None
        self.prx_catalog = None
        self.principal = None
        self.autenticador = None
        self.catalogo = None
        self.peliculas = []
        self.seleccion = None
        self.admin = False

    def run(self, args):
        """Handles the IceFlix client CLI command."""

        veces_reintentado = 0
        setup_logging()
        logging.info("Starting IceFlix client...")

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
                                   "8. Abrir menú de aministrador\n"
                                   "9. Cerrar sesión\n"))

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
                    self.menu_admin(estado)
                elif opcion == 9:
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
                                   "5. Salir del menú de administrador\n"))
                if opcion == 1:
                    self.renombra_peli()
                elif opcion == 2:
                    pass #Añadir método para añadir usuarios
                elif opcion == 3:
                    pass #Añadir método para eliminar usuarios
                elif opcion == 5:
                    break

            except ValueError:
                print("Por favor, introduzca un valor válido")


    def eliminar_usuario(self):
        try:
            self.comprueba_proxy_autenticador()
            usuario = input("Introduzca el nombre de usuario a eliminar\n")
            self.autenticador.removeUser(usuario, "1234")
            print("Usuario eliminado correctamente\n")

        except IceFlix.TemporaryUnavailable:
            print("No se puede añadir el usuario ahora mismo, inténtelo más tarden\n")
        except IceFlix.Unauthorized:
            print("Carece de los permisos para realizar esta acción\n")       


    def anadir_usuario(self):
        try:
            self.comprueba_proxy_autenticador()
            usuario = input("Introduzca el nombre de usuario\n")
            contrasena = hashlib.sha256(input("Introduzca la contraseña\n").encode())
            self.autenticador.addUser(usuario, contrasena, "1234")
            print("Usuario añadido correctamente\n")

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

                self.catalogo.addTags(self.seleccion.mediaId,tags,self.token_autenticacion)
                print("Las etiquetas se han añadido correctamente")

            except IceFlix.Unauthorized:
                print("Su sesión ha caducado, por favor, inicie sesión de nuevo")
                self.token_autenticacion = None
            except IceFlix.WrongMediaId:
                print("Ha habido un error al añadir los tags a la película seleccionada.\n"
                      "Por favor, inténtelo con otra película\n")
            except IceFlix.TemporaryUnavailable:
                print("El catálogo no se encuantra actualmente disponible, pruebe más tarde\n")


    def eliminar_tags(self):
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

                self.catalogo.removeTags(self.seleccion.mediaId,tags,self.token_autenticacion)
                print("Las etiquetas se han eliminado correctamente\n")

            except IceFlix.Unauthorized:
                print("Su sesión ha caducado, por favor, inicie sesión de nuevo")
                self.token_autenticacion = None
            except IceFlix.WrongMediaId:
                print("Ha habido un error al eliminar los tags a la película seleccionada.\n"
                      "Por favor, inténtelo con otra película")
            except IceFlix.TemporaryUnavailable:
                print("El catálogo no se encuantra actualmente disponible, pruebe más tarde\n")

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

            if opcion == 0:
                self.peliculas = self.catalogo.getTilesByTags(tags,False,self.token_autenticacion)
            else:
                self.peliculas = self.catalogo.getTilesByTags(tags,True,self.token_autenticacion)

            self.muestra_pelis_busqueda(1)

        except IceFlix.Unauthorized:
            print("Su sesión ha caducado, por favor, inicie sesión de nuevo")
            self.token_autenticacion = None
        except IceFlix.WrongMediaId:
            print("Ha habido un eror al procesar los títulos\n")
        except IceFlix.TemporaryUnavailable:
            print("El servicio se encuentra temporalmente fuera de servicio, "
                  "por favor, inténtelo más tarde\n")


    def buscar_pelis_nombre(self):
        """Buscamos en el catálogo películas por nombre"""
        try:
            self.comprueba_proxy_catalogo()
            cadena = input("Introduzca el nombre de la película"
                           " que desea buscar\n")
            opcion = int(input("¿Desea buscar por el título exacto que ha introducido (0)"
                               " o buscar todas las películas que contengan ese título? (1)\n"))
            while opcion not in (0, 1):
                opcion = int(input("Por favor, escoja una opción válida\n"))

            if opcion == 0:
                self.peliculas = self.catalogo.getTilesByName(cadena, True)
            else:
                self.peliculas = self.catalogo.getTilesByName(cadena, False)

            if not self.token_autenticacion:
                self.muestra_pelis_busqueda(0)
            else:
                self.muestra_pelis_busqueda(1)

        except IceFlix.TemporaryUnavailable:
            print("El servicio se encuentra temporalmente fuera de servicio, "
                  "por favor, inténtelo más tarde\n")
        except IceFlix.Unauthorized:
            print("Su sesión ha caducado. Por favor, renuévela")
            self.token_autenticacion = None
        except IceFlix.WrongMediaId:
            print("Ha habido un eror al procesar los títulos\n")



    def muestra_pelis_busqueda(self,autenticado):
        """Mostramos las películas que se han obtenido de una búsqueda.
        Diferente si el usuario está autenticado en el sistema o no"""
        try:
            i = 1

            if len(self.peliculas == 0):
                print("No se han obtenido resultados para su búsqueda.\n")
            elif autenticado == 0:
                for pelicula in self.peliculas:
                    print(i,":",pelicula)
                    i += 1
                print("Para ver más información de las películas inicie sesión\n")
            else:
                listado = []

                for pelicula in self.peliculas:
                    media = self.catalogo.getTile(pelicula,self.token_autenticacion)
                    print(i,": ",media.info.name, " [",media.info.tags,"]")
                    listado.append(media)
                    i += 1

                self.peliculas = listado.copy()

        except IceFlix.Unauthorized as exc:
            raise exc
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
            self.comprueba_proxy_autenticador()
            self.usuario = input("Introduzca su nuevo nombre de usuario\n")
            self.contrasena = hashlib.sha256(input("Introduzca su nueva contraseña\n").encode())
            self.autenticador.addUser(self.usuario, self.contrasena, "1234")
            self.autenticador.removeUser(user, "1234")
            print("Usuario cambiado correctamente")

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
            print("El autenticador está temporalmente fuera de servicio"
                  " inténtelo de nuevo más tarde")
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
