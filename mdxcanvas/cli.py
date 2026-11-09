import sys


def entry():
    if sys.argv[1:] in (["skilldir"], ["--skilldir"]):
        from . import skilldir

        print(skilldir)
        return

    from .main import entry as deploy

    deploy()


if __name__ == '__main__':
    entry()
