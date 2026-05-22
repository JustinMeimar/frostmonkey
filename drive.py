import argparse
import subprocess
import os
import sys
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


class Command(Enum):
    BUILD = "build"
    BOOTSTRAP = "bootstrap"
    CLEAN = "clean"
    DEBUG = "debug"
    RUN = "run"
    SYMLINK = "symlink"

MOZ_CONFIG_DIR = Path("../mozconfigs")

class Build(Enum):
    # each option corresponds to mozconfig file name and
    # identically named build directory.
    SHELL_DEBUG = "build-shell-debug"
    SHELL_DEBUG_AOT = "build-shell-debug-aot"
    SHELL_RELEASE = "build-shell-release"
    SHELL_RELEASE_AOT = "build-shell-release-aot"
    BROWSER_DEBUG = "build-browser-debug"
    BROWSER_RELEASE = "build-browser-release"
    BROWSER_DEBUG_AOT = "build-browser-debug-aot"
    BROWSER_RELEASE_AOT = "build-browser-release-aot"

    @property
    def path(self) -> Path:
        return Path(self.value) 

class JSOptions(Enum): 
    BASELINE = \
        "--no-ion --blinterp --baseline-eager --ion-extra-checks \
        --fast-warmup --blinterp-warmup-threshold=100"
    
    PBL_JITLESS = \
        "--no-jit-backend --aot-ics \
        --portable-baseline --portable-baseline-eager"
    
    ENFORCE_AOT_PBL_JITLESS = \
        "--no-jit-backend --enforce-aot-ics \
        --portable-baseline --portable-baseline-eager"
    
    DEFAULT = ""

class CommandRunner:
    def __init__(self, build: Build, program: Optional[str], js_options: str):
        self.build_type: Build      = build
        self.program: Optional[str] = program
        self.js_options: str        = js_options
        self.root_dir: Path         = Path(__file__).parent

    def get_js_path(self) -> Path:
        return self.root_dir / self.build_type.path / "dist" / "bin" / "js"

    def get_jsshell_symlink(self) -> Path:
        return self.root_dir / "jsshell"

    def _build_command(self, extra_args: Optional[List[str]] = None) -> List[str]:
        cmd = [str(self.get_js_path())]
        if self.js_options:
            cmd.extend(self.js_options.split())
        if self.program:
            cmd.extend(["-f", self.program])
        if extra_args:
            cmd.extend(extra_args)
        return cmd

    def run(self, extra_args: Optional[List[str]] = None) -> int:
        cmd = self._build_command(extra_args)
        print(f"Running: {' '.join(cmd)}")
        return subprocess.run(cmd).returncode

    def debug(self, extra_args: Optional[List[str]] = None) -> int:
        cmd = self._build_command(extra_args)
        gdb_cmd = ["gdb", "--args"] + cmd
        print(f"Debugging: {' '.join(cmd)}")
        return subprocess.run(gdb_cmd).returncode

    def symlink_jsshell(self) -> int:
        js_path = self.get_js_path()
        symlink = self.get_jsshell_symlink()
        if symlink.exists() or symlink.is_symlink():
            symlink.unlink()

        symlink.symlink_to(js_path)
        print(f"Created symlink: {symlink} -> {js_path}")
        return 0

    def symlink_compile_commands(self) -> int:
        src = self.root_dir / self.build_type.path / "compile_commands.json"
        dst = self.root_dir / "js" / "src" / "compile_commands.json"
        if not src.exists():
            print(f"Error: {src} does not exist")
            return 1
        if dst.exists() or dst.is_symlink():
            dst.unlink()

        dst.symlink_to(src)
        print(f"Created symlink: {dst} -> {src}")
        return 0

    @staticmethod
    def mozconfig_for(build: 'Build') -> Path:
        name = build.value.removeprefix("build-") + ".mozconfig"
        return MOZ_CONFIG_DIR / name

    def _needs_configure(self) -> bool:
        config_status = self.root_dir / self.build_type.path / "config.status"
        mozconfig_path = self.mozconfig_for(self.build_type)
        if not config_status.exists():
            return True
        return mozconfig_path.stat().st_mtime > config_status.stat().st_mtime

    def _is_aot_build(self) -> bool:
        return "aot" in self.build_type.value

    def build(self) -> int:
        env = os.environ.copy()
        mozconfig_path = str(self.mozconfig_for(self.build_type))
        env["MOZCONFIG"] = mozconfig_path

        print(f"Building with MOZCONFIG={mozconfig_path}")
        print(f"Build directory: {self.build_type.path}")

        if self._needs_configure():
            print("Running configure (mozconfig changed or first build)...")
            result = subprocess.run(["./mach", "configure"], env=env)
            if result.returncode != 0:
                return result.returncode
        else:
            print("Skipping configure (no mozconfig changes)")

        result = subprocess.run(["bear", "--", "./mach", "build"], env=env)
        if result.returncode != 0:
            return result.returncode

        print("\nCreating symlinks...")
        symlink_result = self.symlink_jsshell()
        if symlink_result != 0:
            print("Warning: Failed to create jsshell symlink")

        cc_result = self.symlink_compile_commands()
        if cc_result != 0:
            print("Warning: Failed to create compile_commands.json symlink")

        return 0

    def bootstrap(self) -> int:
        if not self._is_aot_build():
            print("ERROR: bootstrap only works with AOT builds")
            return 1

        print("=== Bootstrap: build (clean) ===")
        rc = self.build()
        if rc != 0:
            return rc

        print("\n=== Bootstrap: dump AOT blobs ===")
        js = self.get_js_path()
        env = os.environ.copy()
        env["IONFLAGS"] = "bl-aot"
        result = subprocess.run(
            [str(js), "--dump-bl-interp", "--dump-aot-ics",
             "--dump-bl-self-hosted", "-e", "quit(0);"],
            env=env,
        )
        if result.returncode != 0:
            print("ERROR: AOT dump failed")
            return result.returncode

        print("\n=== Bootstrap: rebuild with blobs ===")
        rc = self.build()
        if rc != 0:
            return rc

        print("\n=== Bootstrap complete ===")
        return 0

    def clean(self) -> int:
        print("Cleaning build artifacts...")
        env = os.environ.copy()
        env["MOZCONFIG"] = str(self.mozconfig_for(self.build_type))
        subprocess.run(["./mach", "clobber"], env=env)
        return 0

def parse():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "command",
        type=str,
        default="run",
        choices=[cmd.value for cmd in Command],
        help="Build directory to use (default: %(default)s)"
    )
    parser.add_argument(
        "--build",
        type=str,
        default=Build.SHELL_DEBUG.value,
        choices=[bd.value for bd in Build],
        help="Build directory to use (default: %(default)s)"
    )
    parser.add_argument(
        "--program",
        type=str,
        help="JS program/file to execute"
    )
    parser.add_argument(
        "--js-options",
        type=str,
        default="DEFAULT",
        help=f"JS options"
    )
    args, extra = parser.parse_known_args()
    return args, extra

def main():
    args, extra = parse()
    print("COMMAND: ", args.command)
    print("BUILD: ", args.build)
    print("JS OPTIONS: ", args.js_options)

    # Convert string arguments to enums
    build = Build(args.build)

    try:
        js_options_str = JSOptions[args.js_options.upper()].value
        print(f"Using preset: {args.js_options.upper()}")
    except KeyError:
        js_options_str = args.js_options
        print(f"Using custom options: {js_options_str}")
    
    runner = CommandRunner(build, args.program, js_options_str)

    if args.command == Command.RUN.value:
        return runner.run(extra)
    elif args.command == Command.DEBUG.value:
        return runner.debug(extra)
    elif args.command == Command.BUILD.value:
        return runner.build()
    elif args.command == Command.BOOTSTRAP.value:
        return runner.bootstrap()
    elif args.command == Command.SYMLINK.value:
        return runner.symlink_jsshell()
    elif args.command == Command.CLEAN.value:
        return runner.clean()
    else:
        print(f"Unknown command: {args.command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
