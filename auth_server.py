# pip install pyzmq, mysql, mysql-connector-python, python-dotenv, jsonschema
import os
import argparse
import json
import signal
import zmq
import mysql
import mysql.connector
from dotenv import load_dotenv
from jsonschema import validate, ValidationError

# Constants
PORT = 8080
SCHEMA = {
    "type": "object",
    "required": ['username', 'password'],
    "properties": {
            "username": {"type": "string"},
            "password": {"type": "string"},
    },
    "additionalProperties": False
}

# Argparse Config; see https://docs.python.org/3/library/argparse.html#action
parser = argparse.ArgumentParser(
    description='Micro API server to authenticate users against database.')
parser.add_argument(
    '-j', '--json', help='Utilize a static JSON file as the user database.',
    metavar='filename')
args = parser.parse_args()

# Config to interrupt threaded socket listener
interrupted = False


def signal_handler(signum, frame):
    """A handler function to alter a global variable that will assist in
        interrupting the threaded socket listener.
    """
    global interrupted
    interrupted = True


def server_up(db_middleware, db):
    """Brings up the ZMQ socket listener; behavior contingent on supplied
        middleware function.

    Args:
        db_middleware (func): middleware function to determine behavior on
            received message on socket
        db (object): JSON db object loaded via python JSON library; OR mysql
            connector object.
    """
    # ZMQ Socket Config
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:" + str(PORT))
    print(f"Server listening on socket at port {PORT}...\n")

    # Signal observe to allow for Ctrl-C (SIGINT) interrupt of socket listener;
    #   see http://zguide2.zeromq.org/py:interrupt
    signal.signal(signal.SIGINT, signal_handler)
    # Socket listen loop
    while True:
        # Listen for JSON content on socket and validate
        try:
            if interrupted:
                break
            recv_msg = socket.recv_json(zmq.NOBLOCK)
        # When zmq.NOBLOCK flag is set above, the following exception is fired
        #   on every socket listen tick that a message is not received. However,
        #   this is needed to allow for SIGINT (Ctrl-C) interrupts to work.
        #   See http://zguide2.zeromq.org/py:interrupt
        except zmq.ZMQError:
            continue
        else:
            # Once message is recieved:
            try:
                # Utilize JSON Schema defined in SCHEMA constant to validate
                #   recieved JSON
                validate(instance=recv_msg, schema=SCHEMA)
            except ValidationError:
                print("Logger: Invalid JSON content received.")
                socket.send_string('invalid')
                continue
            else:
                db_middleware(socket, recv_msg, db)


def json_middleware(socket, recv_msg, json_db):
    """Middleware to handle checking of recieved msg username and password to
        static json file database. Sends socket message of 'valid' if received
        username and password combo match case-sensitive entry in DB, 'invalid'
        if not.

    Args:
        socket (object): open ZMQ socket
        recv_msg (dict): validated JSON message received on listening socket
        json_db (object): object representation of static db, imported from
            JSON file.
    """
    # If JSON is valid, check static JSON DB for case-sensitive matching
    #   username; O(n). If matching username found, check if associated
    #   password matches; send response.
    for user in json_db:
        if user['username'] == recv_msg['username']:
            if user['password'] == recv_msg['password']:
                socket.send_string('valid')
                return
    socket.send_string('invalid')
    return


def mysql_middleware(socket, recv_msg, mysql_connector):
    """Middleware to handle checking of received msg username and password
        against mysql db. Sends socket message of 'valid' if received
        username and password combo match case-sensitive entry in DB, 'invalid'
        if not.

    Args:
        socket (object): open ZMQ socket
        recv_msg (dict): validated JSON message received on listening socket
        mysql_connector (object): mysql_connector object, initialized and active
            for connected db.
    """
    # Note: 'BINARY' makes the query values case-sensitive
    query = f"SELECT username, password FROM users WHERE username = BINARY '{recv_msg['username']}' AND password = BINARY '{recv_msg['password']}';"
    cursor = mysql_connector.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    if result:
        socket.send_string('valid')
    else:
        socket.send_string('invalid')
    return


def main():
    """Main function - parse CLI arguments if provided, detect initial errors
        with DB connections, otherwise put server up.
    """
    # If the -j or --json flag and a JSON db file passed to CLI call.
    if args.json:
        # Try to open and parse given JSON db file as JSON files
        try:
            db = open(args.json, encoding='UTF-8')
            json_db = json.load(db)
        except Exception as err:
            print(
                f"Exception: JSON DB issue. Check static DB file \n\t{str(err)}")
            quit()
        else:
            server_up(json_middleware, json_db)
    # Default (no CLI flags); mysql database implementation.
    else:
        try:
            # attempt to load DB details from .env file in same directory
            load_dotenv()
            mydb = mysql.connector.connect(
                host=os.environ.get('MYSQL_HOST'),
                user=os.environ.get('MYSQL_USER'),
                password=os.environ.get('MYSQL_PASSWORD'),
                db=os.environ.get('MYSQL_DATABASE'))
        except Exception as err:
            print(
                f"Exception: DB initialization/connection issue. Check env "
                f"file, env variables, and network. \n\t{str(err)}")
            quit()
        else:
            server_up(mysql_middleware, mydb)


if __name__ == "__main__":
    main()
