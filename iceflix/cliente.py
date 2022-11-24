"""Modulo del cliente de IceFlix"""

import sys
import logging
import time
import hashlib
import Ice
import IceFlix # pylint:disable=import-error


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
        self.peliculas = None


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

                self.principal.getCatalog()
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

        return 0


    def menu(self):
        """Muestra un menú al usuario"""
        while True:
            if not self.token_autenticacion:
                opcion = int(input("CONEXIÓN ESTABLECIDA. ESTADO: NO AUTENTICADO. \n"
                                   "Elija qué desea hacer:\n"
                                   "1. Iniciar sesión en el sistema.\n"
                                   "2. Buscar en el catálogo por nombre\n"
                                   "3. Cambiar credenciales\n"))

                if opcion == 1:
                    self.conseguir_token()
                elif opcion == 2:
                    self.buscar_pelis_nombre()
                elif opcion == 3:
                    self.cambiar_credenciales()

            else:
                print("hola")


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
                self.muestra_pelis(0)
            else:
                self.muestra_pelis(1)
        except IceFlix.TemporaryUnavailable:
            print("No se puede realizar la búsqueda de su película, "
                  "por favor, inténtelo más tarde\n")


    def muestra_pelis(self,autenticado):
        """Mostramos las películas. Diferente si el usuario está autenticado en el sistema o no"""
        i = 1
        if autenticado == 0:
            for pelicula in self.peliculas:
                print(i,":",pelicula)
                i += 1
        else:
            for pelicula in self.peliculas:
                pass


    def cambiar_credenciales(self):
        """Cambia las credenciales del usuario por otras"""
        try:
            user = self.usuario
            self.comprueba_proxy_autenticador()
            self.usuario = input("Introduzca su nuevo nombre de usuario\n")
            self.contrasena = hashlib.sha256(input("Introduzca su nueva contraseña\n").encode())
            self.autenticador.addUser(self.usuario, self.contrasena, "1234")
            self.autenticador.removeUser(user, "1234")

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
