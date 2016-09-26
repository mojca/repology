#!/usr/bin/env python3
#
# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
#
# This file is part of repology
#
# repology is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# repology is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with repology.  If not, see <http://www.gnu.org/licenses/>.

import time
import jinja2
from .util import VersionCompare

def SpanTrim(str, maxlength):
    if len(str) <= maxlength:
        return str

    return "<span title=\"%s\">%s...</span>" % (str, str[0:maxlength])

class ReportProducer:
    def __init__(self):
        env = jinja2.Environment(
            loader = jinja2.PackageLoader('repology', 'templates'),
            lstrip_blocks = True,
            trim_blocks = True,
        )
        env.filters["spantrim"] = SpanTrim

        self.env = env

    def Render(self, template, packages, reponames):
        template = self.env.get_template(template)

        template_args = {
            'reponames': reponames,
            'repositories': {},
            'packages': [],
            'gentime': time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
        }

        for reponame in reponames:
            template_args['repositories'][reponame] = {
                'statistics': {
                    'total': 0,
                    'lonely': 0,
                    'good': 0,
                    'multi': 0,
                    'bad': 0,
                    'ignore': 0
                }
            }

        for pkgname in sorted(packages.keys()):
            metapackage = packages[pkgname]

            bestversion, _, _ = metapackage.GetMaxVersion()

            template_package = {
                'name': pkgname,
                'byrepo': {}
            }

            for reponame in metapackage.GetRepos():
                # packages for this repository
                repopackages = metapackage.Get(reponame)

                # determine versions
                repominversion, repomaxversion = metapackage.GetVersionRangeForRepo(reponame)

                versionclass = 'bad'
                if metapackage.GetNumRepos() == 1:
                    versionclass = 'lonely'
                elif bestversion is None:
                    versionclass = 'good'
                elif VersionCompare(repomaxversion, bestversion) > 0: # due to ignore
                    versionclass = 'ignore'
                elif VersionCompare(repomaxversion, bestversion) >= 0:
                    if VersionCompare(repominversion, bestversion) == 0:
                        versionclass = 'good'
                    else:
                        versionclass = 'multi'

                template_package['byrepo'][reponame] = {
                    'version': repomaxversion,
                    'class': versionclass,
                    'numpackages': len(repopackages)
                }

                template_args['repositories'][reponame]['statistics']['total'] += 1
                template_args['repositories'][reponame]['statistics'][versionclass] += 1

            template_args['packages'].append(template_package)

        return template.render(template_args)