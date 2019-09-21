def basic_maker_string(variable, operator, targets):
    """
    Given a variable name, an operator (= or +=), and
    a list of targets, this function creates a string of
    the form

    variable =\
            target0\
            target1\
            target2

    Parameters
    ----------
    variable : str, e.g. exec_SOURCES
    operator : str, must be = or +=
    targets : list of str, e.g. [header.hpp, implementation.cxx, target.hpp, target.cxx]

    Returns
    -------
    str

    """
    value = "{} {}\\\n".format(variable, operator)
    spacing = len(value) - 2
    for target in targets:
        value += spacing * " "
        value += target
        if target != targets[-1]:
            value += "\\\n"
    return value


def make_add_to_LTLIBRARIES(libname, LT_prefix, **kwargs):
    """Creates Makefile segment for a new LTLIBRARY.
    SOURCES, CPPFLAGS, etc are specified in the kwargs,
    while the name of the library and prefix for
    the LTLIBRARY directive are passes as arguments.
    Only the base name of the library is required, which
    will then be specified as libname.la.

    LT_prefix_LTLIBRARY += \
            libname.la

    libname_la_KWARG0=\
            kwarg0.0\
            kwarg0.1

    libname_la_KWARG1=\
            kwarg1.0\
            kwarg1.1

    Parameters
    ----------
    libname : str
    LT_prefix : str
    **kwargs : str, each kwarg entry is a list of SOURCES, CPPFLAGS, etc.

    Returns
    -------
    str

    """
    value = ""
    value += basic_maker_string("{}_LTLIBRARIES".format(LT_prefix), '+=',
                                ["{}.la".format(libname)])

    for k in kwargs:
        value += "\n"
        value += basic_maker_string("{}_la_{}".format(libname, k), '=',
                                    kwargs[k])

    return value


def make_add_to_PROGRAMS(program_name, PROGRAMS_prefix, **kwargs):
    """Create Makefile segment for a new PROGRAMS.
    SOURCES, CPPFLAGS, LDADD, etc. are specified by kwargs.
    The prefix should be something like "bin" or "check"

    Parameters
    ----------
    program_name : str
    PROGRAMS_prefix : str
    **kwargs : str, each kwarg entry is a list of SOURCES, CPPFLAGS, etc.

    Returns
    -------
    str

    """
    value = ""
    value += basic_maker_string("{}_PROGRAMS".format(PROGRAMS_prefix), '+=',
                                [program_name])

    for k in kwargs:
        value += "\n"
        value += basic_maker_string("{}_{}".format(program_name, k), '=',
                                    kwargs[k])

    return value


def main():
    m = basic_maker_string("casm_unit_clex_CPPFLAGS", '=', [
        "tests/unit/clex/ChemicalReference_test.cpp",
        "tests/unit/clex/Clexulator_test.cpp"
    ])
    print m
    print "\n\n"

    m = make_add_to_LTLIBRARIES(
        "libgtest",
        "check",
        SOURCES=["submodules/googletest/googletest/src/gtest-all.cc"],
        CPPFLAGS=["$(AM_CPPFLAGS)", "-DGTEST_HAS_PTHREAD=0"])
    print m
    print "\n\n"

    m = make_add_to_PROGRAMS(
        "casm_unit_App",
        "check",
        CPPFLAGS=["$(AM_CPPFLAGS)", "-I$(top_srcdir)/tests/unit"],
        SOURCES=[
            "tests/unit/App/App_test.cpp",
            "tests/unit/App/QueryPlugin_test.cpp",
            "tests/unit/App/settings_test.cpp", "more/sources"
        ],
        LDADD=[
            "libcasm.la", "libcasmtesting.la", "$(BOOST_SYSTEM_LIB)",
            "MORE_BOOST"
        ])
    print m
    print "\n\n"


if __name__ == "__main__":
    main()
