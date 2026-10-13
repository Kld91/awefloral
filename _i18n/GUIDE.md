# Translating the Awe Floral site (Arabic → English)

Awe Floral (أو فلورا) is a flower shop in Riyadh. It sells gift bouquets and vases with free delivery inside Riyadh
(awefloral.com) and wholesale flowers by the bunch/stem to shops, hotels and event planners (bunches.html, /wholesale/).
We are building an English copy of the whole site. Each segment below is a run of Arabic text cut out of the site's
HTML/JS/JSON. We will replace each Arabic segment, in place, with your English text.

## Output
Write ONE JSON file (path given in your task) shaped exactly like:
{ "t": { "<id>": "<English>", ... }, "notes": { "<id>": "<why this one is tricky>" } }
- Every id in your chunk must appear in "t". "notes" is optional — use it only for segments where the cut (context) made a clean
  translation impossible, or where you think the code around it needs a human look.
- Validate it parses (python3 -c "import json;json.load(open(PATH))").

## Hard rules (the text goes straight into code)
1. NEVER use ASCII apostrophe ' — use ’ (U+2019): we’ll, don’t, Valentine’s.
2. NEVER use ASCII double quote " or backtick ` or the sequence ${ — use “ ” for quotes.
3. Keep numbers, and the order of any numbers relative to the text when it matters (e.g. "10 أغصان" → "10 stems").
4. Keep leading/trailing punctuation roles: if the Arabic ends with ":" or "،" keep an equivalent (":" or ","). Arabic comma ، → ","  Arabic ؟ → "?".
5. The segment is often a FRAGMENT around a variable, tag or price (see ctx; the segment is marked ⟦like this⟧). Translate it so the
   sentence reads naturally in English once the surrounding pieces are put back in the same order. If English word order makes that
   impossible, do the best possible and add a note.
6. If ctx shows the segment is inside a regex (/a|b|c/) or a search-keyword list, return a lowercase English keyword
   (or a few keywords joined by |, e.g. "red|burgundy"), no spaces around |.
7. Same Arabic → same English everywhere (these strings are also used as keys).
8. Brand: أو فلورا → "Awe Floral". The legal company name (شركة روع النباتات للتجارة / روع النباتات) stays in Arabic exactly as written — copy it unchanged inside your English sentence. Keep Latin words already in the text.
9. Currency: ر.س → "SAR". Do not convert prices. شامل الضريبة → "incl. VAT".
10. Saudi dialect UI text → plain, friendly, short English. Button labels stay short (2–4 words).

## Tone
Like a good independent florist: calm, plain, specific, warm. No marketing fluff, no exclamation spam,
no "elevate/curated/stunning/indulge/unforgettable". Short sentences. US spelling. Sentence case for headings and buttons.

## Glossary (use these)
جوري / ورد جوري → roses (جوري أحمر → red roses) · ورد → flowers (or roses when clearly roses) · وردة → rose / flower
سبراي روز → spray roses · بيبي روز → baby roses (product "باقة بيبي روز" → "Baby Rose Bouquet")
ليليوم → lilies (ليليوم كازابلانكا → Casablanca lilies; براعم ليليوم → lily buds) · هدرنجا → hydrangea · قرنفل → carnations
أقحوان → chrysanthemums (أقحوان بومبون → pompon chrysanthemums, أقحوان ديزي → daisy chrysanthemums) · أوكالبتوس → eucalyptus
سوليداغو → solidago · دوار الشمس → sunflowers · جربيرا → gerberas · ستاتيس → statice · ألستروميريا → alstroemeria
واكس فلاور → waxflower · جيبسوفيلا → gypsophila · ليسيانثوس → lisianthus · أوركيد → orchids · سكابيوزا → scabiosa
أنثوريوم → anthurium · توليب → tulips · فاوانيا / بيوني → peonies · أوراق / خضرة → greenery
فازة → vase · فازة زجاج → glass vase · تنسيق → arrangement · سنتر بيس → centerpiece · باقة → bouquet · بوكيه → bouquet
ربطة → bunch · غصن / أغصان → stem / stems · رأس → head (hydrangea heads) · كرتون → box · أصيص → pot · نبتة → plant
كرت الإهداء / الكرت → gift card · نص الكرت → card message · مغذي الورد → flower food
جملة → wholesale · سعر الجملة → wholesale price · أقل كمية → minimum order · محل / محلات → shop(s)
الرياض → Riyadh · حي → district · التوصيل → delivery · نفس اليوم → same day · الفترة → time slot
صباحاً → morning · ظهراً → midday · عصراً → afternoon · ليلاً / مساءً → evening
الواتساب / واتساب → WhatsApp · مدى → mada · تحويل بنكي → bank transfer · رابط دفع → payment link
السلة → basket (use "basket", not "cart") · أضف للسلة → Add to basket · الإجمالي → Total · الطلب → order
المستلم → recipient · إهداء → gift · لي → for me
Colors: أحمر red · وردي pink · وردي فاتح light pink · فوشي fuchsia · أبيض white · كريمي cream · عاجي ivory · أصفر yellow
برتقالي orange · خوخي peach · مرجاني coral · موف mauve · لافندر lavender · بنفسجي purple · عنابي burgundy · بورغندي burgundy
أخضر green · ملون mixed colors · ثنائي اللون bicolor
Occasions: عيد ميلاد birthday · حب / لعيونك love / “For you” · مولودة new baby girl · مولود new baby boy · تخرج graduation
زواج wedding · ملكة وخطوبة engagement · سلامتك / سلامة get well · لشخص غالي someone dear · شكر thank you · اعتذار sorry
بيت جديد new home · وظيفة وترقية new job & promotion · افتتاح grand opening
Product names: if a Latin name exists in ctx (e.g. "Pink & Red Rose Bouquet"), prefer it.
Card messages (short greetings people write on gift cards): translate as natural English card lines, not literal.
