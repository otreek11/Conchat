import secrets
from sys import argv, exit

def dotenv_string(keylen=32, env="development", db_url="sqlite:///teste.db"):
    return f"""
FLASK_APP=src/app.py
FLASK_ENVIRONMENT={env}

SECRET_KEY={secrets.token_urlsafe(keylen)}
DATABASE_URL={db_url}
    """


if __name__ == "__main__":
    with open(".env", 'w') as dotenvf:
        match len(argv):
            case 1:
                dotenvf.write(dotenv_string())
            case 2:
                dotenvf.write(dotenv_string(int(argv[1])))
            case 3:
                dotenvf.write(dotenv_string(int(argv[1]), argv[2]))
            case 4:
                dotenvf.write(dotenv_string(int(argv[1]), argv[2], argv[3]))
        dotenvf.flush()
        