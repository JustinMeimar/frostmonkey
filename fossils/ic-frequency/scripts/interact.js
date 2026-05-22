/**
 * Generic site interaction script for browsertime.
 *
 * Scrolls, clicks visible links, and waits for network idle.
 * Site-agnostic: uses generic selectors that work on any page.
 *
 * Usage: ./mach browsertime --script scripts/interact.js <url>
 */
"use strict";

module.exports = async function (context, commands) {
  const url = context.options._.length
    ? context.options._[context.options._.length - 1]
    : null;

  if (url) {
    await commands.navigate(url);
  }

  await commands.wait.byTime(3000);

  // scroll down in steps to trigger lazy-loaded content
  for (let i = 0; i < 5; i++) {
    await commands.js.run("window.scrollBy(0, window.innerHeight)");
    await commands.wait.byTime(1000);
  }

  // scroll back up
  await commands.js.run("window.scrollTo(0, 0)");
  await commands.wait.byTime(1000);

  // click up to 3 in-page links (same origin, not # anchors)
  const clickCount = await commands.js.run(`
    const origin = window.location.origin;
    const links = [...document.querySelectorAll('a[href]')]
      .filter(a => {
        try {
          const u = new URL(a.href);
          return u.origin === origin
              && u.pathname !== window.location.pathname
              && !a.href.includes('#')
              && a.offsetParent !== null;
        } catch { return false; }
      })
      .slice(0, 3);
    window.__interactLinks = links.map(a => a.href);
    return links.length;
  `);

  for (let i = 0; i < Math.min(clickCount, 3); i++) {
    const href = await commands.js.run(
      `return window.__interactLinks[${i}]`
    );
    if (!href) break;

    try {
      await commands.navigate(href);
      await commands.wait.byTime(2000);

      // scroll on the new page too
      for (let s = 0; s < 3; s++) {
        await commands.js.run("window.scrollBy(0, window.innerHeight)");
        await commands.wait.byTime(800);
      }
    } catch (e) {
      // navigation may fail (popups, etc) -- continue
    }
  }

  await commands.wait.byTime(2000);
};
