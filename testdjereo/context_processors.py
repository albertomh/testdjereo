from testdjereo import __version__


def metadata(request):
    return {"testdjereo": {"meta": {"version": __version__}}}
