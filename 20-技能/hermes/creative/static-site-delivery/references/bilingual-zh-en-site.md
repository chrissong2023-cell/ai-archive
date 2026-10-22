# One-page bilingual (zh/en) static site

One HTML file, no separate /en/ tree: every translatable element carries both
languages, JS swaps them. Keeps URLs, SEO and the user's shared links stable,
and keeps one copy of the layout.

## Markup

```html
<p data-zh="18 年国际货运代理，覆盖 100+ 国家。"
   data-en="18 years in freight forwarding, 100+ countries.">18 年国际货运代理，覆盖 100+ 国家。</p>

<h1>
  <span data-zh="海运、空运、班列，<br>还有别人不愿接的那票货。"
        data-en="Ocean, air, rail —<br>and the shipment nobody else would take.">海运、空运、班列，<br>还有别人不愿接的那票货。</span>
</h1>
```

Inline text = the page's default language, so a JS failure still renders a
readable page. `<html lang>` is also set to the default.

## Script

```js
(function () {
  var html = document.documentElement;
  var btn = document.getElementById('langBtn');

  function applyLang(lang) {
    document.body.setAttribute('data-lang', lang);
    html.setAttribute('lang', lang === 'zh' ? 'zh-CN' : 'en');
    var nodes = document.querySelectorAll('[data-zh][data-en]');
    for (var i = 0; i < nodes.length; i++) {
      var t = nodes[i].getAttribute(lang === 'zh' ? 'data-zh' : 'data-en');
      if (t == null) continue;
      if (/<br\s*\/?>/i.test(t)) nodes[i].innerHTML = t;  // only line breaks travel as HTML
      else nodes[i].textContent = t;
    }
    if (btn) btn.textContent = lang === 'zh' ? 'EN' : '中文';
  }

  var initial = 'zh';                                   // page default
  try { var s = localStorage.getItem('site-lang'); if (s) initial = s; } catch (e) {}
  // URL wins over the remembered preference — BOTH directions
  if (/[?&]lang=en/.test(location.search)) initial = 'en';
  if (/[?&]lang=zh/.test(location.search)) initial = 'zh';
  applyLang(initial);                                   // ALWAYS, not only on change

  if (btn) btn.addEventListener('click', function () {
    var next = document.body.getAttribute('data-lang') === 'zh' ? 'en' : 'zh';
    applyLang(next);
    try { localStorage.setItem('site-lang', next); } catch (e) {}
  });
})();
```

## Pitfalls

- **`applyLang` must run on first load even when the language matches the
  default.** Guard it with `if (initial !== default)` and a page whose inline
  text is Chinese but whose intended default is English shows Chinese until the
  first click — the exact opposite of what `data-en` was added for. Call the
  applier unconditionally; it is idempotent.
- **The `?lang=` deep link must beat the stored preference, in both directions.**
  Handle `lang=zh` as well as `lang=en`, and apply the parameter *after*
  reading `localStorage` — otherwise a phone that once toggled to Chinese keeps
  opening the English page when a colleague shares an `?lang=en` link, and the
  link looks broken.
- **One key per site** (`site-lang`): two sites on one origin share storage.
  In automated screenshot runs, clear origin storage per navigation or every
  job after the first inherits the last language.
- **Only `<br>` may pass through `innerHTML`.** If a translation needs a link
  or `<em>`, use a separate `data-zh-html`/`data-en-html` pair and keep the
  default path on `textContent`.
- **Scan for leaks**: in EN mode walk leaf elements and flag
  `/[\u4e00-\u9fa5]/`. Catches untranslated blocks, CJK typed into a `data-en`
  value, and the intentional cases you should whitelist (the ICP备案号, the
  language button label).
- **Do not translate proper nouns**: legal entity names, WCA IDs, port codes,
  certification names (ISO 9001:2015, FIATA, BASC), people's names.
- **Typography is per-language**: CJK needs more line-height (1.7–1.8) and no
  letter-spacing; Latin headlines look wrong at the CJK size. Cap the clamp
  per language or pick a size that survives both, and check the rendered line
  count once in each.
- **A page that still renders the old language after a fix is usually cache.**
  The screenshot harness's Chrome profile caches `assets/app.js`; disable cache
  (`Network.setCacheDisabled`) or bump `?v=` and re-read `data-lang` from the DOM
  before concluding the toggle is broken. Confirm with
  `document.body.getAttribute('data-lang')` and one known string, not with a
  full-page screenshot at 180px wide.
