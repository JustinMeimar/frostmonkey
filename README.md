
building:

- use the aot moz-configs which export the necessary
  `ENABLE_AOT_BASELINE` and `JS_ENABLE_AOT_ICS`

- run `just use-ics <CORPI>` before a bootstrap to ensure
  that aot ics get picked up, must be compiled s.t
  `CacheIRAOTGenerated.h.stub` is produced anew, only then
  will the dumping to native work. A third build is required
  to boostrap native AOT ics into the engine.

- see Justfile for flags to enable AOT in shell/browser

testing:

- with `--aot` two expected failures:
    - `self-test/assertRecoveredOnBailout-1.js`, this is due to JitOptions for
       baseline-warmup-threshold being baked into the aot blinterp (we have no
       relocation story for JitOptions as of yet)

    - `gc/pretenured-operations.js`

- on an empty AOT corpus with `--aot-ics-enforce`, all IC lookups go
  through FB stub. A dozen or so tests which expect IC allocations
  will fail, asserting GC events that did not occur, these can also be
  ignored.


 
