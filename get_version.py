import tomli

with open("pyproject.toml", "rb") as f:
    pyproject = tomli.load(f)
print(pyproject["project"]["version"])
