# Template project for ssdd-lab

This repository is a Python project template.
It contains the following files and directories:

- `configs` has several configuration files examples.
- `iceflix` is the main Python package.
  You should rename it to something meaninful for your project.
- `iceflix/__init__.py` is an empty file needed by Python to
  recognise the `iceflix` directory as a Python module.
- `iceflix/cli.py` contains several functions to handle the basic console entry points
  defined in `python.cfg`.
  The name of the submodule and the functions can be modified if you need.
- `iceflix/iceflix.ice` contains the Slice interface definition for the lab.
- `iceflix/main.py` has a minimal implementation of a service,
  without the service servant itself.
  Can be used as template for main or the other services.
- `pyproject.toml` defines the build system used in the project.
- `run_client` should be a script that can be run directly from the
  repository root directory. It should be able to run the IceFlix
  client.
- `run_service` should be a script that can be run directly from the
  repository root directory. It should be able to run all the services
  in background in order to test the whole system.
- `setup.cfg` is a Python distribution configuration file for Setuptools.
  It needs to be modified in order to adeccuate to the package name and
  console handler functions.
  
  # Decisiones de diseño
  
  ## Persistencia
  
  Para implementar de forma persistente los usuarios y contraseñas de la aplicación he utilizado un fichero de texto y usado las funciones que da python para abrir y cerrar ficheros. No es la forma más eficiente ya que si queremos eliminar un usuario la única forma que hay es la de leer todo el fichero, y volver a escribir todas las líneas excepto las que no queremos, lo cual en archivos de gran tamaño no es viable.
  
  Debido a la falta de tiempo he decidido implementarlo de esta manera, con más tiempo hubiera intentado implementarlo mediante una base de datos, ya que me parece más eficiente.
  
  # Errores corregidos
  
  ## Pylint no-members
  
  Mirar issue [#01](https://github.com/AitorMillan/distribuidos_lab/issues/1)
  
  # Repositorios funcionales
  
  En caso de que el programa no funcione con otros programas, se ha comprobado que la ejecución el cliente funciona perfectamente con los siguientes programas:
  (Por añadir)
