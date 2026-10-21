# L5 — WhatsApp instructions and sale outcomes (phase R8)

**Research question:** Can approved plans reach farmers as correct WhatsApp messages in their language, and can actual sales be recorded without breaking stock?

**Build:**
- Message templates in Punjabi, Hindi and English, filled from approved assignments only.
- Sending through the **Meta WhatsApp Cloud API test number** to the user's own phone (no real farmers).
- Delivery status tracking.
- Sale recording from a J-form number used as the duplicate key; the sale consumes its reservation.

**Alternatives discussed (not built):** SMS (withdrawn, CHAT-23); live LLM translation (rejected, because numbers could change).

**Tests:**
- each language preview keeps the exact quantity, mandi and date;
- duplicate webhook does not repeat a send;
- duplicate J-form records no second sale;
- the "cannot reach" case.

**Outputs:**
- phone screenshots in each language;
- the test report;
- Section 4.5.

**Done when:** a real test message arrives on the user's phone from an approved plan, and the sale → stock update is verified.
