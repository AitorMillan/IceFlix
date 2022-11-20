"""Modulo del cliente de IceFlix"""

import sys
import logging
import Ice
import IceFlix # pylint:disable=import-error


LOG_FORMAT = '%(asctime)s - %(levelname)-7s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'

def setup_logging():
    """Configure the logging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format=LOG_FORMAT,
    )


class Client(Ice.Application):
    """Clase que implementa al cliente de IceFlix"""
    def run(self,args):
        """Handles the IceFlix client CLI command."""
        setup_logging()
        logging.info("Starting IceFlix client...")
        try:
            prx_main = self.communicator().stringToProxy(args[1])

        
            main = IceFlix.MainPrx.checkedCast(prx_main)

            if not main:
                print("Error")

        except IceFlix.TemporaryUnavailable:
            print("Servicio no disponible. Reintentando...")
        main.getAuthenticator()

        return 0

#def client(Ice.Application):


if __name__ == "__main__":
    sys.exit(Client().main(sys.argv))