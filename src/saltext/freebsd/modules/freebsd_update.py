"""
Support for freebsd-update utility on FreeBSD.

.. versionadded:: 2017.7.0

:maintainer:    George Mamalakis <mamalos@gmail.com>
:maturity:      new
:platform:      FreeBSD
"""

import logging

import salt.utils.path
from salt.exceptions import CommandNotFoundError

log = logging.getLogger(__name__)

# Define the module's virtual name
__virtualname__ = "freebsd_update"
__virtual_aliases__ = ("freebsd-update",)


def __virtual__():
    """
    .. versionadded:: 2016.3.4

    Only work on FreeBSD RELEASEs >= 6.2, where freebsd-update was introduced.
    """
    if __grains__["os"] != "FreeBSD":
        return (
            False,
            "The freebsd_update execution module cannot be loaded: only available on"
            " FreeBSD systems.",
        )
    if float(__grains__["osrelease"]) < 6.2:
        return (
            False,
            "freebsd_update is only available on FreeBSD versions >= 6.2-RELESE",
        )
    if "release" not in __grains__["kernelrelease"].lower():
        return (False, "freebsd_update is only available on FreeBSD RELEASES")
    return __virtualname__


def _cmd(**kwargs):
    """
    .. versionadded:: 2016.3.4

    Private function that returns the freebsd-update command string to be
    executed. It checks if any arguments are given to freebsd-update and appends
    them accordingly.
    """
    update_cmd = salt.utils.path.which("freebsd-update")
    if not update_cmd:
        raise CommandNotFoundError('"freebsd-update" command not found')

    params = []
    if "basedir" in kwargs:
        params.append("-b {}".format(kwargs["basedir"]))
    if "workdir" in kwargs:
        params.append("-d {}".format(kwargs["workdir"]))
    if "conffile" in kwargs:
        params.append("-f {}".format(kwargs["conffile"]))
    if "force" in kwargs:
        params.append("-F")
    if "key" in kwargs:
        params.append("-k {}".format(kwargs["key"]))
    if "newrelease" in kwargs:
        params.append("-r {}".format(kwargs["newrelease"]))
    if "server" in kwargs:
        params.append("-s {}".format(kwargs["server"]))
    if "address" in kwargs:
        params.append("-t {}".format(kwargs["address"]))

    if params:
        return "{} {}".format(update_cmd, " ".join(params))
    return update_cmd


def _wrapper(orig, pre="", post="", err_=None, run_args=None, **kwargs):
    """
    Helper function that wraps the execution of freebsd-update command.

    orig:
        Originating function that called _wrapper().

    pre:
        String that will be prepended to freebsd-update command.

    post:
        String that will be appended to freebsd-update command.

    err_:
        Dictionary on which return codes and stout/stderr are copied.

    run_args:
        Arguments to be passed on cmd.run_all.

    kwargs:
        Parameters of freebsd-update command.
    """
    ret = ""  # the message to be returned
    cmd = _cmd(**kwargs)
    cmd_str = " ".join(list(pre, cmd, post, orig))
    if run_args and isinstance(run_args, dict):
        res = __salt__["cmd.run_all"](cmd_str, **run_args)
    else:
        res = __salt__["cmd.run_all"](cmd_str)

    if isinstance(err_, dict):  # copy return values if asked to
        for k, v in res.items():
            err_[k] = v

    if "retcode" in res and res["retcode"] != 0:
        msg = " ".join([x for x in (res["stdout"], res["stderr"]) if x])
        ret = f'Unable to run "{cmd_str}" with run_args="{run_args}". Error: {msg}'
        log.error(ret)
    else:
        try:
            ret = res["stdout"]
        except KeyError:
            log.error("cmd.run_all did not return a dictionary with a key named 'stdout'")
    return ret


def fetch(**kwargs):
    """
    .. versionadded:: 2016.3.4

    freebsd-update fetch wrapper. Based on the currently installed world and the
    configuration options set, fetch all available binary updates.

    kwargs:
        Parameters of freebsd-update command.

    CLI Example:

    .. code-block:: bash

        salt '*' freebsd-update.fetch

    """
    # fetch continues when no controlling terminal is present
    pre = ""
    post = ""
    run_args = {}
    if float(__grains__["osrelease"]) >= 10.2:
        post += "--not-running-from-cron"
    else:
        pre += " env PAGER=cat"
        run_args["python_shell"] = True
    return _wrapper("fetch", pre=pre, post=post, run_args=run_args, **kwargs)


def install(**kwargs):
    """
    .. versionadded:: 2016.3.4

    freebsd-update install wrapper. Install the most recently fetched updates or
    upgrade.

    kwargs:
        Parameters of freebsd-update command.

    CLI Example:

    .. code-block:: bash

        salt '*' freebsd-update.install

    """
    return _wrapper("install", **kwargs)


def rollback(**kwargs):
    """
    .. versionadded:: 2016.3.4

    freebsd-update rollback wrapper. Uninstalls the most recently installed
    updates.

    kwargs:
        Parameters of freebsd-update command.

    CLI Example:

    .. code-block:: bash

        salt '*' freebsd-update.rollback
    """
    return _wrapper("rollback", **kwargs)


def update(**kwargs):
    """
    .. versionadded:: 2016.3.4

    Command that simplifies freebsd-update by running freebsd-update fetch first
    and then freebsd-update install.

    kwargs:
        Parameters of freebsd-update command.

    CLI Example:

    .. code-block:: bash

        salt '*' freebsd-update.update

    """
    stdout = {}

    for mode in ("fetch", "install"):
        err_ = {}
        ret = _wrapper(mode, err_=err_, **kwargs)
        if "retcode" in err_ and err_["retcode"] != 0:
            return ret
        if "stdout" in err_:
            stdout[mode] = err_["stdout"]
    return "\n".join([f"{k}: {v}" for (k, v) in stdout.items()])


def ids(**kwargs):
    """
    .. versionadded:: 2016.3.4

    freebsd-update IDS wrapper function. Compares the system against a "known
    good" index of the installed release.

    kwargs:
        Parameters of freebsd-update command.

    CLI Example:

    .. code-block:: bash

        salt '*' freebsd-update.ids
    """
    return _wrapper("IDS", **kwargs)
