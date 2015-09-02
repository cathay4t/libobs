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

from libobs import Obs
import os
import time
import re

username = os.environ.get("OBS_USER")
password = os.environ.get("OBS_PASS")
project = os.environ.get("OBS_PROJECT")
package = os.environ.get("OBS_PKG")
git_repo = os.environ.get("OBS_GIT_REPO")
git_branch = os.environ.get("OBS_GIT_BRANCH")

file_service = """
<services>
    <service name="tar_scm">
        <param name="scm">git</param>
        <param name="url">%s</param>
        <param name="filename">libstoragemgmt</param>
        <param name="versionprefix">1.3.git</param>
        <param name="revision">%s</param>
    </service>
    <service name="recompress">
        <param name="file">*git*.tar</param>
        <param name="compression">gz</param>
    </service>
    <service name="set_version"/>
</services>
""" % (git_repo, git_branch)

if not (username and password and project and package):
    print "Please defined these environment variables:"
    print "    OBS_USER OBS_PASS OBS_PROJECT OBS_PKG"
    exit(1)

obs_obj = Obs(username, password, project)


print "Uploading _service file"
obs_obj.file_upload(package, "_service", file_service,
                    "using %s repo %s branch" % (git_repo, git_branch))

"""
print "Invoking service remote run for project: '%s' for package '%s'" % \
         (project, package)
obs_obj.service_remoterun(package)
"""

while(1):
    status, reason = obs_obj.project_status()
    if status == Obs.STATUS_OK:
        print "Build for remote run finished"
        exit(0)

    if status == Obs.STATUS_FAILED:
        print "Build failed: %s" % reason
        exit(1)


    if status == Obs.STATUS_BUILDING:
        print "Still building: %s" % reason

    print "Check again in 5 seconds"
    time.sleep(5)
    continue
