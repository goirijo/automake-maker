from __future__ import absolute_import
from __future__ import print_function

import glob
import os
import subprocess
import git
import re


def horizontal_space():
    return "\n\n"


def vertical_space():
    return "    "


def horizontal_separator():
    return "#-------------------------------------------------------------------------------#"


def horizontal_divide():
    return horizontal_space() + horizontal_separator() + horizontal_space()


def static_vars(**kwargs):
    """
    Decorator for caching variables within functions

    """

    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func

    return decorate


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
    variable : str, e.g. my_executable_SOURCES
    operator : str, must be = or +=
    targets : list of str, e.g. [header.hpp, implementation.cxx, target.hpp, target.cxx]

    Returns
    -------
    str

    """
    value = "{} {} \\\n".format(variable, operator)
    # spacing = len(value) - 2
    for target in targets:
        # value += spacing * " "
        value += vertical_space()
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
        if len(kwargs[k]) == 0:
            continue
        value += "\n"
        value += basic_maker_string("{}_la_{}".format(
            libname.replace('-', '_'), k), '=', kwargs[k])

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
        if len(kwargs[k]) == 0:
            continue
        value += "\n"
        value += basic_maker_string("{}_{}".format(
            program_name.replace('-', '_'), k), '=', kwargs[k])

    return value


def make_add_to_EXTRA_DIST(files):
    """Create a Makefile segment to append new files to the
    EXTRA_DIST directive.

    EXTRA_DIST +=\
            file0.txt\
            file1.txt

    Parameters
    ----------
    files : list of str

    Returns
    -------
    str

    """
    if len(files) == 0:
        return ""
    return basic_maker_string("EXTRA_DIST", "+=", files)


def make_HEADERS(includedir, files):
    """Create a Makefile segment for a new HEADERS directory that
    includes the given file

    path_to_include_directory_includedir=$(includedir)/path/to/include/directory
    path_to_include_directory_HEADERS=\
            file0.hh\
            file1.hh\
            file2.hh

    Parameters
    ----------
    includedir : str, the path you want to invoke when you #include the library
    files : list of files that you want to distribute into the includedir

    Returns
    -------
    str

    """
    flattened = includedir.replace('/', '_')

    value = flattened + "_includedir=" + os.path.join("$(includedir)",
                                                      includedir)
    value += "\n"
    value += basic_maker_string(flattened + "_include_HEADERS", "=", files)

    return value


def files_with_extension_at_directory(extensions, directory):
    """Find all the files of the specified extensions that exist in the
    provided directory.

    Parameters
    ----------
    extensions : list of str
    directory : str

    Returns
    -------
    list of str

    """
    files = [
        f
        for ext in extensions
        for f in glob.glob(os.path.join(directory, "*{}".format(ext)))
    ]
    return files


#------------------------------------------------------------------#


def header_extensions():
    """List of extensions that are considered header files:
    .h, .hh, .hpp
    Returns
    -------
    list of str

    """
    return [".h", ".hh", ".hpp"]


def source_extensions():
    """List of extensions that are considered source files:
    .c, .cc, .cxx, .cpp
    Returns
    -------
    list of str

    """
    return [".c", ".cc", ".cxx", ".cpp"]


def has_header_extension(filepath):
    """Returns true of the file has an extension such as
    .h, .hh, etc as defined by header_extensions()

    Parameters
    ----------
    filepath : path to file

    Returns
    -------
    bool

    """
    for ext in header_extensions():
        if filepath.endswith(ext):
            return True
    return False


def has_source_extension(filepath):
    """Returns true of the file has an extension such as
    .c, .cc, etc as defined by source_extensions()

    Parameters
    ----------
    filepath : path to file

    Returns
    -------
    bool

    """
    for ext in source_extensions():
        if filepath.endswith(ext):
            return True
    return False


def header_and_source_extensions():
    return header_extensions() + source_extensions()


def git_root(path):
    git_repo = git.Repo(path, search_parent_directories=True)
    git_root = git_repo.git.rev_parse("--show-toplevel")
    return git_root


def all_files_tracked_by_git():
    return subprocess.check_output(
        ["git", "ls-tree", "--full-tree", "-r", "--name-only",
         "HEAD"]).splitlines()


def all_files_ignored_by_git():
    return subprocess.check_output(["git", "status", "--ignored"]).splitlines()


@static_vars(cached_roots={})
def relative_filepath_is_tracked_by_git(filename):
    """Checks if the given file, which must exist relative to
    the path of execution, is being tracked by git.

    TODO: I thought caching the root would help because finding the git
    root might be slow with so many calls, but I'm not convinced it makes
    a big difference.

    Parameters
    ----------
    filename : path to file relative to execution directory

    Returns
    -------
    bool

    """
    cwd = os.getcwd()

    if cwd not in relative_filepath_is_tracked_by_git.cached_roots or True:
        relative_filepath_is_tracked_by_git.cached_roots[cwd] = git_root(cwd)

    git_root_path = relative_filepath_is_tracked_by_git.cached_roots[cwd]

    return os.path.relpath(filename,
                           git_root_path) in all_files_tracked_by_git()


def purge_untracked_files(file_list):
    """Return the same list of files, but only include files
    that are currently being tracked by the git repository

    Parameters
    ----------
    file_list : list of path, relative to execution path

    Returns
    -------
    list of path

    """
    return [f for f in file_list if relative_filepath_is_tracked_by_git(f)]


def purge_git_related_files(file_list):
    """Return the same list of files, but exclude
    files that exist in the repository for git purposes and
    are not needed for the build, such as .gitignore.

    Parameters
    ----------
    file_list : list of path, relative to execution path

    Returns
    -------
    list of path

    """
    ignorable = [".gitignore"]
    return [f for f in file_list if os.path.basename(f) not in ignorable]

