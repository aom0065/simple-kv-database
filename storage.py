# Handels persistent storage for the database

import os

DATA_FILE = "data.db"

def save_command(command):
    """Append a command to the database file."""

    with open(DATA_FILE, "a", encoding="utf-8") as file:
        file.write(command + "\n")
        file.flush()
        os.fsync(file.fileno())

def load_commands():
    """Read all previously saved commands."""

    commands = []

    if not os.path.exists(DATA_FILE):
        return commands

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        for line in file:
            command = line.strip()

            if command:
                commands.append(command)

        return commands