import subprocess

from youtube_dl.postprocessor.common import PostProcessor
from youtube_dl.compat import compat_shlex_quote

class PythonExecAfterDownloadPP(PostProcessor):
    def __init__(self, downloader, exec_cmd):
        super(PythonExecAfterDownloadPP, self).__init__(downloader)
        self.exec_cmd = exec_cmd

    def run(self, information):
        cmd = self.exec_cmd
        cmd(information['filepath'])

        return [], information
