# Auth-Microservice
This application represents a small ZeroMQ-based authentication microservice. This tiny authentication server will listen on a socket bound to a given port number, for incoming messages contain simple JSON objects in the format `{"username": [username], "password": [password]}`. The JSON object received by the server will be validated against a JSON schema definition of that format. 

Assuming the provided object has know validation error, the given case-sensitive username will be checked against the server's connected DB. If a username match is found, the case-sensitive password will be checked against DB password record for the found user. If the match of both keys is successfull, a simple string message response of `valid` will be sent by the server. Should either of those matches fail, of the aforementioned data validation fail, a simple string message response of `invalid` will be sent by the server. 

At this time, and as requested by my CS361 partner, the microservice supports a static JSON database, provided as a single file containing an array of JSON object records of users. See the `static_db.json` file in this repo for an example of the expected format. User objects may contain any number of keys, but they *must* contain a `username` and a `password` key. 

The microservice has been built in such a way that it will easily support SQL DB integration in the near future. In fact, the default option for the CLI is reserved for SQL DB use. As an alternative----and the focus of the current implementation----a static JSON db file can be provided via CLI flags `-j` or `--json`.

## Dependencies
To get started, ensure that the `pyzmq` and `jsonschema` packages are installed to your environment or system:
```pip install pyzmq jsonschema```

## Configuration

If you would like the microservice to listen on a specific port, please edit the `PORT` constant in the auth_server.py file. The default is for the service to listen on PORT `8080`.

## Calling the service

The authentication microservice is intended to be started via the CLI. To start the serivice:
```python auth_server.py```

For an elaboration of currently available command line arguments:
```python auth_server.py -h```

To utilize the service with a static JSON db: 
```python auth_server.py --json db_filename.json```

## Sending Data

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

Notably, it is not mandatory to utilize ZeroMQ's send_string() and recv_string(), but it does simplify encoding and serialization within the code. Please see the [ZMQ Sock Class](https://pyzmq.readthedocs.io/en/latest/api/zmq.html#zmq.Socket) documentation for more details (i.e. see recv_ and send_ class methods). 
