"""
Experimental structure to link IM871-A driver to parser(s).
Uses atomic and threadsafe datastructure deque.
https://docs.python.org/3.5/library/collections.html#collections.deque

Implements that a new key is created when telegram arrives if it doesn't exist at runtime

"""

from collections import deque

# Here we implement a max length. This is not necessary, but avoids saving gigabytes of
# useless data from wm-bus meters we don't care about
MAXBUFFER = 2

# Expecting telegrams from addresses 0xBEEF, 0xF00D and 0xDEAF
postoffice = {
    b'BEEF': deque(maxlen=MAXBUFFER),
    b'F00D': deque(maxlen=MAXBUFFER),
    b'DEAF': deque(maxlen=MAXBUFFER),
}

if __name__ == '__main__':

    # Simulated data flowing from IM871-A.
    # Sender addresses are 4xBEEF, 2xFOOD, 1xBAAD
    telegrams = [b'27442D2CBEEF000000FFFF',
                 b'27442D2CBEEF000001FFFF',
                 b'27442D2CBEEF000002FFFF',
                 b'27442D2CBEEF000003FFFF',
                 b'27442D2CF00D000000FFFF',
                 b'27442D2CF00D000001FFFF',
                 b'27442D2CBAAD000001FFFF'
    ]

    for t in telegrams:                                             # Simulate arrivals at the post office
        address = t[8:12]                                           # Who is this for?
        if address not in postoffice.keys():
            postoffice.update({address: deque(maxlen=MAXBUFFER)})   # Create the new address entry
        postoffice[address].appendleft(t)                           # Insert telegram into deque

    print(postoffice)                                               # Let's see what structure have

    # Simulate data being read by parser(s).
    # Let BEEF read 3 times from postoffice, 3rd time must fail, as deque is only 2 deep.
    try:
        for i in range(3):
            my_telegram = postoffice[b'BEEF'].pop()
            print(my_telegram)
    except Exception as e:
        print(e)
