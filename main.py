# Simple Key-Value Databse
# CSCE 4350 - Build a databse

import time
import json

from copy import deepcopy

from storage import save_command, load_commands

# In memory database
# Each entry contains a key and its value
database = []

# Custom hashes storage using nested lists
# Each hash contains a name and a list of field value pairs
hashes = []

def find_entry(key):
    """Find a key, removing ut if it has expired."""
    for entry in database:
        if entry[0] == key:
            expires_at = entry[2]

            if expires_at is not None and time.time() >= expires_at:
                database.remove(entry)
                return None

            return entry
    
    return None

def set_value(key,value):
    """Store or update a key-value pair"""
    entry = find_entry(key)

    if entry is not None:
        entry[1] = value
        entry[2] = None

    else:
        database.append([key, value, None])

def get_value(key):
    """Retrieve a value using its key."""

    entry = find_entry(key)
    return entry[1] if entry is not None else None

def delete_value(key):
    """Delete a key from the in-memory index."""
    entry = find_entry(key)

    if entry is not None:
        database.remove(entry)
        return True

    return False

def key_exists(key):
    """Check whether a key exists."""
    return find_entry(key) is not None

def expire_value(key,seconds):
    """Assign a time-to-live to a key."""
    entry = find_entry(key)

    if entry is None:
        return None

    expires_at = time.time() + seconds
    entry[2] = expires_at

    return expires_at

def ttl_value(key):
    """Return the remaning TTL in seconds."""
    entry = find_entry(key)

    if entry is None:
        return -2

    if entry[2] is None:
        return -1

    remaning = entry[2] - time.time()

    if remaning <= 0:
        database.remove(entry)
        return -2

    return int(remaning)

def range_values(start, end):
    """Return sorted keys within an inclusive range."""
    keys = []

    # Work on a coopy becuase find_value mat removed exired keys.
    for entry in database[:]:
        key = entry[0]

        if find_entry(key) is not None and start <= key <= end:
            keys.append(key)

    keys.sort()
    return keys

def find_hash(hash_name):
    """Find a hash by name."""
    for entry in hashes:
        if entry[0] == hash_name:
            return entry

    return None

def hset_value(hash_name, field, value):
    """Create or update a field inside a hash."""
    hash_entry = find_hash(hash_name)

    if hash_entry is None:
        hash_entry = [hash_name, []]
        hashes.append(hash_entry)

    for entry in hash_entry[1]:
        if entry[0] == field:
            entry[1] = value
            return 0

    hash_entry[1].append([field, value])
    return 1

def hget_value(hash_name, field):
    """Retrieve a single field from a hash."""
    hash_entry = find_hash(hash_name)

    if hash_entry is None:
        return None

    for entry in hash_entry[1]:
        if entry[0] == field:
            return entry[1]

    return None

def hgetall_values(hash_name):
    """Retrieve all field value pairs from a hash"""
    hash_entry = find_hash(hash_name)

    if hash_entry is None:
        return []

    return sorted(hash_entry[1], key=lambda entry: entry[0])

def replay_command(command):
    """Apply a saved command without writing it again."""
    parts = command.split()

    if not parts:
        return

    action = parts[0].upper()

    if action == "SET" and len(parts) == 3:
        set_value(parts[1], parts[2])

    elif action == "DEL" and len(parts) == 2:
        delete_value(parts[1])

    elif action == "MSET" and len(parts) >= 3:
        if (len(parts) - 1) % 2 == 0:
            for i in range(1, len(parts), 2):
                set_value(parts[i], parts[i + 1])

    elif action == "EXPIREAT" and len(parts) == 3:
        entry = find_entry(parts[1])
        if entry is not None:
            entry[2] = float(parts[2])

    elif action == "HSET" and len(parts) == 4:
        hset_value(parts[1], parts[2], parts[3])

def restore_database():
    """Restore ordinary writes and comitted transactions."""
    for command in load_commands():

        if command.startswith("TXN "):
            try:
                operations = json.loads(command[4:])
                
            except (ValueError, TypeError):
                continue

            if not isinstance(operations, list):
                continue

            for operation in operations:
                if isinstance(operation, str):
                    replay_command(operation)

        else:
            replay_command(command)

def main():
    # Restore previously saved information
    restore_database()

    transaction_active = False
    transaction_snapshot = []
    hash_snapshot = []
    pending_commands = []

    def record_write(command):
        """Queue writes during a transaction, otherwise save."""
        if transaction_active:
            pending_commands.append(command)

        else:
            save_command(command)

    while True:
        try:
            command = input()
        except EOFError:
            break

        parts = command.strip().split()

        if not parts:
            continue

        action = parts[0].upper()

        # Start a transaciton
        if action == "BEGIN" and len(parts) == 1:
            if transaction_active:
                print("ERROR")

            else:
                transaction_snapshot = [entry.copy() for entry in database]
                hash_snapshot = deepcopy(hashes)
                
                pending_commands = []
                transaction_active = True
                print("OK")

        # Save a transaction
        elif action == "COMMIT" and len(parts) == 1:
            if not transaction_active:
                print("ERROR")
                continue

            record = "TXN " + json.dumps(pending_commands)
            save_command(record)

            pending_commands = []
            transaction_snapshot = []
            hash_snapshot = []
            transaction_active = False
            print("OK")

        # Cancel a transaction
        elif action == "ABORT" and len(parts) == 1:
            if not transaction_active:
                print("ERROR")
                continue

            database[:] = transaction_snapshot
            hashes[:] = hash_snapshot

            pending_commands = []
            transaction_snapshot = []
            hash_snapshot = []
            transaction_active = False
            print("OK")
     
        # SET: store one key-value pair
        elif action == "SET" and len(parts) == 3:
            set_value(parts[1], parts[2])
            record_write("SET " + parts[1] + " " + parts[2])
            print("OK")

        # GET: Retreive one value
        elif action == "GET" and len(parts) == 2:
            result = get_value(parts[1])
            print(result if result is not None else "NULL")

        # DEL: Delete a key
        elif action == "DEL" and len(parts) == 2:
            deleted = delete_value(parts[1])

            if deleted:
                record_write("DEL " + parts[1])
                print("1")

            else:
                print("0")

        # EXISTS: Check if a key exists 
        elif action == "EXISTS" and len(parts) == 2:
            print("1" if key_exists(parts[1]) else "0")

        # MSET: Store multiple key-value pairs
        elif action == "MSET" and len(parts) >= 3:
            if(len(parts) - 1) % 2 != 0:
                print("ERROR")
                continue

            for i in range(1, len(parts), 2):
                set_value(parts[i], parts[ i + 1])

            record_write(" ".join(parts))
            print("OK")

        # MGET: Retrieve multiple values
        elif action == "MGET" and len(parts) >= 2:
            values = []

            for key in parts[1:]:
                result = get_value(key)
                values.append(result if result is not None else "NULL")

            print(" ".join(values))

        # EXPIRE: Set an expiration time for a key
        elif action == "EXPIRE" and len(parts) == 3:
            try:
                seconds = int(parts[2])
            except ValueError:
                print("ERROR")
                continue

            if seconds < 0:
                print("ERROR")
                continue

            expires_at = expire_value(parts[1], seconds)

            if expires_at is None:
                print("0")

            else:
                # Save absolute expiration time for restart recovery.
                record_write("EXPIREAT " + parts[1] + " " + str(expires_at))
                print("1")

        # TTL: Check how much time a key has left before expiration
        elif action == "TTL" and len(parts) == 2:
            print(ttl_value(parts[1]))

        # RANGE: Retrieve keyts within a alphabetical range
        elif action == "RANGE" and len(parts) == 3:
            keys = range_values(parts[1], parts[2])
            print(" ".join(keys))

        # HSET: Create or update a hash field
        elif action == "HSET" and len(parts) == 4:
            result = hset_value(parts[1], parts[2], parts[3])

            record_write("HSET " + parts[1] + " " + parts[2] + " " + parts[3])
            print(result)

        # HGET: Retrieve one hash field
        elif action == "HGET" and len(parts) == 3:
            result = hget_value(parts[1], parts[2])
            print(result if result is not None else "NULL")

        # HGETALL: Retrieve every field in a hash
        elif action == "HGETALL" and len(parts) == 2:
            fields = hgetall_values(parts[1])

            output = []

            for field, value in fields:
                output.append(field)
                output.append(value)

            print(" ".join(output))

        # EXIT: Close the database
        elif action == "EXIT":
            break

        else:
            print("ERROR")

if __name__ == "__main__":
    main()