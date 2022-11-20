"""Module containing a template for a main service."""

import logging

import sys 

import Ice

import IceFlix  # pylint:disable=import-error


usuario = "user"
contrasena = "pass"

class Main(IceFlix.Main):
    """Servant for the IceFlix.Main interface.

    Disclaimer: this is demo code, it lacks of most of the needed methods
    for this interface. Use it with caution
    """

    def getAuthenticator(self, current):  # pylint:disable=invalid-name, unused-argument
        "Return the stored Authenticator proxy."
        print("Devuelvo token")
        # TODO: implement
        return None

    def getCatalog(self, current):  # pylint:disable=invalid-name, unused-argument
        "Return the stored MediaCatalog proxy."
        print("Accedes al programa")
        # TODO: implement
        return None

    def newService(self, proxy, service_id, current):  # pylint:disable=invalid-name, unused-argument
        "Receive a proxy of a new service."
        # TODO: implement
        return

    def announce(self):  # pylint:disable=invalid-name, unused-argument
        "Announcements handler."
        print("Has iniciado sesionñ")
        # TODO: implement
        return


class MainApp(Ice.Application):
    """Example Ice.Application for a Main service."""

    def __init__(self):
        super().__init__()
        self.servant = Main()
        self.proxy = None
        self.adapter = None

    def run(self, args):
        """Run the application, adding the needed objects to the adapter."""
        logging.info("Running Main application")
        comm = self.communicator()
        self.adapter = comm.createObjectAdapter("MainAdapter")
        self.adapter.activate()

        self.proxy = self.adapter.addWithUUID(self.servant)
        print("El proxy de MainApp es: ",self.proxy, flush=True)
        
        self.shutdownOnInterrupt()
        comm.waitForShutdown()

        return 0
    
if __name__ == "__main__":
    MainApp = MainApp()
    sys.exit(MainApp.main(sys.argv)) 
