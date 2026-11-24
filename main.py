# Simple Key-Value Databse
# CSCE 4350 - Build a databse

import time

from storage import save_command, load_commands

# In memory database
# Each entry contains a key and its value
database = []

def find_entry(key):
    """Find a key, removing ut if it has expired."""
    for entry in database:
        if entry[0] == key:
            expires_at = entry[2]

            if expires_at is not None and time.time() >= expires_at:
                database.remove(entry)

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
    """Retrive a value using its key."""

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


def restore_database():
    """Rebuild the database from saved commands"""

    for command in load_commands():
        parts = command.split()

        if not parts:
            continue

        action = parts[0].upper()

        if action == "SET" and len(parts) == 3:
            set_value(parts[1], parts[2])

        elif action == "DEL" and len(parts) == 2:
            delete_value(parts[1])

        elif action == "MSET" and len(parts) >= 3:
            if(len(parts) - 1 ) % 2 == 0:
                for i in range(1, len(parts), 2):
                    set_value(parts[i], parts[i + 1])

        elif action == "EXPIREAT" and len(parts) == 3:
            entry = find_entry(parts[1])
            if entry is not None:
                entry[2] = float(parts[2])

def main():
    # Restore previously saved information
    restore_database()

    while True:
        try:
            command = input()
        except EOFError:
            break

        parts = command.strip().split()

        if not parts:
            continue

        action = parts[0].upper()

        # SET: store one key-value pair
        if action == "SET" and len(parts) == 3:
            set_value(parts[1], parts[2])
            save_command("SET " + parts[1] + " " + parts[2])
            print("OK")

        # GET: Retreive one value
        elif action == "GET" and len(parts) == 2:
            result = get_value(parts[1])
            print(result if result is not None else "NULL")

        # DEL: Delete a key
        elif action == "DEL" and len(parts) == 2:
            deleted = delete_value(parts[1])

            if deleted:
                save_command("DEL " + parts[1])
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

            save_command(" ".join(parts))
            print("OK")

        # MGET: Retrive multiple values
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
                save_command("EXPIREAT " + parts[1] + " " + str(expires_at))
                print("1")

        # TTL: Check how much time a key has left before expiration
        elif action == "TTL" and len(parts) == 2:
            print(ttl_value(parts[1]))

        # RANGE: Retrive keyts within a alphabetical range
        elif action == "RANGE" and len(parts) == 3:
            keys = range_values(parts[1], parts[2])
            print(" ".join(keys))

        # EXIT: Close the database
        elif action == "EXIT":
            break

        else:
            print("ERROR")

if __name__ == "__main__":
    main()