"""Windows-only containment for local project processes."""

from contextlib import contextmanager
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import subprocess
import sys
from threading import Lock, Timer
import time


def _job_api():
    if os.name != 'nt':
        raise OSError('Candidate process containment requires Windows')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    for name, arguments, result in (
        ('CreateJobObjectW', [ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
        ('SetInformationJobObject', [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL),
        ('QueryInformationJobObject', [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p], wintypes.BOOL),
        ('OpenProcess', [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
        ('AssignProcessToJobObject', [wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
        ('TerminateJobObject', [wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
        ('CloseHandle', [wintypes.HANDLE], wintypes.BOOL),
    ):
        function = getattr(kernel, name)
        function.argtypes, function.restype = arguments, result
    return kernel


class _BasicLimits(ctypes.Structure):
    _fields_ = [('process_time', ctypes.c_int64), ('job_time', ctypes.c_int64),
                ('flags', wintypes.DWORD), ('minimum_working_set', ctypes.c_size_t),
                ('maximum_working_set', ctypes.c_size_t), ('active_process_limit', wintypes.DWORD),
                ('affinity', ctypes.c_size_t), ('priority', wintypes.DWORD), ('scheduling', wintypes.DWORD)]


class _IoCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in ('read_ops', 'write_ops', 'other_ops', 'read_bytes', 'write_bytes', 'other_bytes')]


class _ExtendedLimits(ctypes.Structure):
    _fields_ = [('basic', _BasicLimits), ('io', _IoCounters),
                ('process_memory', ctypes.c_size_t), ('job_memory', ctypes.c_size_t),
                ('peak_process_memory', ctypes.c_size_t), ('peak_job_memory', ctypes.c_size_t)]


class _Accounting(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int64) for name in ('user_time', 'kernel_time', 'period_user_time', 'period_kernel_time')] + [
        (name, wintypes.DWORD) for name in ('page_faults', 'total', 'active', 'terminated')]


def _checked(result):
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())
    return result


class ProcessJob:
    def __init__(self, kernel, handle, deadline):
        self.kernel, self.handle, self.deadline = kernel, handle, deadline
        self.lock = Lock()
        self.expired = False
        self.stopped = False
        self.drained = False
        self.stop_error = None
        self.launchers = []

    def start(self, command, *, cwd, env, stdout):
        # The launcher can only read its gate until assigned to the job.
        launcher = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), '--child', *command],
                                    cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=stdout,
                                    stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW,
                                    close_fds=True)
        try:
            with self.lock:
                if self.stopped or (self.deadline is not None and time.monotonic() >= self.deadline):
                    raise TimeoutError('The process job deadline expired.')
                process = _checked(self.kernel.OpenProcess(0x0101, False, launcher.pid))
                try:
                    _checked(self.kernel.AssignProcessToJobObject(self.handle, process))
                finally:
                    self.kernel.CloseHandle(process)
                self.launchers.append(launcher)
                launcher.stdin.write(b'G')
                launcher.stdin.flush()
            return launcher
        except BaseException:
            if launcher.poll() is None:
                launcher.kill()
            launcher.wait(timeout=5)
            raise
        finally:
            launcher.stdin.close()

    def stop(self, *, expired=False):
        with self.lock:
            if self.stopped:
                return
            self.expired |= expired or (self.deadline is not None and time.monotonic() >= self.deadline)
            _checked(self.kernel.TerminateJobObject(self.handle, 1))
            self.stopped = True

    def expire(self):
        try:
            self.stop(expired=True)
        except OSError as error:
            self.stop_error = error

    def wait(self):
        deadline = time.monotonic() + 5
        while True:
            accounting = _Accounting()
            _checked(self.kernel.QueryInformationJobObject(self.handle, 1, ctypes.byref(accounting),
                                                           ctypes.sizeof(accounting), None))
            if accounting.active == 0:
                for launcher in self.launchers:
                    launcher.wait(timeout=1)
                self.drained = True
                return
            if time.monotonic() >= deadline:
                raise RuntimeError('Owned verification job did not become empty')
            time.sleep(0.02)


@contextmanager
def owned_job(deadline=None):
    """Own all spawned descendants until cleanup or a monotonic deadline."""
    kernel = _job_api()
    handle = _checked(kernel.CreateJobObjectW(None, None))
    job = ProcessJob(kernel, handle, deadline)
    timer = None
    try:
        limits = _ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway.
        _checked(kernel.SetInformationJobObject(handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
        if deadline is not None:
            timer = Timer(max(0, deadline - time.monotonic()), job.expire)
            timer.daemon = True
            timer.start()
        try:
            yield job
        finally:
            job.stop()
            job.wait()
    finally:
        try:
            if timer is not None:
                timer.cancel()
                timer.join()
        finally:
            kernel.CloseHandle(handle)
        if job.stop_error is not None:
            raise job.stop_error


@contextmanager
def owned_process(command, *, cwd, env, stdout):
    with owned_job() as job:
        yield job.start(command, cwd=cwd, env=env, stdout=stdout)


def run_owned(command, *, cwd, env, stdout, timeout):
    with owned_process(command, cwd=cwd, env=env, stdout=stdout) as launcher:
        return subprocess.CompletedProcess(command, launcher.wait(timeout=timeout))


if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] != '--child':
        sys.exit('Use run_owned from the candidate runner')
    if sys.stdin.buffer.read(1) != b'G':
        sys.exit('Unassigned candidate launcher')
    sys.exit(subprocess.call(sys.argv[2:], stdin=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW))
