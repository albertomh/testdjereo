from testdjereo import __version__


def metadata(request):  # pragma: no cover
    return {"testdjereo": {"meta": {"version": __version__}}}
