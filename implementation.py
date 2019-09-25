from maker import *

def all_boost_LDADD_flags():
    """Returns list of all the autotools boost library linker flags
    that should be added to the LDADD directive, including system,
    filesystem, program_options, regex, and chrono.

    TODO: Linking to all of these is completely unnecessary, you should
    only be linking to the ones you actually need! This function is bad
    and stupid, and you should refactor things so that it doesn't exist anymore.

    Returns
    -------
    list of str

    """

    def flagify(lib):
        return "$(BOOST_{}_LIB)".format(lib)

    return [
        flagify(lib)
        for lib in
        ["SYSTEM", "FILESYSTEM", "PROGRAM_OPTIONS", "REGEX", "CHRONO"]
    ]


def make_libgtest():
    """Creates the Makefile segment for the gtest library used
    for unit testing
    Returns
    -------
    str

    """
    return make_add_to_LTLIBRARIES(
        "libgtest",
        "check",
        SOURCES=["submodules/googletest/googletest/src/gtest-all.cc"],
        CPPFLAGS=[
            "$(AM_CPPFLAGS)", "-DGTEST_HAS_PTHREAD=0",
            "-DGTEST_LINKED_AS_SHARED_LIBRARY=1"
        ])


def make_unit_test(unit_test_directory):
    """Creates the Makefile segment for a particular unit test. Will
    include all the c++ files in the directory as SOURCES, and all
    the other files as EXTRA_DIST. Only files being tracked by git
    will be included.

    The name of the executable will be casm_unit_DIR, where DIR is
    the directory name that includes the files needed for the unit
    test compilation.

    Parameters
    ----------
    unit_test_directory : path to unit test, e.g. "tests/unit/App/"

    Returns
    -------
    str

    """
    last_directory = os.path.basename(os.path.normpath(unit_test_directory))
    test_name = "casm_unit_{}".format(last_directory)

    all_dir_files_relative = [
        os.path.join(unit_test_directory, f)
        for f in os.listdir(unit_test_directory)
    ]
    only_tracked_files = purge_untracked_files(all_dir_files_relative)
    only_makeable_files = purge_git_related_files(only_tracked_files)

    #TODO:
    #I think it would be better if instead of mixing up EXTRA_DIST files
    #with the test code, all files necessary for the test to run existed
    #in a separate subdirectory
    source_files = [f for f in only_makeable_files if f.endswith("_test.cpp")
                   ] + ["tests/unit/gtest_main_run_all.cpp"]
    ldadd = ["libcasm.la", "libcasmtesting.la"] + all_boost_LDADD_flags()

    value = basic_maker_string("TESTS", "+=", [test_name])
    value += "\n"
    value += make_add_to_PROGRAMS(
        test_name,
        "check",
        SOURCES=source_files,
        LDADD=ldadd,
        CPPFLAGS=["$(AM_CPPFLAGS)", "-I$(top_srcdir)/tests/unit/"])

    extra_files = [f for f in only_makeable_files if f not in source_files]
    value += "\n"
    value += make_add_to_EXTRA_DIST(extra_files)

    return value


def make_libcasmtesting():
    """Creates the Makefile segment for the libcasmtesting library,
    which contains implementations shared across various unit tests.
    Returns
    -------
    str

    """
    libdir = "tests/unit"
    #We want all the files in libdir, except gtest_main_run_all.cpp
    sources_candidates = [
        f
        for f in files_with_extension_at_directory(
            header_and_source_extensions(), libdir)
        if "gtest_main_run_all" not in f
    ]

    sources = purge_untracked_files(sources_candidates)

    return make_add_to_LTLIBRARIES(
        "libcasmtesting",
        "check",
        SOURCES=sources,
        CPPFLAGS=[
            "$(AM_CPPFLAGS)", "-DABS_SRCDIR=\\\"$(abs_srcdir)\\\"",
            "-DABS_TOP_BUILDDIR=\\\"$(abs_top_builddir)\\\""
        ],
        LIBADD=["libgtest.la"])


def make_aggregated_unit_test():
    """Create a jumbo Makefile that has everything you need to
    run anything within tests.
    Returns
    -------
    string

    """
    value = horizontal_divide()

    print("Create Makefile segment for libgtest")
    value += make_libgtest()
    value += horizontal_divide()

    print("Create Makefile segment for libcasmtesting")
    value += make_libcasmtesting()
    value += horizontal_divide()

    test_root = "tests/unit"
    test_directories = [
        name
        for name in
        [os.path.join(test_root, ls) for ls in os.listdir(test_root)]
        if os.path.isdir(name) and "test_projects" not in name
    ]

    for d in test_directories:
        print("Create Makefile segment for unit test {}".format(d))
        value += make_unit_test(d)
        value += horizontal_divide()

    return value


def is_extensionless_Eigen_header(filepath):
    """Returns true if the provided file resides in
    include/casm/external/Eigen, which contains header files
    that don't have an extension like .h

    Parameters
    ----------
    filepath : path to file, relative to git root

    Returns
    -------
    bool

    """
    parent, f = os.path.split(filepath)
    return parent == "include/casm/external/Eigen"


def make_include(includeable_path):
    """Create a Makefile segment for including the files of the
    given path as headers

    Parameters
    ----------
    includeable_path : str, path is assumed to begin with "include/"

    Returns
    -------
    str

    """
    assert (includeable_path[0:8] == "include/")

    available_files = [
        os.path.join(includeable_path, f) for f in os.listdir(includeable_path)
        if os.path.isfile(os.path.join(includeable_path, f))
    ]
    only_tracked_files = purge_untracked_files(available_files)
    only_header_files = [
        f for f in only_tracked_files
        if is_extensionless_Eigen_header(f) or has_header_extension(f)
    ]

    target_path = includeable_path[8::]
    return make_HEADERS(target_path, only_header_files)


def make_recursive_include(search_root):
    """Make a jumbo Makefiles so that every single header file
    within the include directory gets installed on the system.

    Returns
    -------
    str

    """
    value = horizontal_divide()

    dirpaths = [dirpath for dirpath, dirnames, files in os.walk(search_root)]

    for d in dirpaths:
        print("Create Makefile segment for headers in {}".format(d))
        candidate = make_include(d)

        #If this is true, then you passed a directory with no headers, and there's just
        #a dangling HEADER list
        if search_root not in candidate:
            print("Skipping {} because there are no headers there...".format(d))
            continue

        value += candidate
        value += horizontal_divide()

    return value


def make_ccasm():
    """Create Makefile for ccasm executable

    Returns
    -------
    str

    """
    print("Create Makefile for ccasm program")
    value = make_add_to_PROGRAMS(
        "ccasm",
        "bin",
        SOURCES=["apps/ccasm/ccasm.cpp"],
        LDADD=["libcasm.la"] + all_boost_LDADD_flags())
    return value


def make_casm_complete():
    """Create Makefile for casm-complete executable

    Returns
    -------
    str

    """
    print("Create Makefile for casm-complete program")

    value = "if ENABLE_BASH_COMPLETION\n"
    value += "bashcompletiondir=$(BASH_COMPLETION_DIR)\n\n"

    value += basic_maker_string("dist_bashcompletion_DATA", "=",
                                ["apps/completer/casm"])
    value += "\n"

    value += make_add_to_PROGRAMS(
        "casm-complete",
        "bin",
        SOURCES=["apps/completer/complete.cpp"],
        LDADD=["libcasm.la"] + all_boost_LDADD_flags())

    value += "\n\nendif"

    return value


def make_lib(libname, search_root, additional_sources, **kwargs):
    """Descends into search_root and adds every file with
    a source extension as a SOURCE. Given a list of the
    related headers, it will also include those alongside the
    sources

    Parameters
    ----------
    libname : name of the library, e.g. libcasm
    search_root : path from which to descend and search for source files
    additional_sources : list of paths, these should be all the headers

    Returns
    -------
    str

    """
    files = [(dirpath, files)
             for dirpath, dirnames, files in os.walk(search_root)]
    source_files = [
        os.path.join(d, f) for d, fs in files for f in fs
        if has_source_extension(f)
    ]

    return make_add_to_LTLIBRARIES(
        libname, "lib", SOURCES=source_files + additional_sources, **kwargs)


def make_libcasm(additional_sources):
    """Create Makefile for libcasm by aggregating every source
    file within src/casm. Also adds the additional sources
    (header files that this routine won't search for)

    Parameters
    ----------
    additional_sources : list of additional files, such as headers

    Returns
    -------
    str

    """
    value = make_lib(
        "libcasm",
        "src/casm",
        additional_sources,
        LIBADD=all_boost_LDADD_flags(),
        LDFAGS=["-avoid-version", "$(BOOST_LDFLAGS)"])
    return value

def make_libccasm(additional_sources):
    """Create Makefile for libccasm by aggregating every source
    file within src/ccasm. Also adds the additional sources
    (header files that this routine won't search for)

    Parameters
    ----------
    additional_sources : list of additional files, such as headers

    Returns
    -------
    str

    """
    value = make_lib(
        "libccasm",
        "src/ccasm",
        additional_sources,
        LDFAGS=["-avoid-version"])
    value+="\nsrc/casm/version/autoversion.lo: .FORCE"
    return value


def string_to_file(string, filepath):
    """Writes the string to the provided file

    Parameters
    ----------
    string : str
    filepath : path

    Returns
    -------
    void

    """
    makefile = open(filepath, 'w')
    makefile.write(string)
    makefile.close()

    return


def _exit_on_bad_run_directory():
    print(
        "This script must be run from the root directory of the CASMcode-dev repo."
    )
    exit()


def main():


    try:
        repo = git.Repo("./")
        if os.path.basename(repo.working_dir) != "CASMcode-dev":
            _exit_on_bad_run_directory()

    except git.exc.InvalidGitRepositoryError:
        _exit_on_bad_run_directory()

    chunk = make_ccasm()
    target = os.path.join("apps", "ccasm", "Makemodule.am")
    string_to_file(chunk, target)


    chunk = make_casm_complete()
    target = os.path.join("apps", "completer", "Makemodule.am")
    string_to_file(chunk, target)


    chunk = make_aggregated_unit_test()
    target = os.path.join("tests", "unit", "Makemodule.am")
    string_to_file(chunk, target)


    chunk = make_recursive_include("include/casm")
    target = os.path.join("include", "casm", "Makemodule.am")
    string_to_file(chunk, target)

    header_files = [
        f.replace('\\', '').replace(' ', '') for f in chunk.splitlines()
        if "include/" in f
    ]

    chunk = make_libcasm(header_files)
    target = os.path.join("src", "casm", "Makemodule.am")
    string_to_file(chunk, target)


    chunk = make_recursive_include("include/ccasm")
    target = os.path.join("include", "ccasm", "Makemodule.am")
    string_to_file(chunk, target)

    header_files = [
        f.replace('\\', '').replace(' ', '') for f in chunk.splitlines()
        if "include/" in f
    ]

    chunk = make_libccasm(header_files)
    target = os.path.join("src", "ccasm", "Makemodule.am")
    string_to_file(chunk, target)

if __name__ == "__main__":
    main()
