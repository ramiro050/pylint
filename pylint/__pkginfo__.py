# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/master/COPYING

from typing import Optional

__version__ = "2.8.0"
# For an official release, use 'alpha_version = False' and 'dev_version = None'
alpha_version: bool = False  # Release will be an alpha version if True (ex: '1.2.3a6')
dev_version: Optional[int] = 1

if dev_version is not None:
    if alpha_version:
        __version__ += f"a{dev_version}"
    else:
        __version__ += f".dev{dev_version}"
