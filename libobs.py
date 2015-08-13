#!/usr/bin/env python2
#
# Copyright (C) 2015 Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Gris Ge <fge@redhat.com>

import re
import urllib2
from cookielib import CookieJar


_HTTP_STATUS_OK = 200
_HTTP_STATUS_UNAUTHORIZED = 401


class ObsError(Exception):
    """
    Error raised by Obs class.
    The ObsError object has two properties:
        code (integer):
            ObsError.LIB_BUG
                Please report a bug to us.
            ObsError.BAD_AUTH
                Invalid username or password.
            ObsError.EMPTY_PROJECT
                Provided project has no pacakge or repository configured.
        message (string):
            Human friendly error message.
    """
    LIB_BUG = 1
    BAD_AUTH = 2
    EMPTY_PROJECT = 3

    def __init__(self, code, message, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
        self.code = code
        self.message = message


def _handle_http_errors(method):
    """
    Convert urllib2.HTTPError to ObsError
    """
    def wrapper(*args, **kargs):
        try:
            return method(*args, **kargs)
        except urllib2.HTTPError as http_err:
            http_err_code = http_err.getcode()
            if http_err_code == _HTTP_STATUS_UNAUTHORIZED:
                raise ObsError(
                    ObsError.BAD_AUTH, "Invalid username and password")
            raise ObsError(
                ObsError.LIB_BUG,
                "URL %s got http error %d: %s" %
                (http_err.geturl(), http_err_code, str(http_err)))
    return wrapper


def _parse_build_status(out_str):
    """
    Due to XML vulnerabilities of python modules,
    https://docs.python.org/2/library/xml.html#xml-vulnerabilities
    use regex instead.

    Return a list in this data layout:
        [
            {
                project = "home:cathay4t:misc_fedora",
                repository = "Fedora_20",
                arch = "i586",
                code = "published",
                state = "published",
                statuscount = {
                    succeeded = 1,
                    failed = 0,
                }
            }
        ]
    """
    rc_list = list()
    tmp_dict = dict()
    regex_status_count = re.compile(
        'statuscount code="(?P<code>[a-z]+)" count="(?P<count>[0-9]+)"')
    for line in out_str.split("\n"):
        line = line.lstrip()

        if line.startswith("<result "):
            # Remove heading and tailing < >
            line = line[1:-1]
            for key_value in line.split(" "):
                tmp_l = key_value.split("=")
                if len(tmp_l) == 2:
                    value = tmp_l[1]
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    tmp_dict[tmp_l[0]] = value
            tmp_dict["statuscount"] = {}
        elif line.startswith("<statuscount "):
            regex_result = regex_status_count.search(line)
            if regex_result:
                tmp_dict["statuscount"][regex_result.group('code')] = \
                    regex_result.group('count')

        elif line == "</result>":
            if len(tmp_dict) != 0:
                rc_list.append(tmp_dict)
                tmp_dict = dict()

    return rc_list


class Obs(object):
    """
    Library for OpenSuSE Build Service build management using
    OBS REST API at open-build-service project '/docs/api/api/api.txt'.
    """
    API_URL = "https://api.opensuse.org"
    STATUS_OK = 0
    STATUS_FAILED = 1
    STATUS_BUILDING = 2

    _BUILD_STATUS_FAILED_LIST = ['failed', 'unresolvable', 'broken']
    _BUILD_STATUS_BUILDING_LIST = ['scheduled', 'building', 'dispatching',
                                   'blocked', 'signing', 'finished',
                                   'unknown']

    def __init__(self, username, password, project, apiurl=None):
        """
        Define apiurl if you are not using public openSuSE build service(
        https://build.opensuse.org).
        """
        self.username = username
        self.password = password
        self.project = project
        if apiurl is None:
            self.apiurl = Obs.API_URL
        else:
            self.apiurl = apiurl

        cookie_jar = CookieJar()
        pass_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        pass_mgr.add_password(None, self.apiurl, username, password)

        self._opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(cookie_jar),
            urllib2.HTTPBasicAuthHandler(pass_mgr))

    @_handle_http_errors
    def service_remoterun(self, package):
        """
        Usage:
            Trigger a re-run on the server side via:
                POST /source/<project_name>/<package_name>?cmd=runservice
                    Post with empty data.
        Args:
            package (string)
                The package name to invoke "service remoterun".
        Return:
            void
                Raise exception when error.
        """
        url = "%s/source/%s/%s?cmd=runservice" % (self.apiurl, self.project,
                                                  package)
        rc_obj = self._opener.open(url, data="")
        http_code = rc_obj.getcode()
        if http_code != _HTTP_STATUS_OK:
            raise ObsError(
                http_code,
                "service_remoterun() failed with http error "
                "code %d, message %s" % (http_code, rc_obj.read()))

    @_handle_http_errors
    def project_status(self):
        """
        Usage:
            Check overall status of this project via:
                GET /build/<project_name>/_result?view=summary
        Args:
            void
        Return:
            (status, reason)
                status (integer)
                    Obs.STATUS_OK
                        Build finished and repo is ready.
                    Obs.STATUS_FAILED
                        At least one package is failed.
                    Obs.STATUS_BUILDING
                        At least one package is still waiting, building or
                        signing or publishing repo. No package has any
                        failure yet. This is an intermediate state, it will
                        lead to Obs.STATUS_OK or Obs.STATUS_FAILED.
                    Obs.STATUS_UNKNOWN
                reason (string)
                    Human friendly message when not Obs.STATUS_OK.
                    Example:
                        Fedora_21 x86_64 has 2 packages in building state.
        """
        url = "%s/build/%s/_result?view=summary" % (self.apiurl, self.project)
        out_str = self._opener.open(url).read()
        status = Obs.STATUS_OK
        reason = ""
        bs_list = []
        if not out_str:
            raise ObsError(
                ObsError.LIB_BUG,
                "project_status(): Got empty string return from %s" % url)

        bs_list = _parse_build_status(out_str)
        if len(bs_list) == 0:
            raise ObsError(
                ObsError.EMPTY_PROJECT,
                "Provided project has not repository or package")

        for bs in bs_list:
            if bs['state'] != 'published' and bs['state'] != 'building':
                status = Obs.STATUS_BUILDING
                reason += "%s %s repo is publishing. " % (
                    bs['repository'], bs['arch'])

            sc = bs['statuscount']
            for building_key in Obs._BUILD_STATUS_BUILDING_LIST:
                if building_key in sc.keys():
                    status = Obs.STATUS_BUILDING
                    reason += "%s %s has %s packages in %s state. " % \
                              (bs['repository'], bs['arch'],
                               sc[building_key], building_key)

        for bs in bs_list:
            sc = bs['statuscount']
            for failed_key in Obs._BUILD_STATUS_FAILED_LIST:
                if failed_key in sc.keys():
                    status = Obs.STATUS_BUILDING
                    reason += "%s %s has %s packages in %s state. " % \
                              (bs['repository'], bs['arch'],
                               sc[failed_key], failed_key)

        reason = reason.rstrip()
        return (status, reason)
