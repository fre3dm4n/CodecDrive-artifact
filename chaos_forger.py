"""
ChaosCodec - Systematic Codec State Space Exploration

This module implements the chaos injection strategy described in the paper,
systematically exploring codec state space through controlled resource stress
and configuration manipulation.

Requirements:
    pip install tomli

Usage:
    python chaos_forger.py --app zoom --pid 12345 --duration 600
    python chaos_forger.py --app ms-teams --pid 67890 --duration 600 --config tasks.toml
"""

import argparse
import random
import time
import tomli
import os
from typing import List, Dict, Any
from task_runner import run_task


class ChaosForger:
    """
    Implements systematic chaos injection for codec state space exploration.

    The system explores codec states by:
    1. Iterating through content types (camera video, screen sharing)
    2. Randomly applying resource stress actions or configuration parameters
    3. Running each action for 30 seconds
    4. Cycling through combinations over a 10-minute window
    """

    # Content Types (T)
    CONTENT_CAMERA = "camera"
    CONTENT_SCREEN = "screen"

    # Resource Stress Actions (R)
    ACTION_CPU = "cpu"
    ACTION_GPU = "gpu"
    ACTION_NETWORK = "network"

    # Configuration Parameters (C)
    ACTION_RESOLUTION = "resolution"
    ACTION_QUALITY = "quality"

    def __init__(self, app: str, pid: int, config_file: str = "tasks.toml",
                 action_duration: int = 30, network_kbps: int = 20):
        """
        Initialize ChaosForger.

        Args:
            app: Application name (e.g., "zoom", "ms-teams", "wecom", "wemeet")
            pid: Process ID of the target application
            config_file: Path to tasks.toml configuration file
            action_duration: Duration for each action in seconds (default: 30)
            network_kbps: Network bandwidth limit in kbps (default: 20)
        """
        self.app = app
        self.pid = pid
        self.config_file = config_file
        self.action_duration = action_duration
        self.network_kbps = network_kbps

        # Load configuration
        self.config = self._load_config()

        # Define content types
        self.content_types = [self.CONTENT_CAMERA, self.CONTENT_SCREEN]

        # Define all possible actions (R ∪ C)
        self.resource_actions = [self.ACTION_CPU, self.ACTION_GPU, self.ACTION_NETWORK]
        self.config_actions = [self.ACTION_RESOLUTION, self.ACTION_QUALITY]
        self.all_actions = self.resource_actions + self.config_actions

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from TOML file."""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Config file not found: {self.config_file}")

        with open(self.config_file, "rb") as f:
            return tomli.load(f)

    def _get_task_name(self, content_type: str, action: str, phase: str) -> str:
        """
        Get task name from configuration.

        Args:
            content_type: "camera" or "screen"
            action: Action type (cpu, gpu, network, resolution, quality)
            phase: "start" or "end"

        Returns:
            Task name in format "app_content_phase" or None if not found
        """
        # For resource stress actions, use chaos namespace
        if action in self.resource_actions:
            if action == self.ACTION_CPU:
                return "chaos_cpu-stress"
            elif action == self.ACTION_GPU:
                return "chaos_gpu-stress"
            elif action == self.ACTION_NETWORK:
                return "chaos_network-stress"

        # Map content types to task keys
        if content_type == self.CONTENT_CAMERA:
            content_key = "camera"
        elif content_type == self.CONTENT_SCREEN:
            content_key = "screen"
        else:
            content_key = None

        # For configuration actions, use app-specific tasks
        if action in self.config_actions:
            task_name = f"{self.app}_{action}_{phase}"
            if task_name in self.config:
                return task_name

        # For content-based tasks (camera/screen)
        if content_key:
            task_name = f"{self.app}_{content_key}_{phase}"
            if task_name in self.config:
                return task_name

        return None

    def _execute_content_switch(self, content_type: str, enable: bool) -> bool:
        """
        Switch content type (camera video or screen sharing).

        Args:
            content_type: "camera" or "screen"
            enable: True to start, False to stop

        Returns:
            True if successful, False otherwise
        """
        phase = "start" if enable else "end"
        task_name = self._get_task_name(content_type, None, phase)

        if not task_name:
            print(f"  Warning: No task found for {self.app}.{content_type}.{phase}")
            return False

        print(f"  {'Enabling' if enable else 'Disabling'} {content_type} mode: {task_name}")

        try:
            return run_task(task_name, self.pid, self.config_file)
        except Exception as e:
            print(f"  Error executing {task_name}: {e}")
            return False

    def _execute_action(self, action: str, enable: bool) -> bool:
        """
        Execute a chaos action (resource stress or configuration change).

        Args:
            action: Action type (cpu, gpu, network, resolution, quality)
            enable: True to start, False to stop

        Returns:
            True if successful, False otherwise
        """
        phase = "start" if enable else "end"

        # For resource stress actions
        if action in self.resource_actions:
            if not enable:
                # Resource stress actions don't need explicit stop
                return True

            task_name = self._get_task_name(None, action, phase)
            if not task_name:
                print(f"  Warning: No task found for {action}")
                return False

            print(f"  Applying resource stress: {action}")

            try:
                # For network stress, we need to pass the PID
                if action == self.ACTION_NETWORK:
                    # Simply run the task - duration and bandwidth are in config
                    return run_task(task_name, self.pid, self.config_file)
                else:
                    return run_task(task_name, self.pid, self.config_file)
            except Exception as e:
                print(f"  Error executing {task_name}: {e}")
                return False

        # For configuration actions
        if action in self.config_actions:
            task_name = self._get_task_name(None, action, phase)
            if not task_name:
                print(f"  Warning: No task found for {self.app}.{action}.{phase}")
                return False

            print(f"  {'Applying' if enable else 'Reverting'} configuration: {action}")

            try:
                return run_task(task_name, self.pid, self.config_file)
            except Exception as e:
                print(f"  Error executing {task_name}: {e}")
                return False

        return False

    def run_chaos_cycle(self, duration: int = 600):
        """
        Run a complete chaos injection cycle.

        The system systematically explores codec state space by:
        1. Iterating through each content type (camera, screen)
        2. Randomly applying actions from R ∪ C for 30 seconds each
        3. Cycling through combinations over the specified duration

        Args:
            duration: Total duration in seconds (default: 600 = 10 minutes)
        """
        print("=" * 80)
        print("ChaosCodec - Systematic Codec State Space Exploration")
        print("=" * 80)
        print(f"Application: {self.app}")
        print(f"Process ID: {self.pid}")
        print(f"Total Duration: {duration}s")
        print(f"Action Duration: {self.action_duration}s")
        print(f"Network Limit: {self.network_kbps} kbps")
        print("=" * 80)

        # Filter available actions based on what exists in config
        available_actions = []
        for action in self.all_actions:
            task_name = self._get_task_name(None, action, "start")
            if task_name:
                available_actions.append(action)
            else:
                print(f"Skipping action '{action}' - task not found in config")

        if not available_actions:
            print(f"\nError: No available actions found in config for app '{self.app}'")
            return

        print(f"\nAvailable actions: {', '.join(available_actions)}")
        print("=" * 80)

        # Calculate duration per content type
        duration_per_content = duration // len(self.content_types)
        print(f"\nDuration per content type: {duration_per_content}s")
        print("=" * 80)

        start_time = time.time()
        overall_elapsed = 0

        # Iterate through each content type
        for content_idx, content_type in enumerate(self.content_types):
            content_start_time = time.time()
            content_elapsed = 0
            action_count = 0

            print(f"\n[Content Type {content_idx + 1}/{len(self.content_types)}: {content_type.upper()}]")
            print(f"Allocated time: {duration_per_content}s")
            print("-" * 80)

            # Enable content type
            print(f"  Enabling {content_type} mode...")
            if not self._execute_content_switch(content_type, True):
                print(f"  Warning: Failed to enable {content_type} mode")

            time.sleep(2)  # Small delay after switching

            # Apply random chaos actions for the allocated duration
            while content_elapsed < duration_per_content:
                action_count += 1

                # Randomly select an action from available actions
                action = random.choice(available_actions)
                print(f"\n  [Action {action_count}] Applying chaos: {action.upper()}")

                # Apply the action
                self._execute_action(action, True)

                # Resource stress actions have their own duration, config actions need to be maintained
                if action in self.resource_actions:
                    print(f"    Resource stress action running with configured duration...")
                    # Resource stress actions manage their own duration, no need to wait
                else:
                    # Wait for action duration for configuration actions
                    print(f"    Maintaining state for {self.action_duration}s...")
                    action_start = time.time()

                    # Show progress during action
                    while time.time() - action_start < self.action_duration:
                        remaining = self.action_duration - (time.time() - action_start)
                        print(f"      Progress: {self.action_duration - remaining:.1f}s / {self.action_duration}s", end='\r')
                        time.sleep(1)

                    print(f"      Progress: {self.action_duration}s / {self.action_duration}s")

                    # Revert configuration actions
                    print(f"    Reverting configuration: {action.upper()}")
                    self._execute_action(action, False)
                    time.sleep(1)

                # Update elapsed time for this content type
                content_elapsed = time.time() - content_start_time
                overall_elapsed = time.time() - start_time
                print(f"    Content elapsed: {content_elapsed:.1f}s / {duration_per_content}s | Overall: {overall_elapsed:.1f}s / {duration}s")

            # Disable content type
            print(f"\n  Disabling {content_type} mode...")
            if not self._execute_content_switch(content_type, False):
                print(f"  Warning: Failed to disable {content_type} mode")

            time.sleep(2)  # Small delay before next content type

            overall_elapsed = time.time() - start_time
            print(f"\n  Content type '{content_type}' completed: {action_count} actions in {content_elapsed:.1f}s")

        print("\n" + "=" * 80)
        print(f"Chaos injection completed! Total time: {overall_elapsed:.1f}s")
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="ChaosCodec - Systematic Codec State Space Exploration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python chaos_forger.py --app zoom --pid 12345 --duration 600
  python chaos_forger.py --app ms-teams --pid 67890 --duration 300
  python chaos_forger.py --app wecom --pid 11111 --action-duration 20
  python chaos_forger.py --app wemeet --pid 22222 --network-kbps 50
        """
    )

    parser.add_argument(
        "--app",
        required=True,
        choices=["zoom", "ms-teams", "wecom", "wemeet"],
        help="Target application name"
    )

    parser.add_argument(
        "--pid",
        type=int,
        required=True,
        help="Process ID of the target application"
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=600,
        help="Total chaos injection duration in seconds (default: 600 = 10 minutes)"
    )

    parser.add_argument(
        "--action-duration",
        type=int,
        default=30,
        help="Duration for each chaos action in seconds (default: 30)"
    )

    parser.add_argument(
        "--network-kbps",
        type=int,
        default=20,
        help="Network bandwidth limit in kbps (default: 20)"
    )

    parser.add_argument(
        "--config",
        default="tasks.toml",
        help="Path to tasks.toml configuration file (default: tasks.toml)"
    )

    args = parser.parse_args()

    try:
        forger = ChaosForger(
            app=args.app,
            pid=args.pid,
            config_file=args.config,
            action_duration=args.action_duration,
            network_kbps=args.network_kbps
        )

        forger.run_chaos_cycle(duration=args.duration)

    except KeyboardInterrupt:
        print("\n\nChaos injection interrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
