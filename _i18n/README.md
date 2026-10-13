# English site (/en/)

The English pages are generated from the Arabic pages — don't edit files under /en/ by hand.

After changing any Arabic page:

    python3 _i18n/build_en.py .

The script swaps every Arabic text run for its English translation (segments.json + out*.json + fixes.json),
turns the page left-to-right and points its links at /en/. If it prints UNTRANSLATED lines, add those strings
to fixes.json as {"new-id": "English"} together with an entry in segments.json, or ask Claude to translate them.

This folder starts with "_" so GitHub Pages doesn't publish it.
