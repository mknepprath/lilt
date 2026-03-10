# -*- coding: utf-8 -*-

"""
Command-line interface for Lilt.
"""

import engine


def main():
    print("=== LILT ===")
    print('Type "start" to begin.\n')

    state = None

    while True:
        try:
            move = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not move:
            continue
        if move.lower() in ('quit', 'exit'):
            print("Bye.")
            break

        result = engine.play(move, state)
        state = result['state']
        print(result['response'])
        print()


if __name__ == "__main__":
    main()
