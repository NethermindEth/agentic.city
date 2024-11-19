Installation
============

Requirements
-----------

* Python 3.9 or higher
* Poetry for dependency management

Installation
----------

Install from source:

.. code-block:: bash

   git clone https://github.com/jorikschellekens/swarmer.git
   cd swarmer
   poetry install

Development Setup
---------------

After installation, set up the development environment:

1. Install pre-commit hooks:

   .. code-block:: bash

      poetry run pre-commit install

2. Run tests:

   .. code-block:: bash

      poetry run pytest

3. Build documentation:

   .. code-block:: bash

      cd docs
      poetry run make html
