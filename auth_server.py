import argparse
import json
import signal
import zmq                          # pip install pyzmq
import mysql                        # pip install mysql
import mysql.connector              # pip install mysql-connector-python
from jsonschema import validate     # pip install jsonschema

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
    '-j', '--json', help='Utilize a static JSON file as the user database.', metavar='filename')
args = parser.parse_args()

# Config to interrupt threaded socket listener
interrupted = False


def signal_handler(signum, frame):
    """A handler function to alter a global variable that will assist in
        interrupting the threaded socket listener.
    """
    global interrupted
    interrupted = True


def server_up(db_middleware, json_db=None):
    """Brings up the ZMQ socket listener; behavior contingent on supplied
        middleware function.

    Args:
        db_middleware (func): middleware function to determine behavior on
            received message on socket
        json_db (object): JSON db object, loaded via python JSON library
    """
    # ZMQ Socket Config
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:" + str(PORT))
    print(f"\nServer listening on socket at port {PORT}...\n")

    # Signal observe to allow for Ctrl-C (SIGINT) interrupt of socket listener;
    #   see http://zguide2.zeromq.org/py:interrupt
    signal.signal(signal.SIGINT, signal_handler)
    # Socket listen loop
    while True:
        db_middleware(socket, json_db)
        if interrupted:
            break


def json_middleware(socket, json_db):
    # Listen for JSON content on socket and validate
    try:
        json_msg = socket.recv_json(zmq.NOBLOCK)
    # When zmq.NOBLOCK flag is set above, the following exception is fired
    #   on every socket listen tick that a message is not received. However,
    #   this is needed to allow for SIGINT (Ctrl-C) interrupts to work.
    #   See http://zguide2.zeromq.org/py:interrupt
    except zmq.ZMQError:
        return

    # Once message is recieved:
    try:
        # Utilize JSON Schema defined in SCHEMA constant to validate recieved JSON
        validate(instance=json_msg, schema=SCHEMA)
    except:
        print("Exception: Invalid JSON content received.")
        socket.send_string('invalid')
        return
    else:
        # If JSON is valid, check static JSON DB for case-sensitive matching username; O(n)
        #   If matching username found, check if associated password matches; send response.
        for user in json_db:
            if user['username'] == json_msg['username']:
                if user['password'] == json_msg['password']:
                    socket.send_string('valid')
                    return
        socket.send_string('invalid')
        return


def main():
    # If the -j or --json flag and a JSON db file passed to CLI call.
    if args.json:
        # Try to open and parse given JSON db file as JSON files
        try:
            db = open(args.json)
            json_db = json.load(db)
        except:
            print("Exception: provided JSON database file is invalid.")
            quit()
        else:
            server_up(json_middleware, json_db)
    # TODO: Default (no CLI flag) call, for SQL database implementation.
    else:
        print("Not yet implemented. Placeholder for SQL database integration.\
            \nPlease use -h argument for more options.")


if __name__ == "__main__":
    main()
