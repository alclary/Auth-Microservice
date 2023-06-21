# Auth-Microservice

This application represents a small [ZeroMQ-based](https://zeromq.org/) authentication microservice. This tiny auth server will listen on a port-bound socket for incoming packets containing simple JSON objects, in the format `{"username": [username], "password": [password]}`. The serialized JSON object received by the server will be validated against a [JSON schema](https://json-schema.org/understanding-json-schema/about.html) definition of that format.

Assuming the provided object produces no validation error, the given case-sensitive username will be checked against the record of the service's connected DB. If a username match is found, the case-sensitive password will be checked against the same username record. If the match of both keys is successful, a simple string message response of `valid` will be sent by the server. Should either of those matches fail, or the aforementioned data validation fail, a message response of `invalid` will be sent by the server. Please see the `test_client.py` file in the repo for an example of the data validation in action.

The microservice supports querying against a live mySQL database or a static JSON database---- the latter provided as a single file containing an array of JSON objects describing users. See the `static_db.json` file in this repo for an example of the expected format. User objects in either type of database may contain any number of attributes/keys, but they _must_ contain `username` and `password` attributes/keys.

By default, the microservice python file does not require any CLI arguments and will try to connect to an SQL database. However, it will expect a `.env` file to be located in the same directory as the `auth_server.py` file. The .env file should contain the following variables, one to a line: `MYSQL_HOST=, MYSQL_USER=, MYSQL_PASSWORD=, MYSQL_DATABASE=`. DB details can be entered directly after the equal sign, without quotes or wrapped in quotes. Spaces are permitted before and after the equal sign. The `.env_example` file contains an example of the required variables.

Alternatively, to utilize a static JSON db, a JSON file can be provided via CLI flags `-j` or `--json`.

## Dependencies

To get started, ensure that the pyzmq, mysql, mysql-connector-python, python-dotenv, and jsonschema packages are installed to your environment or system:
`pip install pyzmq, mysql, mysql-connector-python, python-dotenv, jsonschema`

## Configuration

If you would like the microservice to listen on a specific port, please edit the `PORT` constant in the auth_server.py file. The service currently defaults to port `8080`.

## Calling the service

The authentication microservice is intended to be started via the CLI. To start the service:
`python auth_server.py`

For an elaboration of currently available command line arguments:
`python auth_server.py -h`

To utilize the service with a static JSON DB file:
`python auth_server.py --json db_filename.json`

## Sending and Receiving Data

The contents of data requests sent to the service must be sent strictly in the following format (with values in brackets replaced with **strings** wrapped in double-quotes):
`{"username": [username], "password": [password]}`
For example, a real packet might contain:
`{"username": "julioJones", "password": "falcons"}`

In the client, standard the dependencies named above should be imported, and then a ZeroMQ socket readied to make calls to the server. For example:

```python
import zmq
import json

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:8080")

data = '{"username": "julioJones", "password": "falcons"}'

# Send data to server
socket.send_string(data)
# Receive server reply
reply = socket.recv_string()
print(reply)
```

Notably, it is not mandatory to utilize ZeroMQ's send_string() and recv_string(), but it does simplify encoding and serialization within the code. Please see the [ZMQ Socket Class](https://pyzmq.readthedocs.io/en/latest/api/zmq.html#zmq.Socket) documentation for more details (i.e. see recv\* and send\_ class methods). For example, to avoid serialization of JSON objects (i.e. stringifying), an approach like the following could be used:

```python
import zmq
import json

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:8080")

data = {"username": "julioJones", "password": "falcons"}

# Send data to server; python dictionary -> JSON object
socket.send_json(data)
# Receive server reply as byte object; requires decode to convert to string
reply = socket.recv()
print(reply.decode())
```
