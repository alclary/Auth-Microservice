import zmq
import json

# Constant
PORT = 8080

context = zmq.Context()

#  Socket to talk to server
print("Connect to server")
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:" + str(PORT))

# Test requests
test_requests = [
    # Working request - VALID
    '{"username": "julioJones", "password": "falcons"}',
    # Working request - VALID
    '{"username": "d_wright", "password": "bears00"}',
    # Username case incorrect - INVALID
    '{"username": "JulioJones", "password": "falcons"}',
    # Password case incorrect - INVALID
    '{"username": "julioJones", "password": "falCons"}',
    # Username invalid - INVALID
    '{"username": "test", "password": "falcons"}',
    # Password invalid - INVALID
    '{"username": "julioJones", "password": "test"}',
    # Malformed JSON msg - INVALID
    '{"username": "julioJones", "password": "falcons", "extra": "x"}',
    # Just username key - INVALID
    '{"username": "julioJones"}',
    # Just password key - INVALID
    '{"password": "falcons"}',
]

# Cycle through test_requests
for request in test_requests:
    socket.send_string(request)
    #  Get the reply.
    message = socket.recv_string()
    print(f"REQUEST: {request +', ':<67}" + f"RESULT: {message}")
