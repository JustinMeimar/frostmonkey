
building:
- use the aot moz-configs which export the necessary
  `ENABLE_AOT_BASELINE` and `JS_ENABLE_AOT_ICS`

- run `just use-ics <CORPI>` before a bootstrap to ensure
  that aot ics get picked up, must be compiled s.t
  `CacheIRAOTGenerated.h.stub` is produced anew, only then
  will the dumping to native work. A third build is required
  to boostrap native AOT ics into the engine.

testing:

- two expected failures:
    - `self-test/assertRecoveredOnBailout-1.js`, this is due to JitOptions for
       baseline-warmup-threshold being baked into the aot blinterp (we have no
       relocation story for JitOptions as of yet)

    - `gc/pretenured-operations.js` needs confirmation
 
