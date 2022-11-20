"""Modulo del cliente de IceFlix"""

import sys
import logging
import time
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
        self.usuario = None
        self.contrasena = None


    def run(self,args):
        """Handles the IceFlix client CLI command."""

        veces_reintentado = 0
        setup_logging()
        logging.info("Starting IceFlix client...")

        while veces_reintentado != REINTENTOS:
            try:

                prx_main = self.communicator().stringToProxy(args[1])


                main = IceFlix.MainPrx.checkedCast(prx_main)

                if not main:
                    raise IceFlix.TemporaryUnavailable

                main.getAuthenticator()
                break
            except IceFlix.TemporaryUnavailable:
                print("Servicio no disponible. Reintentando...")
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
        if not self.usuario:
            opcion = input("CONEXIÓN ESTABLECIDA. ESTADO: NO AUTENTICADO. \n"
                "Elija qué desea hacer:\n"
                "1. Iniciar sesión en el sistema.\n"
                "2. Buscar en el catálogo por nombre\n")
        else:
            print("hola")


if __name__ == "__main__":
    sys.exit(Client().main(sys.argv))
