from skipping_schoo import version
from skipping_schoo import download_schoo
from skipping_schoo import rip_audio
from skipping_schoo import transscribe
from skipping_schoo import summarize
from skipping_schoo import utils
from skipping_schoo.errors import SkippingSchooError


__version__ = version.VERSION
__all__ = [
    "version",
    "download_schoo",
    "rip_audio",
    "transscribe",
    "summarize",
    "utils",
    "SkippingSchooError"
]
