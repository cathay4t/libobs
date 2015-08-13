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

username = os.environ.get("OBS_USER")
password = os.environ.get("OBS_PASS")
project = os.environ.get("OBS_PROJECT")
package = os.environ.get("OBS_PKG")

if not (username and password and project and package):
    print "Please defined these environment variables:"
    print "    OBS_USER OBS_PASS OBS_PROJECT OBS_PKG"
    exit(1)

obs_obj = Obs(username, password, project)

print "Invoking service remote run for project: '%s' for package '%s'" % \
    (project, package)
obs_obj.service_remoterun(package)

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
