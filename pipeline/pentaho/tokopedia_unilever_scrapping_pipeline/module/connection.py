from pathlib import Path
from pandas import DataFrame
from pandas import read_csv
from urllib.parse import quote_plus

def url(user: str, password: str, host: str, port: str, database: str) -> str:
    """
    Get connection url of sqlalchemy for Oracle database. 

    Args:
        - user(string): username to access database
        - password string): password to access database
        - host(string): host to access database
        - port(string): port to access database
        - database(string): database name

    Returns:
        url_string(string): connection url of sqlalchemy for Oracle database 
    """
    return f"postgresql+psycopg2://{user}:{quote_plus(password)}@{host}:{port}/{database}"

def credential_get(credential_file_path: str =  f"{str(Path(__file__).parent.parent)}\\credential.csv"):
    """
    Function to get the credential data from credential.csv
    
    Args:
        credential_file_path (string): directory path of credential file. the file must be in csv format with pipe ("|") as separator. The default file path will be "root\\credential.csv"
    
    Returns:
        credential_data (pandas dataframe): table containing credential to connect to database
        credential_dict (list): result of transforming credential_data into a list of data per row (each row stored as dictionary)
    """
    credential_data: DataFrame = read_csv(filepath_or_buffer = credential_file_path, sep = "|", dtype = {"port": "object"})
    credential_data: DataFrame = credential_data.fillna('')
    credential_dict: list[dict[str, str]] = credential_data.to_dict('records')
    return credential_dict[0]