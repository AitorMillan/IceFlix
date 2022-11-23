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
        self.principal = None
        self.autenticador = None

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

        while True:
            self.menu()
            break

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
                    None # pylint:disable=pointless-statement
                elif opcion == 3:
                    self.cambiar_credenciales()

            else:
                print("hola")


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
            print("No se puede cambiar su usuario ahora mismo, inténtelo más tarde")
        except IceFlix.Unauthorized:
            print("Carece de los permisos para realizar esta acción")


    def conseguir_token(self):
        """Pedimos el token al authenticator"""
        try:
            self.comprueba_proxy_autenticador()
            self.token_autenticacion = self.autenticador.refreshAuthorization(self.usuario,
                                                                              self.contrasena)

        except IceFlix.Unauthorized:
            print("Error intentando conseguir el token de autenticación\n")
            self.token_autenticacion = None #Igual no hace falta porque no se asigna.
        except IceFlix.TemporaryUnavailable:
            print("No se ha podido conseguir el token, inténtelo más tarde")
        except Ice.ConnectionRefusedException:
            self.prx_auth = None
            self.conseguir_token()


    def comprueba_proxy_autenticador(self):
        """Comprobamos si tenemos el proy del autenticador"""
        try:
            if  not self.prx_auth:
                self.prx_auth = self.principal.getAuthenticator()
                self.conexion_autenticador()

        except IceFlix.TemporaryUnavailable as exc:
            print("El autenticador está temporalmente fuera de servicio"
                  " inténtelo de nuevo más tarde")
            raise exc


    def conexion_autenticador(self):
        """Creamos una conexión con el autenticador"""
        self.autenticador = IceFlix.AuthenticatorPrx.checkedCast(self.prx_auth)

        if not self.autenticador:
            raise IceFlix.TemporaryUnavailable


if __name__ == "__main__":
    sys.exit(Client().main(sys.argv))
