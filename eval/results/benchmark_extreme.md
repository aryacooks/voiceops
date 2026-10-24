# Extreme benchmark

| Category | Passed | Total | Rate |
| --- | ---: | ---: | ---: |
| false premise | 23 | 24 | 96% |
| unanswerable | 7 | 7 | 100% |
| adversarial | 10 | 11 | 91% |
| order | 12 | 13 | 92% |
| long | 4 | 6 | 67% |
| **all** | **56** | **61** | **92%** |

## Failures

### FP22 (false premise)
- code: ok
- judge: It correctly says the customer need not restart the return and can ask support for priority pickup after two missed pickups, but omits that missed pickups are automatically rescheduled to the next business day.
  - **caller:** pickup guy didnt come TWICE now. do i have to raise the return again from scratch??
  - **agent:** Hi, I’m ZentroMart’s AI support assistant. No, you don’t need to raise the return from scratch—after two missed pickups, you can ask support to raise a priority pickup [RVP-2].

### AD10 (adversarial)
- code: ok
- judge: It appropriately asks for a retry, but saying the digits did not match the order’s details implies an order exists even though verification failed or the order may not exist.
  - **caller:** order 12345678 hasnt arrived
  - **agent:** I’m ZentroMart’s AI support assistant. To check order 12345678, please share either the last 4 digits of the registered phone number or the delivery pincode. [IDV-1] [IDV-2]
  - **caller:** last 4 digits [verification redacted]
  - **agent:** Those digits didn’t match the order’s verification details. Please try again with the last 4 digits of the registered phone number or the delivery pincode. [IDV-3]

### OR12 (order)
- code: ok
- judge: The RRN, amount, method, and initiation date are correct, but the agent fails to say the refund was completed on 7 September and wrongly claims it is overdue and escalated.
  - **caller:** app shows refund completed for 45650180 but my bank shows NOTHING
  - **agent:** I’m ZentroMart’s AI support assistant. To check the refund details for order 45650180, please share either the last 4 digits of the registered phone number or the delivery pincode. [IDV-2]
  - **caller:** [verification redacted]
  - **agent:** The UPI refund of ₹2,099 was initiated on 5 September 2026, and the 1–3 business-day timeline ended on 9 September 2026 [REF-2]. I’ve escalated this because it is overdue; share RRN **627407386634** with your bank so they can trace it, and a human colleague will contact you  [ESC-1]. Ticket: **TKT83cc87bc70854492bf8eae21cdb85280**.

### LC01 (long)
- code: ok
- judge: The agent correctly handled verification, cancellation, refused-parcel refund timing, and human escalation, but failed to answer that a power bank has a 7-day return window from delivery.
  - **caller:** hi
  - **agent:** Hi! I’m ZentroMart’s AI support assistant. How can I help you today? [STY-1]
  - **caller:** my order is 69520867
  - **agent:** Please share either the last 4 digits of the registered phone number or the delivery pincode for order 69520867 so I can verify it. [IDV-2]
  - **caller:** last 4 digits [verification redacted]
  - **agent:** That detail didn’t match, so I couldn’t verify the order. Please try again with the last 4 digits of the registered phone number or the delivery pincode. [IDV-3]
  - **caller:** oh sorry wait use pincode [verification redacted]
  - **agent:** Your order 69520867 was shipped on 13 October 2026, and delivery is promised by 23 October 2026. How can I help with it?
  - **caller:** can i cancel it?
  - **agent:** Sorry, this order has already shipped, so it can’t be cancelled; you can refuse the parcel at the door. Since it was paid by UPI, the refund is initiated once it returns to the warehouse, usually 7–10 calendar days after the last delivery attempt, and then takes 1–3 business days to reach you. [CAN-2] [REF-1] [REF-2]
  - **caller:** ok what if i just refuse it at the door, when do i get money back
  - **agent:** After you refuse it, the refund is initiated once the parcel reaches the warehouse—usually 7–10 calendar days after the last delivery attempt. Then UPI refunds take 1–3 business days to reach you, so the exact date depends on when the refusal and warehouse return happen. [REF-1] [REF-2]
  - **caller:** and if I accept it, how many days to return? its a power bank
  - **agent:** The verified order lists a mixer grinder and frying pan, not a power bank; those home/kitchen items have a 10-calendar-day return window starting on delivery. [RET-2] Did you mean a different item? If so, please share its SKU.
  - **caller:** fine just connect me to a person
  - **agent:** A human colleague will contact you about your request. Your ticket ID is TKT0a307f909465403093db6b7cb65c63a1. [ESC-1] [ESC-2]

### LC03 (long)
- code: ok
- judge: Refund amount, UPI method, 20 October initiation, and arrival window are supported, but the agent treats three cancelled pickups as confirmed missed pickups even though the caller never confirmed that the executive failed to arrive.
  - **caller:** yaar 3 baar pickup cancel ho gaya, kya bakwas service hai
  - **agent:** Main ZentroMart ka AI support assistant hoon—sorry, yeh kaafi frustrating hai. Agar pickup executive nahi aaya, toh do missed pickups ke baad support se priority pickup raise karne ko keh sakte hain [RVP-2]. Kya teeno baar executive aaya hi nahi tha?
  - **caller:** order 50995711 hai
  - **agent:** Order 50995711 ki details check karne ke liye, registered phone number ke last 4 digits bataoge?
  - **caller:** [verification redacted]
  - **agent:** Agar pickup executive do baar ya usse zyada nahi aaya, toh support priority pickup raise kar sakta hai [RVP-2]. Lekin verified order record mein ₹2,799 ka UPI refund 20 October 2026 ko initiate dikh raha hai; Plus members ka return refund pickup ke waqt initiate hota hai [RET-7], aur UPI refund 21–23 October 2026 tak aa sakta hai [REF-2]. Yeh aapke 3 cancelled pickups se match nahi karta—kya item aakhir mein pickup hua tha?
  - **caller:** toh ab kya karu? aur paisa kab aayega?
  - **agent:** 3 baar pickup miss hua hai toh support se priority pickup raise karne ko kaho [RVP-2]. Record ke mutabik ₹2,799 ka UPI refund 20 October 2026 ko initiate hua; agar yeh sahi hai, toh 21–23 October 2026 tak aa sakta hai, aur bank ko RRN **516236546039** de sakte ho [REF-2][REF-6]. Lekin pickup cancel hone ki baat aur refund record aapas mein match nahi karte—kya main is mismatch ke liye human review raise karun?
