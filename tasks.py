from invoke import task


@task
def exportreqs(c):
    c.run("poetry export -f requirements.txt --output requirements.txt --without-hashes")

@task
def format(c):
    c.run("black -l 120 bot tests")
