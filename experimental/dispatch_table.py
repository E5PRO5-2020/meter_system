"""
Demos dispatch table.
Used for dynamically calling different functions just by way of a text string.
Nowhere do we need to directly call functions. Everywhere we work through their pointers.
https://en.wikipedia.org/wiki/Dispatch_table

Demo:
- The dispatch table initially has two attached functions.
- We can call these functions just by knowing a string name of the meter we want to use.
- Avoids very long and non-dynamic if-elif statements.
- In that way, it enables something like RPC.
- Then we dynamically add a third function, again only using a string name of the function.

"""

# Pre-defined handler functions. Could be many if we support many kinds of meters / many omnipower IDs
def omnipower(m: str):
    print("OmniPower. " + m.upper())


def multical403(m: str):
    print("Multical403. " + m.upper())


def multical803(m: str):
    print("Multical803. " + m.upper())


# meter_name: handler_function (pointer)
dispatch_table = {
    "omnipower": omnipower,
    "multical403": multical403
}

# Register a new function during runtime (registering a callback in the dispatch table)
new_meter_name = "multical803"                                  # Imagine this being sent through MQTT also
new_handler_function = locals()[new_meter_name]                 # Find function pointer in namespace
dispatch_table.update({new_meter_name: new_handler_function})   # Register the function by its pointer

# Do dynamic dispatch using dispatch table. Call a function through the dispatch_table
# Some argument we need to pass, like a C1 telegram
c = "Process data."

for meter in ["omnipower", "multical403", "multical803"]:
    dispatch_table[meter](c)                                    # Use the updated dispatch table to call functions
