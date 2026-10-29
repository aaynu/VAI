from __future__ import annotations

import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# --- DPI Constants ---
DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)

# --- Window Extended Styles ---
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000

# --- SetWindowPos & ShowWindow Flags ---
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020
HWND_TOPMOST = ctypes.c_void_p(-1)

SW_HIDE = 0
SW_SHOWNOACTIVATE = 4

# --- Hotkey Constants ---
WM_HOTKEY = 0x0312
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000

VK_F7 = 0x76   # Ctrl+Shift+F7  -> Cycle Target Monitor
VK_F8 = 0x77   # Ctrl+Shift+F8  -> Toggle Show/Hide (True SW_HIDE for DWM DirectFlip)
VK_F9 = 0x78   # Ctrl+Shift+F9  -> Toggle Calibration Mode (Lock/Unlock)
VK_F10 = 0x79  # Ctrl+Shift+F10 -> Cycle Agent Preset
VK_R = 0x52    # Ctrl+Shift+R   -> Toggle 3-Point Role Filter Waypoint
VK_Q = 0x51    # Ctrl+Shift+Q   -> Clean Exit

HOTKEY_CYCLE_MONITOR = 1
HOTKEY_TOGGLE_VISIBILITY = 2
HOTKEY_TOGGLE_CALIBRATION = 3
HOTKEY_CYCLE_AGENT = 4
HOTKEY_TOGGLE_ROLE_POINT = 5
HOTKEY_EXIT = 6

# --- Process Priority & EcoQoS Constants ---
IDLE_PRIORITY_CLASS = 0x00000040
ProcessPowerThrottling = 4
PROCESS_POWER_THROTTLING_CURRENT_VERSION = 1
PROCESS_POWER_THROTTLING_EXECUTION_SPEED = 0x1


class PROCESS_POWER_THROTTLING_STATE(ctypes.Structure):
    _fields_ = [
        ("Version", wintypes.ULONG),
        ("ControlMask", wintypes.ULONG),
        ("StateMask", wintypes.ULONG),
    ]


class SYSTEM_INFO(ctypes.Structure):
    _fields_ = [
        ("wProcessorArchitecture", wintypes.WORD),
        ("wReserved", wintypes.WORD),
        ("dwPageSize", wintypes.DWORD),
        ("lpMinimumApplicationAddress", ctypes.c_void_p),
        ("lpMaximumApplicationAddress", ctypes.c_void_p),
        ("dwActiveProcessorMask", ctypes.c_size_t),
        ("dwNumberOfProcessors", wintypes.DWORD),
        ("dwProcessorType", wintypes.DWORD),
        ("dwAllocationGranularity", wintypes.DWORD),
        ("wProcessorLevel", wintypes.WORD),
        ("wProcessorRevision", wintypes.WORD),
    ]


LONG_PTR = ctypes.c_longlong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_long

user32.SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
user32.SetProcessDpiAwarenessContext.restype = wintypes.BOOL

user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetWindowLongPtrW.restype = LONG_PTR

user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, LONG_PTR]
user32.SetWindowLongPtrW.restype = LONG_PTR

user32.SetWindowPos.argtypes = [
    wintypes.HWND,
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
]
user32.SetWindowPos.restype = wintypes.BOOL

user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL

user32.RegisterHotKey.argtypes = [
    wintypes.HWND,
    ctypes.c_int,
    wintypes.UINT,
    wintypes.UINT,
]
user32.RegisterHotKey.restype = wintypes.BOOL

user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
user32.UnregisterHotKey.restype = wintypes.BOOL

kernel32.GetCurrentProcess.argtypes = []
kernel32.GetCurrentProcess.restype = wintypes.HANDLE

kernel32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
kernel32.SetPriorityClass.restype = wintypes.BOOL

kernel32.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
kernel32.SetProcessAffinityMask.restype = wintypes.BOOL

kernel32.SetProcessInformation.argtypes = [
    wintypes.HANDLE,
    ctypes.c_int,
    ctypes.c_void_p,
    wintypes.DWORD,
]
kernel32.SetProcessInformation.restype = wintypes.BOOL

kernel32.GetSystemInfo.argtypes = [ctypes.POINTER(SYSTEM_INFO)]
kernel32.GetSystemInfo.restype = None


def enable_per_monitor_dpi_v2() -> None:
    """Must be called before QApplication is instantiated."""
    if not user32.SetProcessDpiAwarenessContext(
        DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
    ):
        user32.SetProcessDPIAware()


def apply_efficiency_scheduler_profile(prefer_last_n_cores: int = 4) -> None:
    """Pins process to Efficiency Cores (E-Cores) and enables Windows 11 EcoQoS."""
    h_proc = kernel32.GetCurrentProcess()
    kernel32.SetPriorityClass(h_proc, IDLE_PRIORITY_CLASS)

    throttling = PROCESS_POWER_THROTTLING_STATE(
        Version=PROCESS_POWER_THROTTLING_CURRENT_VERSION,
        ControlMask=PROCESS_POWER_THROTTLING_EXECUTION_SPEED,
        StateMask=PROCESS_POWER_THROTTLING_EXECUTION_SPEED,
    )
    kernel32.SetProcessInformation(
        h_proc,
        ProcessPowerThrottling,
        ctypes.byref(throttling),
        ctypes.sizeof(throttling),
    )

    sys_info = SYSTEM_INFO()
    kernel32.GetSystemInfo(ctypes.byref(sys_info))
    total_cores = sys_info.dwNumberOfProcessors

    if total_cores > prefer_last_n_cores:
        mask = 0
        for idx in range(total_cores - prefer_last_n_cores, total_cores):
            mask |= 1 << idx
        mask &= sys_info.dwActiveProcessorMask
        if mask != 0:
            kernel32.SetProcessAffinityMask(h_proc, mask)


def set_overlay_window_styles(hwnd: int, click_through: bool = True) -> None:
    """Applies or removes WS_EX_TRANSPARENT and WS_EX_NOACTIVATE on the target HWND."""
    ex_style = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
    base_flags = WS_EX_TOPMOST | WS_EX_LAYERED | WS_EX_TOOLWINDOW

    if click_through:
        new_style = ex_style | base_flags | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE
    else:
        new_style = (ex_style | base_flags) & ~WS_EX_TRANSPARENT & ~WS_EX_NOACTIVATE

    ctypes.set_last_error(0)
    user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, new_style)

    swp_flags = SWP_NOMOVE | SWP_NOSIZE | SWP_FRAMECHANGED
    if click_through:
        swp_flags |= SWP_NOACTIVATE
    user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, swp_flags)


def show_overlay_no_activate(hwnd: int) -> None:
    """Shows the HWND without stealing focus from Valorant."""
    user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)


def hide_overlay_from_dwm(hwnd: int) -> None:
    """Completely hides the HWND so DWM restores hardware Independent Flip (iFlip)."""
    user32.ShowWindow(hwnd, SW_HIDE)
