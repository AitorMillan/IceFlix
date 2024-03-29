https://github.com/AitorMillan/distribuidos_lab

# Cómo ejecutar el programa

## Ejecutar icestorm

Lo primero de todo es ejecutar el archivo ""**./run_icestorm**"" para que se creen los topics correspondientes y el programa funcione correctamente.

## Usando python3

Si quieres ejecutar el programa utilizando el comando python3 debes ejecutar lo siguiente desde la carpeta distribuidos_lab:

"**python3 iceflix/cliente.py --Ice.Config=configs/client.config**"

Adicionalmente se ha incluido un arhcivo de ejecución para evitar tener que escribir todo el comando cada vez que se quiera ejecutar el programa, para ejecutarlo debemos escribir "**./run_client_python**"

## Usando ./run_client_iceflix

Para poder ejecutar el programa de esta manera debes de utilizar los siguientes comandos en la carpeta distribuidos_lab:

"**python3 -m pip install --upgrade build**" (este comando no tiene porqué ser obligatorio, pero en mi caso lo utilicé antes de ejecutar el siguiente comando)

Una vez se ha ejecutado el comando anterior se debe de ejecutar el siguiente:

"**python -m pip install .**" o "**python3 -m pip install .**" 

En mi caso al instalar iceflix me decía que no se añadía al PATH, si ocurre esto no se podrá ejecutar el programa mediante el método listado más abajo.

Para solucionarlo de forma temporal (en la terminal donde estamos), deberemos escribir en nuestro directorio raíz: ""**export PATH="/home/{carpeta_personal}/.local/bin:$PATH"**""

Una vez hemos hecho esto podemos ejecutar el programa mediante "**./run_client_iceflix**"

Si quieres desinstalar el programa puedes hacerlo poniendo "**pip uninstall IceFlix-Client**"

  # Errores de pylint deshabilitados
  
  La mayoría de errores de pylint que tengo desactivados son debido a restricciones de la propia práctica, al tener que implementar todas las interfaces para poder escuchar en todos los canales, he tenido que desactivar todos los errores de **unused-argument** que había, al igual que pasa con los errores  **too-few-public-methods** o **too-many-arguments**, al ser necesidades del propio programa he considerado correcto desactivarlos para que pylint no los marque como erróneos, ya que no es algo que pueda controlar.
  
  No he desactivado los errores de **invalid-name** que me lanza para los nombres de los métodos de las interfaces de los canales de IceStorm porque no sabía si eso se consideraría como desahibilitar muchos errores de pylint, pero en su mayoría son errores que yo no puedo evitar por lo comentado anteriormente.
  
  No obstante, si se han eliminado errores de pylint, todos relacionados con **consider-using-with** a la hora de abrir archivos, los he desactivado porque pienso que la implementación en esos casos usando el "with" de Python hace el programa más engorroso
  
  # Decisiones de diseño
  
  ## Persistencia
  
  Para implementar de forma persistente los usuarios y contraseñas de la aplicación he utilizado un fichero de texto y usado las funciones que da python para abrir y cerrar ficheros. No es la forma más eficiente ya que si queremos eliminar un usuario la única forma que hay es la de leer todo el fichero, y volver a escribir todas las líneas excepto las que no queremos, lo cual en archivos de gran tamaño no es viable.
  
  Debido a la falta de tiempo he decidido implementarlo de esta manera, con más tiempo hubiera intentado implementarlo mediante una base de datos, ya que me parece más eficiente.
  
  # Errores corregidos
  
  ## Pylint no-members
  
  Mirar issue [#01](https://github.com/AitorMillan/distribuidos_lab/issues/1)
