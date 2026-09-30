"""
Find a window using pywinauto, set focus to it, then press a key combination.
All configurations are read from tasks.toml.

Requirements:
    pip install pyautogui pywinauto tomli

Usage:
    python focus_and_press.py ms-teams share start --pid 12345
    python focus_and_press.py ms-teams share end --pid 12345
    python focus_and_press.py wecom share start --pid 67890
"""

import pyautogui
import time
import tomli
import os
import subprocess
from pywinauto import Application
from pywinauto.application import ProcessNotFoundError


def click_button_by_text(pid, button_text, case_sensitive=False, exact_match=True):
    """
    Finds and clicks a button by its text.

    Args:
        pid: Process ID of the target application
        button_text: Text to search for in buttons
        case_sensitive: Whether to match case exactly
        exact_match: If True, requires exact match. If False, allows partial match.

    Returns:
        True if button was found and clicked, False otherwise
    """
    try:
        print(f"Connecting to PID: {pid}...")
        app = Application(backend="uia").connect(process=pid)

        windows = app.windows()
        if not windows:
            print("No windows found!")
            return False

        print(f"Found {len(windows)} window(s)")
        print(f"Searching for button with text: '{button_text}'")
        print("=" * 80)

        # Prepare search text
        search_text = button_text if case_sensitive else button_text.lower()

        for i, window in enumerate(windows):
            window_title = window.window_text()
            print(f"\n[Window {i+1}: '{window_title}']")

            try:
                descendants = window.descendants()
                print(f"Searching {len(descendants)} controls...")

                for ctrl in descendants:
                    try:
                        ctrl_type = ctrl.element_info.control_type

                        # Look for clickable controls
                        if ctrl_type in [
                            "Button",
                            "MenuItem",
                            "Hyperlink",
                            "SplitButton",
                            "Text",
                            "CheckBox",
                        ]:
                            ctrl_text = ctrl.window_text()
                            ctrl_name = (
                                ctrl.element_info.name
                                if hasattr(ctrl.element_info, "name")
                                else ""
                            )

                            # Check both text and name
                            texts_to_check = [ctrl_text, ctrl_name]

                            for text in texts_to_check:
                                if not text:
                                    continue

                                compare_text = text if case_sensitive else text.lower()

                                # Check for match
                                match_found = False
                                if exact_match:
                                    match_found = compare_text == search_text
                                else:
                                    match_found = search_text in compare_text

                                if match_found:
                                    print(f"\n✓ Found matching button!")
                                    print(f"  Type: {ctrl_type}")
                                    print(f"  Text: {ctrl_text}")
                                    print(f"  Name: {ctrl_name}")
                                    print(f"  Window: {window_title}")

                                    # Set focus to window first using the focus_window helper
                                    print(f"\nSetting focus to window...")
                                    window_info = {
                                        "window": window,
                                        "hwnd": (
                                            window.handle
                                            if hasattr(window, "handle")
                                            else None
                                        ),
                                        "title": window_title,
                                    }
                                    if not focus_window(window_info):
                                        print(
                                            f"⚠ Could not set window focus, attempting to click anyway..."
                                        )

                                    # Set focus to control before clicking
                                    print(f"\nSetting focus to control...")
                                    try:
                                        ctrl.set_focus()
                                        print("✓ Control focus set successfully!")
                                    except Exception as focus_error:
                                        print(
                                            f"⚠ Could not set control focus: {focus_error}"
                                        )

                                    # Try to click
                                    print(f"\nAttempting to click...")
                                    try:
                                        ctrl.click_input()
                                        print("✓ Button clicked successfully!")
                                        return True
                                    except Exception as click_error:
                                        print(f"✗ Click failed: {click_error}")
                                        print("Trying alternative click method...")
                                        try:
                                            ctrl.click()
                                            print(
                                                "✓ Button clicked successfully (alternative method)!"
                                            )
                                            return True
                                        except Exception as alt_error:
                                            print(
                                                f"✗ Alternative click also failed: {alt_error}"
                                            )
                                            return False

                    except Exception:
                        continue

            except Exception as e:
                print(f"Error processing window: {e}")

        print("\n" + "=" * 80)
        print(f"✗ No button found with text: '{button_text}'")
        return False

    except ProcessNotFoundError:
        print(f"Error: Process {pid} not found!")
        return False
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def load_combo_config(config_file="tasks.toml"):
    """
    Load combo configuration from TOML file.

    Args:
        config_file: Path to tasks.toml file

    Returns:
        Dictionary with combo configurations
    """
    if not os.path.exists(config_file):
        return None

    try:
        with open(config_file, "rb") as f:
            config = tomli.load(f)
        return config
    except Exception as e:
        print(f"Error loading config file: {e}")
        return None


def find_windows_by_title(title, pid=None, fuzzy=False):
    """
    Find windows by title using pywinauto.

    Args:
        title: Window title to search for
        pid: Process ID (required)
        fuzzy: If True, do partial matching (case-insensitive contains)

    Returns:
        List of window information dictionaries
    """
    if pid is None:
        raise ValueError("PID is required. Please provide --pid argument.")

    print(f"Searching for windows with title: '{title}' in PID: {pid} (fuzzy={fuzzy})")

    found_windows = []

    try:
        # Try both backends
        for backend in ["win32", "uia"]:
            try:
                # Connect to specific process
                app = Application(backend=backend).connect(process=pid)
                windows = app.windows()

                # Process found windows
                for win in windows:
                    try:
                        win_title = win.window_text()
                        print(f"  Checking window: '{win_title}' [{backend}]")
                        # Check if title matches
                        if fuzzy:
                            # Partial match (case-insensitive contains)
                            if title.lower() not in win_title.lower():
                                continue
                        else:
                            # Exact match (case-insensitive)
                            if title.lower() != win_title.lower():
                                continue

                        # Get window properties
                        is_visible = (
                            win.is_visible() if hasattr(win, "is_visible") else False
                        )

                        # Only include visible windows
                        if not is_visible:
                            continue

                        rect = win.rectangle() if hasattr(win, "rectangle") else None
                        width = rect.width() if rect else 0
                        height = rect.height() if rect else 0

                        # Get handle
                        hwnd = win.handle if hasattr(win, "handle") else None

                        window_info = {
                            "backend": backend,
                            "window": win,
                            "hwnd": hwnd,
                            "title": win_title,
                            "width": width,
                            "height": height,
                        }

                        found_windows.append(window_info)
                        print(f"  Found: '{win_title}' [{backend}] ({width}x{height})")

                    except Exception as e:
                        print(f"  Warning: Could not read window: {e}")

            except Exception as e:
                print(f"  Backend {backend}: {e}")

    except Exception as e:
        print(f"Error searching for windows: {e}")

    return found_windows


def focus_window(window_info):
    """
    Set focus to a window.

    Args:
        window_info: Window information dictionary

    Returns:
        True if successful, False otherwise
    """
    try:
        win = window_info["window"]

        print(f"Focusing window: '{window_info['title']}'")

        # Try to set focus using pywinauto
        try:
            win.set_focus()
            time.sleep(0.3)
            print("  Focused using pywinauto")
            return True
        except Exception as e:
            print(f"  pywinauto focus failed: {e}")

        # Fallback to win32gui
        try:
            import win32gui
            import win32con

            hwnd = window_info["hwnd"]

            # Restore if minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

            # Bring to foreground
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.3)
            print("  Focused using win32gui")
            return True
        except Exception as e:
            print(f"  win32gui focus failed: {e}")

        return False
    except Exception as e:
        print(f"Error focusing window: {e}")
        return False


def press_key_combo(combo):
    """
    Press a key combination.

    Args:
        combo: Key combination string (e.g., "ctrl+c", "ctrl+shift+t")
    """
    # Normalize the combo string
    combo = combo.lower().strip()

    # Split by + to get individual keys
    keys = [k.strip() for k in combo.split("+")]

    # Map common key names to pyautogui key names
    key_mapping = {
        "control": "ctrl",
        "windows": "win",
        "cmd": "command",
        "command": "command",
        "super": "win",
        "return": "enter",
        "escape": "esc",
        "del": "delete",
    }

    # Normalize keys
    normalized_keys = []
    for key in keys:
        if key in key_mapping:
            normalized_keys.append(key_mapping[key])
        else:
            normalized_keys.append(key)

    print(f"  Pressing: {' + '.join(normalized_keys)}")

    # Press the key combination
    if len(normalized_keys) == 1:
        pyautogui.press(normalized_keys[0])
    else:
        pyautogui.hotkey(*normalized_keys)


def click_wemeet_share(pid=None, title="WeCom Meeting"):
    """
    Special action: Find the smallest window and click on its right corner.

    Args:
        pid: Process ID to filter by

    Returns:
        True if successful, False otherwise
    """
    # Find windows
    windows = find_windows_by_title(title, pid=pid, fuzzy=True)

    if not windows:
        print(f"\nError: No windows found matching '{title}'")
        return False

    print(f"\nFound {len(windows)} window(s)")

    # Find the smallest window by area
    smallest_window = min(windows, key=lambda w: w["width"] * w["height"])

    print(
        f"Smallest window: '{smallest_window['title']}' ({smallest_window['width']}x{smallest_window['height']})"
    )

    # Focus the window
    if not focus_window(smallest_window):
        print("Warning: Could not focus window, attempting to click anyway...")

    # Small delay after focusing
    time.sleep(0.3)

    # Calculate right corner position
    rect = smallest_window["window"].rectangle()
    # Click near the right edge, slightly inset from the corner
    click_x = rect.right - 100
    click_y = rect.bottom - 100

    print(f"Clicking at position: ({click_x}, {click_y})")

    # Move mouse and click
    pyautogui.click(click_x, click_y)

    print("Done!")
    return True


def run_cpu_stress(duration=30, prime95_path="prime95.exe"):
    """
    Run CPU stress test using Prime95.

    Args:
        duration: Duration in seconds (default: 30)
        prime95_path: Path to prime95.exe (default: "prime95.exe")

    Returns:
        True if successful, False otherwise
    """
    print(f"Starting CPU stress test for {duration} seconds...")
    print(f"  Using: {prime95_path}")

    try:
        # Build Prime95 command with -t option for torture test
        cmd = [prime95_path, "-t"]

        print(f"  Command: {' '.join(cmd)}")

        # Start Prime95 torture test
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        print(f"  Prime95 started (PID: {process.pid})")

        # Wait for specified duration
        time.sleep(duration)

        # Terminate Prime95
        print("  Stopping Prime95...")
        process.terminate()
        try:
            process.wait(timeout=5)
            print("  Prime95 terminated successfully")
        except subprocess.TimeoutExpired:
            process.kill()
            print("  Prime95 killed (force)")

        print("CPU stress test completed!")
        return True

    except FileNotFoundError:
        print(f"  Error: {prime95_path} not found!")
        return False
    except Exception as e:
        print(f"  Error running CPU stress test: {e}")
        return False


def run_gpu_stress(duration=30, furmark_path="furmark.exe", width=1920, height=1080):
    """
    Run GPU stress test using FurMark.

    Args:
        duration: Duration in seconds (default: 30)
        furmark_path: Path to furmark.exe (default: "furmark.exe")
        width: Resolution width (default: 1920)
        height: Resolution height (default: 1080)

    Returns:
        True if successful, False otherwise
    """
    print(f"Starting GPU stress test for {duration} seconds...")
    print(f"  Using: {furmark_path}")
    print(f"  Resolution: {width}x{height}")

    try:
        # Build FurMark command with CLI options
        # Convert duration from seconds to milliseconds for --max-time
        max_time_ms = duration * 1000

        cmd = [
            furmark_path,
            "--demo", "furmark-gl",
            "--width", str(width),
            "--height", str(height),
            "--artifact-scanner",
            "--log-gpu-data",
            "--max-time", str(max_time_ms)
        ]

        print(f"  Command: {' '.join(cmd)}")

        # Start FurMark
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        print(f"  FurMark started (PID: {process.pid})")

        # Wait for the process to complete (FurMark will exit after max-time)
        # Add a small buffer to the wait time
        try:
            process.wait(timeout=duration + 10)
            print("  FurMark completed successfully")
        except subprocess.TimeoutExpired:
            print("  FurMark timeout, terminating...")
            process.terminate()
            try:
                process.wait(timeout=5)
                print("  FurMark terminated successfully")
            except subprocess.TimeoutExpired:
                process.kill()
                print("  FurMark killed (force)")

        print("GPU stress test completed!")
        return True

    except FileNotFoundError:
        print(f"  Error: {furmark_path} not found!")
        return False
    except Exception as e:
        print(f"  Error running GPU stress test: {e}")
        return False


def run_network_stress(pid, out_kbps=100, duration=30, limit_app_path="LimitForApplication.exe"):
    """
    Run network stress test by limiting bandwidth for a specific process.

    Args:
        pid: Process ID to limit bandwidth for
        out_kbps: Output bandwidth limit in kbps (default: 100)
        duration: Duration in seconds (default: 30)
        limit_app_path: Path to LimitForApplication.exe (default: "LimitForApplication.exe")

    Returns:
        True if successful, False otherwise
    """
    print(f"Starting network stress test for {duration} seconds...")
    print(f"  Using: {limit_app_path}")
    print(f"  Target PID: {pid}")
    print(f"  Bandwidth limit: {out_kbps} kbps")

    try:
        # Build LimitForApplication command
        cmd = [
            limit_app_path,
            str(pid),
            str(out_kbps),
            str(duration)
        ]

        print(f"  Command: {' '.join(cmd)}")

        # Start LimitForApplication
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        print(f"  LimitForApplication started (PID: {process.pid})")

        # Wait for the process to complete
        try:
            stdout, stderr = process.communicate(timeout=duration + 10)
            if process.returncode == 0:
                print("  Network stress test completed successfully")
            else:
                print(f"  Warning: Process exited with code {process.returncode}")
                if stderr:
                    print(f"  Error output: {stderr.decode('utf-8', errors='ignore')}")
        except subprocess.TimeoutExpired:
            print("  Timeout, terminating...")
            process.terminate()
            try:
                process.wait(timeout=5)
                print("  Terminated successfully")
            except subprocess.TimeoutExpired:
                process.kill()
                print("  Killed (force)")

        print("Network stress test completed!")
        return True

    except FileNotFoundError:
        print(f"  Error: {limit_app_path} not found!")
        return False
    except Exception as e:
        print(f"  Error running network stress test: {e}")
        return False


def execute_actions(actions, pid, window_index=0, interval=0.5):
    """
    Execute a list of actions from tasks.toml.

    Args:
        actions: List of action dictionaries
        pid: Process ID
        window_index: Which window to use if multiple found (0 = first)
        interval: Delay between actions in seconds

    Returns:
        True if successful, False otherwise
    """
    print(f"Executing {len(actions)} action(s):")

    for i, action in enumerate(actions, 1):
        action_type = action.get("type")
        print(f"  [{i}/{len(actions)}] Action type: {action_type}")

        if action_type == "focus":
            # Focus window by title
            title = action.get("title")
            if not title:
                print(f"    Error: 'focus' action requires 'title' field")
                return False

            fuzzy = action.get("fuzzy", False)
            windows = find_windows_by_title(title, pid=pid, fuzzy=fuzzy)
            if not windows:
                print(f"    Error: No windows found matching '{title}'")
                return False

            if window_index >= len(windows):
                print(
                    f"    Warning: Index {window_index} out of range, using first window"
                )
                window_index = 0

            window = windows[window_index]
            print(f"    Focusing window: '{window['title']}'")

            if not focus_window(window):
                print("    Warning: Could not focus window")
                return False

            time.sleep(0.3)

        elif action_type == "press":
            # Press key combination
            key = action.get("key")
            if not key:
                print(f"    Error: 'press' action requires 'key' field")
                return False

            press_key_combo(key)
        elif action_type == "click":
            # Click button by text
            text = action.get("text")
            if not text:
                print(f"    Error: 'click' action requires 'text' field")
                return False

            case_sensitive = action.get("case_sensitive", False)
            exact_match = action.get("exact_match", False)

            print(f"    Clicking button with text: '{text}'")
            if not click_button_by_text(
                pid, text, case_sensitive=case_sensitive, exact_match=exact_match
            ):
                print(f"    Warning: Could not click button with text '{text}'")
                return False
        elif action_type == "click-wemeet-share":
            # Special action: click wemeet share
            title = action.get("title")
            click_wemeet_share(pid=pid, title=title)
        elif action_type == "cpu-stress":
            # CPU stress test
            duration = action.get("duration", 30)
            prime95_path = action.get("path", "prime95.exe")
            if not run_cpu_stress(duration=duration, prime95_path=prime95_path):
                print(f"    Warning: CPU stress test failed")
                return False
        elif action_type == "gpu-stress":
            # GPU stress test
            duration = action.get("duration", 30)
            furmark_path = action.get("path", "furmark.exe")
            width = action.get("width", 1920)
            height = action.get("height", 1080)
            if not run_gpu_stress(duration=duration, furmark_path=furmark_path, width=width, height=height):
                print(f"    Warning: GPU stress test failed")
                return False
        elif action_type == "network-stress":
            # Network stress test
            if not pid:
                print(f"    Error: 'network-stress' action requires PID")
                return False
            duration = action.get("duration", 30)
            out_kbps = action.get("out_kbps", 100)
            limit_app_path = action.get("path", "LimitForApplication.exe")
            if not run_network_stress(pid=pid, out_kbps=out_kbps, duration=duration, limit_app_path=limit_app_path):
                print(f"    Warning: Network stress test failed")
                return False
        else:
            print(f"    Error: Unknown action type '{action_type}'")
            return False

        # Wait between actions (except after the last one)
        if i < len(actions):
            time.sleep(interval)

    print("Done!")
    return True


def run_task(task_name, pid, config_file="tasks.toml", window_index=0, interval=0.5):
    """
    Execute a task from tasks.toml configuration.

    Args:
        task_name: Task name from tasks.toml (e.g., "zoom.video.start", "cpu-stress")
        pid: Process ID (required for window-based tasks, can be None for stress tests)
        config_file: Path to tasks.toml config file (default: "tasks.toml")
        window_index: Which window to use if multiple found (0 = first)
        interval: Delay between actions in sequence (seconds)

    Returns:
        True if successful, False otherwise

    Raises:
        ValueError: If task not found or no actions defined
        FileNotFoundError: If config file doesn't exist
    """
    # Load config from tasks.toml
    config = load_combo_config(config_file)

    if not config:
        raise FileNotFoundError(f"Could not load config file '{config_file}'")

    # Check if task exists
    if task_name not in config:
        available = ", ".join(config.keys())
        raise ValueError(
            f"Task '{task_name}' not found in {config_file}. Available: {available}"
        )

    task_config = config[task_name]

    # Get actions from task config
    actions = task_config.get("actions")
    if not actions:
        raise ValueError(f"No 'actions' found in task '{task_name}'")

    print(f"Using task '{task_name}' from {config_file}")
    if pid:
        print(f"  PID: {pid}")
    print(f"  Interval: {interval}s")

    # Execute actions
    return execute_actions(
        actions, pid=pid, window_index=window_index, interval=interval
    )
