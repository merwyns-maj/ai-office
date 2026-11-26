---
name: phone-check
description: 2-minute phone check Merwyn runs on the published AI Office page after a merged UI change
---
# Phone check

Run on a real phone, on the published "AI Office" page. About 2 minutes. For each step, do it, compare with Expect, answer pass or fail. Janice pastes these steps to Merwyn.

1. **Do:** open the published AI Office page on your phone. **Expect:** office view, top strip with agents, bar at the bottom, no error text, within about 5 s.
2. **Do:** look at the office. **Expect:** agents at their desks with names; nothing cut off at the sides.
3. **Do:** read the usage panel. **Expect:** session total and agent rows with numbers, a budget word or "budget not set", the main-session row text.
4. **Do:** tap Chat in the bar. **Expect:** chat opens below the bar, full width; the office shrinks above it and is still visible.
5. **Do:** drag the handle at the chat's top edge up, then down. **Expect:** chat follows your finger; the office re-fits without stretching; chat stops at a minimum (header, 2 lines, composer) and leaves an office strip at the top.
6. **Do:** with chat tall, look at the usage and latest-events panels. **Expect:** both inside the office area, not under the chat or bar, not on top of each other.
7. **Do:** tap the composer and type a few letters (do not send). **Expect:** keyboard up, composer and your text visible above it.
8. **Do:** delete the letters and close the keyboard. **Expect:** the office strip comes back; chat at the height you left it.
9. **Do:** close chat. **Expect:** chat gone, office full height, panels where they were.
10. **Do:** read usage once more. **Expect:** same numbers as step 3.

Reply: "phone check pass", or "fail step N: what you saw", plus your phone and browser.

Janice records the reply in the task's Review log (see pmo-playbook, Publish). It does not replace a Reviewer PASS.
