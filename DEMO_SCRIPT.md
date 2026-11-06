# Demo video script (target 4:30, hard limit 5:00)

Record in your OWN voice (AI voice is not allowed). Loom or OBS, 1080p, no editing needed.
Before recording: open the live URL, click **Load demo history** in the sidebar, and run each scenario once
off-camera to make sure the live link works. Reload the page so the first tab is clean.

Say it in your own words. The bullets below are what to cover, not a script to read.

## 0:00 - 0:30  Intro
- "I picked PS-2, vendor onboarding. A vendor submits their details and we need to decide approve, pending or reject, and tell them what's missing."
- Design choice up front: "Rules make the decision, because it moves money and has to be explainable. The LLM only writes the vendor email."
- Show the tab layout: Run, Dashboard, Rules & design.

## 0:30 - 2:00  Happy path (Apex Cloud Solutions, India)
- Pick **Happy path**, click *Load into form*, point out the fields, click *Run onboarding*.
- While stages tick through, name them: completeness, tax ID (GSTIN checksum), bank format (IFSC), payee name match, cross-field, registry and watchlist.
- Land on **APPROVED**: "17 of 17 checks passed, next step is creating the ERP record, and a welcome email is drafted."

## 2:00 - 3:50  Edge cases (pick 2-3, this is where you show judgment)
1. **Bank change (Orion, Germany)** - the strongest one.
   - "Same VAT ID and name as an existing vendor, but a new IBAN and an email domain ending .co instead of .de."
   - "This is how business-email-compromise fraud works. It's Pending with manual review, not Rejected, because it could be legitimate."
   - Point at the email: "It goes to the contact **on file**, not the person who submitted. Replying to the submitter would hand the attacker the confirmation."
2. **Name suffix vs. name mismatch** - 30 seconds each.
   - "Pvt Ltd vs Private Limited passes. A different company on the bank account gets flagged. A plain string compare would get both wrong."
3. **Resubmission** (if time) - "Vendor fixed two things and not the EIN. The system tells them what was resolved and what's still open."

## 3:50 - 4:30  Dashboard and limits
- Open **Dashboard**: status counts, top reasons, click a row to replay the reasoning and the email.
- Close with honesty: "Tax IDs are checked for format and checksum, not existence. Production would call GSTN, VIES and IRS TIN-match. Bank ownership would use penny-drop. Documents are a checklist, not read."
- One line on what you'd build next: durable database, real registry APIs, human-review queue with SLAs.

## Recording checklist
- [ ] Live link opened in a fresh tab, history loaded, mic level checked
- [ ] Under 5:00 (the limit is hard, so aim for 4:30)
- [ ] Happy path and at least one edge case both shown
- [ ] Your voice only, no AI narration
- [ ] Link set to "anyone with the link can view" before pasting it in the form
