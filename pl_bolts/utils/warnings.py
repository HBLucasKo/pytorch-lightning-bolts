import os
import warnings

MISSING_PACKAGE_WARNINGS = {}


def warn_missing_pkg(pkg_name: str, pypi_name: str = None, extra_text: str = None, stdout_func=warnings.warn):
    """
    Template for warning on missing packages, show them just once.

    Args:
        pkg_name: name of missing package
        pypi_name: in case that package name differ from PyPI name
        extra_text: additional text after the base warning
        stdout_func: define used function for streaming warning, use `warnings.warn` or `logging.warning`

    Returns:
        number of warning calls
    """
    global MISSING_PACKAGE_WARNINGS
    if pkg_name not in MISSING_PACKAGE_WARNINGS:
        extra_text = os.linesep + extra_text if extra_text else ''
        if not pypi_name:
            pypi_name = pkg_name
        stdout_func(f'You want to use `{pkg_name}` which is not installed yet,'
                    f' install it with `pip install {pypi_name}`.' + extra_text)
        MISSING_PACKAGE_WARNINGS[pkg_name] = 1
    else:
        MISSING_PACKAGE_WARNINGS[pkg_name] += 1

    return MISSING_PACKAGE_WARNINGS[pkg_name]
