
mozconfigs for building SpiderMonkey + FireFox

notes:

- each config uses `MOZ_OBJDIR` to point build artifacts
  into a directory named `build-<shell|browser>-<debug|release>`,
  which prevents builds clobbering one another.

- debugging: With `--enable-jitspew` in the build config, 
  the debug channels can be accessed with the environment var
  `IONFLAGS` set while running the shell.

  e.g: `IONFLAGS=codegen ./jsshell -e 'console.log(1);'` 

- testing: after building the shell, jit tests can be run with:
  `python3 ./jit-test/jit_test.py --args="--no-ion" ../../jsshell`

- see `spidermonkey.nix` if you're a nix user for a devshell

- AOT based configs will not work on upstream as they are for my fork.

