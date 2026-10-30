# Stars figures

Checked 2026-10-30. These values change without a Bot API version, so re-read the source before quoting one. The terms say Telegram sets the value of a Star at its sole discretion.

| Figure | Value | Source | Status |
|---|---|---|---|
| Developer reward per Star | 0.013 USD | [Terms § 6.2.4](https://telegram.org/tos/bot-developers#6-2-4-rewards-for-stars) | official |
| Hold after receipt | up to 21 days before Stars are available for ads or rewards | [Terms § 6.2.4](https://telegram.org/tos/bot-developers#6-2-4-rewards-for-stars) | official; the terms cite "technical reasons" and an upper bound |
| Validity of earned Stars | 3 years from receipt, then debited from the balance | [Terms § 6.2.7](https://telegram.org/tos/bot-developers#6-2-7-expiration) | official |
| Telegram Ads credit per Star | 0.02 USD, only for your own bot or Mini App; may fluctuate | [Terms § 6.2.3](https://telegram.org/tos/bot-developers#6-2-3-advertising-with-stars) | official |
| Minimum withdrawal | 1000 Stars | [`stars_revenue_withdrawal_min`](https://core.telegram.org/api/config#stars-revenue-withdrawal-min) | example value in the docs; the live value comes from client config |
| Maximum per withdrawal | 25000000 Stars | [`stars_revenue_withdrawal_max`](https://core.telegram.org/api/config#stars-revenue-withdrawal-max) | example value in the docs |
| Withdrawal rate | `1300` in the example config | [`stars_usd_withdraw_rate_x1000`](https://core.telegram.org/api/config#stars-usd-withdraw-rate-x1000) | example value in the docs; the page says "US dollars" for 1000 Stars while § 6.2.4 implies 13, so rely on § 6.2.4 |
| Fee with topics in private chats | 15% of all purchases while enabled, non-refundable | [Terms § 6.2.6](https://telegram.org/tos/bot-developers#6-2-6-enabling-topics-in-private-chats) | official |
| Paid broadcast | 0.1 Star per message over 30 per second | [Terms § 6.2.5](https://telegram.org/tos/bot-developers#6-2-5-broadcasting-messages-with-stars) | official; eligibility thresholds disagree, see `tg-bot-ops` |

Consequences:

- Price against the 0.013 USD reward, never against what buyers pay. The buyer's price varies with VAT and store fees, and the terms state that the reward has no connection to it.
- A selling bot should keep topics in private chats off unless the feature earns more than 15%. The fee stops after you disable it, "following a reasonable delay".
- Telegram may withhold or debit Stars for user refunds, suspected abuse or terms violations (§ 6.2.4). Count revenue as final only after the hold.
- Stars on the balance are not your property (§ 6.2.2), and taxes are yours to handle (§ 6.4).

## Withdrawal

Rewards are processed by [Fragment](https://fragment.com) under its own terms. The owner requests them through a Telegram client; for third-party clients the method is [`payments.getStarsRevenueWithdrawalUrl`](https://core.telegram.org/api/stars#withdrawing-revenue), which needs the owner's 2FA password and a balance of at least the minimum, and returns a Fragment page for the TON wallet address. There is no Bot API method for it.

Fragment may be unable to issue rewards for certain users or countries, and Telegram then offers no alternative (§ 6.2.4.1). No list of countries is published. Confirm availability for your own case before relying on payouts.

The docs name the payout coin in two ways: [Fragment's terms](https://fragment.com/terms) and the [MTProto page](https://core.telegram.org/api/stars) say Gram, the [bot features page](https://core.telegram.org/bots/features) still says Toncoin.

Reading the balance: `getMyStarBalance` and `getStarTransactions`. Transaction amounts can carry `nanostar_amount`, a fraction of a Star.
