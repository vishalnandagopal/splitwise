# Splitwise (Unofficial) implementation

attempt at implementing the logic for basic features of [Splitwise](https://www.splitwise.com/) in Python, including settling transactions and ["simplify debts"](https://blog.splitwise.com/2012/09/14/debts-made-simple/) ([video](https://www.youtube.com/watch?v=R2CBrFq9KAI)).

## Running the app

1. Clone the repository

```
$ git clone https://github.com/vishalnandagopal/splitwise.git
```

2. Install Python and Pip.

-   Download [Python](https://python.org/downlaods) and install it.
-   Make sure both Python and Pip are installed using `python --version` / `python3 --version` and `pip --version` / `pip3 --version`

3. Install pipenv

```
$ python -m pip install -U  pipenv
```

4. Let pipenv install from the Pipfile

-   This will also automatically create a virtual environment and run it, if it does not exist.

```
$ pipenv install
```

This project also uses [`mypy`](https://www.mypy-lang.org/) for type-checking in Python.

Install that using

```
$ python -m pip install -U mypy
```

and run your file (file.py) using `mypy file.py` or type check the classes module using `mypy classes`.

### TODO:

-   web UI using flask.
