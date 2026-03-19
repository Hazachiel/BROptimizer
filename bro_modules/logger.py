from pathlib import Path
from bro_modules import file_manager as bfm

def log_exception(e:Exception, exception_source:str = "Unknown", msg:str = "None", file:Path|None = None):
    """ Función que se lanza cuando ocurre una excepción.

    Guarda un registro con la función donde ocurrió la excepción y un mensaje dentro de la carpeta logs del programa """

    print(f"Ocurrió un error inesperado en: {exception_source}")
    print(f"Mensaje de error: \n {e}")
    with open(f"{bfm.get_logs_folder()}/error_{exception_source}.log", "a") as f:
        if file != None:
            print(f"Archivo afectado: {file}")
            f.write(f"Error Source:{exception_source}\nError Message: {msg}\nException Message: {e}\n")
        else:
            f.write(f"Error Source:{exception_source}\nError Message: {msg}\nAffected file: {file}\nException Message: {e}\n")
