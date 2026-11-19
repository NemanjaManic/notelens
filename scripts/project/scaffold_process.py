"""Windows-only containment for finite candidate verification commands."""

import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import subprocess
import sys
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


def run_owned(command, *, cwd, env, stdout, timeout):
    """Assign a blocked launcher before releasing it; stop only that job on every exit.

    The non-inherited job handle also closes if this coordinator is terminated.
    Descendants cannot start before assignment, so failure never falls back to an
    uncontained command. No service lookup, global process scan or port kill is used.
    """
    kernel = _job_api()
    job = _checked(kernel.CreateJobObjectW(None, None))
    launcher = None
    try:
        limits = _ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway.
        _checked(kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
        launcher = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), '--child', *command],
                                    cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=stdout,
                                    stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW,
                                    close_fds=True)
        process = _checked(kernel.OpenProcess(0x0101, False, launcher.pid))  # SET_QUOTA | TERMINATE
        try:
            _checked(kernel.AssignProcessToJobObject(job, process))
        finally:
            kernel.CloseHandle(process)
        launcher.stdin.write(b'G')
        launcher.stdin.close()
        return subprocess.CompletedProcess(command, launcher.wait(timeout=timeout))
    finally:
        try:
            # Also remove descendants left after an apparently successful command.
            _checked(kernel.TerminateJobObject(job, 1))
            if launcher is not None:
                if launcher.poll() is None:
                    launcher.kill()  # Assignment may have failed; this launcher is ours.
                launcher.wait(timeout=5)
                if launcher.stdin and not launcher.stdin.closed:
                    launcher.stdin.close()
            deadline = time.monotonic() + 5
            while True:
                accounting = _Accounting()
                _checked(kernel.QueryInformationJobObject(job, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None))
                if accounting.active == 0:
                    break
                if time.monotonic() >= deadline:
                    raise RuntimeError('Owned verification job did not become empty')
                time.sleep(0.02)
        finally:
            kernel.CloseHandle(job)


if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] != '--child':
        sys.exit('Use run_owned from the candidate runner')
    if sys.stdin.buffer.read(1) != b'G':
        sys.exit('Unassigned candidate launcher')
    sys.exit(subprocess.call(sys.argv[2:], stdin=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW))
