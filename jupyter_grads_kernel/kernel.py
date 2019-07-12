from subprocess import Popen
from ipykernel.kernelbase import Kernel


class RealTimeGrads(Popen):
    """
    GrADS as a background process
    """

    def __init__(self, grads="grads", mode="landscape", stdout=None, stderr=None, display=True):
        """
        Start grads
        :param grads: PATH to GrADS binary
        :param mode: landscape or portrait; default is landscape
        """
        from subprocess import PIPE
        from queue import Queue
        from threading import Thread
        import sys

        opts = ["-b"]  # what is -u option? (http://cola.gmu.edu/grads/gadoc/start.html)
        if mode == "landscape":
            opts.append("-l")
        elif mode == "portrait":
            opts.append("-p")
        else:
            raise ValueError(
                "arg mode must be 'landscape' or 'portrait'. not {}".format(mode)
            )
        cmd = grads + " " + " ".join(opts)

        super(RealTimeGrads, self).__init__(
            cmd,
            stdout=PIPE,
            stderr=PIPE,
            stdin=PIPE,
            shell=True,
            bufsize=0
        )

        self._write_to_stdout = stdout
        if stdout is None:
            self._write_to_stdout = lambda x: print(x)
        self._write_to_stderr = stderr
        if stderr is None:
            self._write_to_stderr = lambda x: print(x)

        self._stdout_queue = Queue()
        self._stdout_thread = Thread(
            target=RealTimeGrads._enqueue_output,
            args=(self.stdout, self._stdout_queue)
        )
        self._stdout_thread.daemon = True
        self._stdout_thread.start()

        self._stderr_queue = Queue()
        self._stderr_thread = Thread(
            target=RealTimeGrads._enqueue_output,
            args=(self.stderr, self._stderr_queue)
        )
        self._stderr_thread.daemon = True
        self._stderr_thread.start()


        outtxt, errtxt = self.read_all_outputs()
        if display:
            print(outtxt)
            print(errtxt)
        return

    @staticmethod
    def _enqueue_output(stream, queue):
        """
        Add chunks of data from a stream to a queue until the stream is empty.
        """
        for line in iter(lambda: stream.read(4096), b''):
            queue.put(line)
        stream.close()

    @staticmethod
    def _read_all_from_queue(queue):
        """
        read all contents from queue
        :param queue:
        :return:
        """
        res = b''
        size = queue.qsize()
        while size != 0:
            res += queue.get_nowait()
            size -= 1
        return res.decode()

    def read_stdout(self):
        """
        read stdout from last call to the latest
        :return:
        """
        return self._read_all_from_queue(self._stdout_queue)

    def read_stderr(self):
        """
        read stderr from last call to the latest
        :return:
        """
        return self._read_all_from_queue(self._stderr_queue)

    def read_all_outputs(self):
        """
        continuously read all outputs until grads becomes stand-by state again
        :return: stdout, stderr
        """
        outtxt = ""
        errtxt = ""
        while self.poll() is None:
            outtxt += self.read_stdout()
            errtxt += self.read_stderr()

            if "ga->" in outtxt:
                if outtxt[:4] == "ga->" or "\nga->" in outtxt:
                    outtxt = outtxt[:outtxt.index("ga->")]
                    break
        return outtxt, errtxt

    def flush_all_outputs(self):
        self.read_all_outputs()
        return

    def write_outputs(self):
        """
        Write the available content from stdin and stderr where specified when the instance was created
        :return:
        """
        stdout_contents = self.read_stdout()
        if stdout_contents:
            self._write_to_stdout(stdout_contents)
        stderr_contents = self.read_stderr()
        if stderr_contents:
            self._write_to_stderr(stderr_contents)

    def write_all_outputs(self):
        """
        continuously write the available content from stdin and stderr until grads becomes stand-by state again
        :return:
        """
        outtxt, errtxt = self.read_all_outputs()

        if len(outtxt.strip()) > 0:
            self._write_to_stdout(outtxt.strip() + "\n")
        if len(errtxt.strip()) > 0:
            self._write_to_stdout(errtxt.strip() + "\n")
        return

    def exec_ga_cmd(self, cmd, display=True):
        """
        execute grads command
        :param cmd:
        :param display:
        :return:
        """
        _cmd = cmd + "\n"
        self.stdin.write(_cmd.encode())
        if display:
            self.write_all_outputs()
        return

    def savefig(self, f):
        self.exec_ga_cmd("gxprint {}".format(f), display=False)
        self.flush_all_outputs()
        return


class GradsKernel(Kernel):
    implementation = 'jupyter_grads_kernel'
    implementation_version = '0.1.1b'
    language = 'GrADS'
    language_version = 'GrADS2'
    language_info = {'name': 'grads',
                     'mimetype': 'text/plain',
                     'file_extension': 'ga'}
    banner = "GrADS kernel"

    display_data_size_default = (400, 280)

    def __init__(self, *args, **kwargs):
        super(GradsKernel, self).__init__(*args, **kwargs)
        self.grads = RealTimeGrads(
            stdout=self._write_to_stdout,
            stderr=self._write_to_stderr
        )
        self.display_data_size = self.display_data_size_default
        return

    def _write_to_stdout(self, contents):
        self.send_response(self.iopub_socket, 'stream', {'name': 'stdout', 'text': contents})

    def _write_to_stderr(self, contents):
        self.send_response(self.iopub_socket, 'stream', {'name': 'stderr', 'text': contents})

    def _create_jupyter_png(self):
        """
        return a base64-encoded PNG from current grads
        :return: png
        """
        from io import BytesIO
        from tempfile import NamedTemporaryFile
        import os
        import urllib
        import base64

        tmpfile = NamedTemporaryFile(suffix=".png", delete=False)
        tmpfile.close()
        try:
            self.grads.savefig(tmpfile.name)
            with open(tmpfile.name, "rb") as f:
                bfig = BytesIO(f.read())
            return urllib.parse.quote(
                base64.b64encode(bfig.getvalue())
            )

        finally:
            if os.path.exists(tmpfile.name):
                os.remove(tmpfile.name)

    def _send_display(self):
        fig = self._create_jupyter_png()
        self.send_response(
            self.iopub_socket,
            "display_data",
            {
                # "source": "kernel",
                "data": {"image/png": fig},
                "metadata": {
                    "image/png": {
                        "width": self.display_data_size[0],
                        "height": self.display_data_size[1]
                    }
                }
            }
        )
        return

    def _exe_script(self, s):
        from tempfile import NamedTemporaryFile
        import os

        fgs = NamedTemporaryFile(mode="w", suffix=".gs", delete=False)
        fgs.write(s)
        fgs.close()
        self.grads.exec_ga_cmd("run {}".format(fgs.name))
        os.remove(fgs.name)
        return

    def set_display_size(self, cmds):
        try:
            if cmds[1] == "default":
                self.display_data_size = self.display_data_size_default
            else:
                x = int(cmds[1])
                y = int(cmds[2])
                self.display_data_size = (x, y)

        except (ValueError, IndexError) as e:
            self._write_to_stderr("Invalid format for *%display_size")
        
        return

    @staticmethod
    def _split_magic_line(line):
        m = map(lambda x: x.strip(), line.split(" "))
        return [x for x in m if len(x) > 0]

    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):

        drawn = False
        script = False
        script_s = ""
        for _line in code.split("\n"):
            line = _line.strip()

            if line.startswith("*%"):
                cmds = self._split_magic_line(line)

                if cmds[0] == "*%script":
                    script = True

                if cmds[0] == "*%display":
                    drawn = True

                if cmds[0] == "*%display_size":
                    self.set_display_size(cmds)

            if script:
                script_s += line + "\n"

            elif line.startswith("*%"):
                pass

            else:
                self.grads.exec_ga_cmd(line)
                if "d " == line[:2] or "display" == line[:7]:
                    drawn = True

        if script:
            self._exe_script(script_s)

        # else:
        if drawn:
            self._send_display()

        return {'status': 'ok', 'execution_count': self.execution_count, 'payload': [], 'user_expressions': {}}

