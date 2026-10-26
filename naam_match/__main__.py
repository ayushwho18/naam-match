import sys

from .core import match


def main() -> int:
    if len(sys.argv) != 3:
        print('usage: python -m naam_match "NAME ONE" "NAME TWO"')
        return 2
    print(match(sys.argv[1], sys.argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
