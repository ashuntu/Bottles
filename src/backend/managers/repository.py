# repository.py
#
# Copyright 2020 brombinmirko <send@mirko.pm>
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

import os
import urllib.request
from typing import Union, NewType

from bottles.backend.logger import Logger # pyright: reportMissingImports=false
from bottles.backend.repos.dependency import DependencyRepo
from bottles.backend.repos.component import ComponentRepo
from bottles.backend.repos.installer import InstallerRepo
from bottles.params import VERSION_NUM

logging = Logger()

# Define custom types for better understanding of the code
BottleConfig = NewType('BottleConfig', dict)


class RepositoryManager:

    __repositories = {
        "components": {
            "url": "https://raw.githubusercontent.com/bottlesdevs/components/main/",
            "index": "",
            "cls": ComponentRepo
        },
        "dependencies": {
            "url": "https://raw.githubusercontent.com/bottlesdevs/dependencies/main/",
            "index": "",
            "cls": DependencyRepo
        },
        "installers": {
            "url": "https://raw.githubusercontent.com/bottlesdevs/programs/main/",
            "index": "",
            "cls": InstallerRepo
        }
    }

    def __init__(self):
        self.__check_locals()
        self.__get_index()
    
    def get_repo(self, name: str):
        if name in self.__repositories:
            repo = self.__repositories[name]
            return repo["cls"](repo["url"], repo["index"])
        
        logging.error(f"Repository {name} not found")
    
    def __check_locals(self):
        _locals = {}
        if "LOCAL_COMPONENTS" in os.environ:
            _locals["components"] = os.environ["LOCAL_COMPONENTS"]
        if "LOCAL_DEPENDENCIES" in os.environ:
            _locals["dependencies"] = os.environ["LOCAL_DEPENDENCIES"]
        if "LOCAL_INSTALLERS" in os.environ:
            _locals["installers"] = os.environ["LOCAL_INSTALLERS"]

        if not _locals:
            return

        for repo in self.__repositories:
            if repo not in _locals:
                continue
            _path = _locals[repo]
            if os.path.exists(_path):
                self.__repositories[repo]["url"] = f"file://{_path}/"
                logging.info(f"Using local {repo} repository at {_path}")
            else:
                logging.error(f"Local {repo} path does not exist: {_path}")
    
    def __get_index(self):
        for repo, data in self.__repositories.items():
            __index = os.path.join(data["url"], f"{VERSION_NUM}.yml")
            __fallback = os.path.join(data["url"], "index.yml")

            try:
                with urllib.request.urlopen(__index) as res:
                    data["index"] = __index
            except:
                try:
                    with urllib.request.urlopen(__fallback) as res:
                        data["index"] = __fallback
                except:
                    logging.error(f"Could not get index for {repo} repository")
                    continue
        