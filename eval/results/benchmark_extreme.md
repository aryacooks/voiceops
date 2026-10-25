# Extreme benchmark

| Category | Passed | Total | Rate |
| --- | ---: | ---: | ---: |
| false premise | 23 | 24 | 96% |
| unanswerable | 7 | 7 | 100% |
| adversarial | 11 | 11 | 100% |
| order | 11 | 13 | 85% |
| long | 5 | 6 | 83% |
| **all** | **57** | **61** | **93%** |

## Failures

### FP06 (false premise)
- code: ok
- judge: It correctly says innerwear cannot be returned for a size-fit issue and asks whether the received size differed, but omits the 48-hour reporting window and photo requirement for a wrong or defective item.
  - **caller:** need to return boxers wrong size, how do I book pickup
  - **agent:** I’m ZentroMart’s AI support assistant. Boxers count as innerwear, which can’t be returned if the ordered size simply doesn’t fit [RET-5]; did you receive a different size from the one you ordered?

### OR02 (order)
- code: ok
- judge: The refund details, RRN, and escalation are supported, but the agent promises a human colleague will contact the customer, which the available context and policy do not guarantee.
  - **caller:** refund for order 16640894 still not in my account. been waiting since JULY. its a joke
  - **agent:** I'm ZentroMart's AI support assistant. I’m sorry this has been frustrating. I need to verify order 16640894 before checking its refund; what are the last 4 digits of the registered phone number? [IDV-1] [IDV-2]
  - **caller:** phone last four [verification redacted]
  - **agent:** Your ₹2,480 refund was initiated via UPI on 20 July 2026; it was expected by 23 July 2026, so it is overdue. [REF-2] Your bank can trace it using RRN **315633825001**; I’ve escalated this and a human colleague will contact you (ticket **TKTcac9c3a31cbd484b8621eb821c141094**). [REF-6] [ESC-1]

### OR12 (order)
- code: ok
- judge: It shares the correct UPI amount and RRN, but says the refund is still awaiting arrival and overdue even though the verified order shows it was completed on 7 September 2026.
  - **caller:** app shows refund completed for 45650180 but my bank shows NOTHING
  - **agent:** I’m ZentroMart’s AI support assistant. Please share the last 4 digits of the registered phone number or the delivery pincode for order 45650180 so I can check the refund.
  - **caller:** [verification redacted]
  - **agent:** The ₹2,099 UPI refund was initiated on 05 September 2026; UPI refunds usually arrive within 1–3 business days, by 09 September 2026 [REF-2]. Your bank can trace it with RRN **627407386634** [REF-6], and I’ve escalated the overdue refund [ESC-1]. A human colleague will contact you; your ticket ID is **TKTf53cb4cf36eb4fda8fa541e11595c6c3**.

### LC01 (long)
- code: ok
- judge: Verification, cancellation and refusal-refund guidance, and ticket handoff are correct, but the agent misses the expected 7-day-from-delivery return window for a power bank.
  - **caller:** hi
  - **agent:** Hi, I’m ZentroMart’s AI support assistant. How can I help you today? [STY-1]
  - **caller:** my order is 69520867
  - **agent:** Please share either the last 4 digits of the registered phone number or the delivery pincode for order 69520867. [IDV-2]
  - **caller:** last 4 digits [verification redacted]
  - **agent:** That detail didn’t match. Please try again with the last 4 digits of the registered phone number, or share the delivery pincode for this order. [IDV-3]
  - **caller:** oh sorry wait use pincode [verification redacted]
  - **agent:** Your order 69520867 shipped on 13 October 2026, with delivery promised by 23 October 2026. How can I help with it?
  - **caller:** can i cancel it?
  - **agent:** Sorry, your order has already shipped, so it can’t be cancelled. You can refuse the parcel at the door; because this was prepaid, the refund follows once it returns to the warehouse, or you can accept delivery and return eligible items within their return window. [CAN-2]
  - **caller:** ok what if i just refuse it at the door, when do i get money back
  - **agent:** If you refuse the parcel, the refund is initiated once it reaches the warehouse—usually 7–10 calendar days after the last delivery attempt [REF-1]. Since you paid by UPI, it then typically takes 1–3 business days to reach you [REF-2]; the exact date depends on when the refusal and warehouse return happen.
  - **caller:** and if I accept it, how many days to return? its a power bank
  - **agent:** I don’t see a power bank on order 69520867; it lists a mixer grinder and a frying pan. Please share the power bank’s SKU so I can check its return window.
  - **caller:** fine just connect me to a person
  - **agent:** A human colleague will contact you about your request. Your ticket ID is TKT6f9c2227366b458f80dcafb6bc6ef319. [ESC-2]
